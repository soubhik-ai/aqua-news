"""Data Acquisition Layer — async RSS ingestion + full-text extraction."""

import asyncio
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import Optional

import feedparser
from newspaper import Article

logger = logging.getLogger(__name__)

# Minimum useful article length (chars).  Articles shorter than this are
# typically fragments, video-only pages, or extraction failures.
_MIN_TEXT_LENGTH = 300

# Patterns that indicate the extracted text is boilerplate, not news content.
# If the *entire* article text matches one of these, discard it.
_GARBAGE_PATTERNS: list[re.Pattern] = [
    re.compile(r"browser.{0,20}extension.{0,40}blocking.{0,40}video", re.I),
    re.compile(r"thank you for visiting.{0,30}you are using a browser", re.I),
]

# Known per-domain boilerplate to strip from article text before use.
# Each value is a list of (pattern, replacement) applied in order.
_BOILERPLATE_STRIPS: dict[str, list[tuple[re.Pattern, str]]] = {
    "economictimes.com": [
        # ET prepends a variable block of trending headlines + subscription CTA
        (re.compile(
            r"^.*?Economic Times WhatsApp channel\s*\)?\s*\n*",
            re.I | re.S,
        ), ""),
    ],
    "news18.com": [
        # Leading "Curated By : News18.com" + date block
        (re.compile(r"^.*?Curated By\s*:\s*\n*News18\.com\s*\n*Last Updated:.*?\n+", re.I | re.S), ""),
        # Trailing disclaimer + comments block
        (re.compile(r"Disclaimer:\s*Comments reflect.*$", re.I | re.S), ""),
        # CNN copyright boilerplate
        (re.compile(r"CNN name, logo and all associated elements.*?All rights reserved\.?\s*", re.I), ""),
    ],
}

# Shared thread pool — newspaper3k is blocking I/O, so we parallelize via threads.
# 30 workers lets ~30 article downloads run simultaneously.
_executor = ThreadPoolExecutor(max_workers=30)


@dataclass
class FeedSource:
    url: str
    domain: str
    region: str
    category: str
    bias_score: int


@dataclass
class ArticleRecord:
    title: str
    url: str
    text: str
    publish_date: Optional[str]
    top_image: Optional[str]
    domain: str
    region: str
    category: str
    bias_score: int

    def to_dict(self) -> dict:
        return asdict(self)


def load_config(path: str = "config/feeds.json") -> tuple[list[FeedSource], dict]:
    """Load feed sources and settings from JSON config.

    If the env var ``FEEDS_SECRET`` is set (a GCP Secret Manager secret
    name), the config is fetched from Secret Manager.  Otherwise falls
    back to the local filesystem *path*.
    """
    secret_name = os.environ.get("FEEDS_SECRET")
    if secret_name:
        from google.cloud import secretmanager
        project = os.environ.get("GCP_PROJECT", "aqua-news")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        data = json.loads(response.payload.data.decode("utf-8"))
    else:
        with open(path, "r") as f:
            data = json.load(f)
    sources = [FeedSource(**feed) for feed in data["feeds"]]
    settings = data.get("settings", {})
    return sources, settings


def _extract_article(url: str) -> Optional[Article]:
    """Download and parse a single article via newspaper3k."""
    try:
        article = Article(url, request_timeout=10)
        article.download()
        article.parse()
        return article
    except Exception as e:
        logger.warning("Failed to extract %s: %s", url, e)
        return None


def _clean_text(text: str, domain: str) -> Optional[str]:
    """Strip boilerplate and reject garbage content.  Returns cleaned text
    or None if the article should be discarded."""
    # Reject articles that are entirely boilerplate / error messages
    for pat in _GARBAGE_PATTERNS:
        if pat.search(text[:400]):
            return None

    # Strip known per-domain boilerplate
    for strip_pat, replacement in _BOILERPLATE_STRIPS.get(domain, []):
        text = strip_pat.sub(replacement, text).strip()

    if len(text) < _MIN_TEXT_LENGTH:
        return None
    return text


async def _fetch_one(entry: dict, source: FeedSource, loop: asyncio.AbstractEventLoop) -> Optional[ArticleRecord]:
    """Extract a single article from an RSS entry."""
    link = entry.get("link")
    if not link:
        return None

    article = await loop.run_in_executor(_executor, _extract_article, link)
    if article is None or not article.text:
        return None

    cleaned = _clean_text(article.text, source.domain)
    if cleaned is None:
        return None

    pub_date = None
    if article.publish_date:
        pub_date = str(article.publish_date)
    elif entry.get("published"):
        pub_date = entry["published"]

    return ArticleRecord(
        title=article.title or entry.get("title", "Untitled"),
        url=link,
        text=cleaned,
        publish_date=pub_date,
        top_image=article.top_image or None,
        domain=source.domain,
        region=source.region,
        category=source.category,
        bias_score=source.bias_score,
    )


async def _fetch_feed(source: FeedSource, max_articles: int, loop: asyncio.AbstractEventLoop) -> list[ArticleRecord]:
    """Parse one RSS feed and extract all articles concurrently."""
    feed = await loop.run_in_executor(_executor, feedparser.parse, source.url)
    entries = feed.entries[:max_articles]

    # Fan out all article downloads in parallel
    tasks = [_fetch_one(entry, source, loop) for entry in entries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    records = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Article extraction error in %s: %s", source.domain, r)
        elif r is not None:
            records.append(r)

    logger.info("Fetched %d articles from %s", len(records), source.domain)
    return records


async def ingest_all(
    sources: list[FeedSource], max_articles: int = 20
) -> list[ArticleRecord]:
    """Ingest all configured feeds concurrently with parallel article extraction."""
    loop = asyncio.get_event_loop()
    tasks = [_fetch_feed(source, max_articles, loop) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles: list[ArticleRecord] = []
    seen_urls: set[str] = set()
    for result in results:
        if isinstance(result, Exception):
            logger.error("Feed ingestion error: %s", result)
            continue
        for article in result:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                articles.append(article)

    logger.info("Total articles ingested: %d (deduped from %d)", len(articles),
                len(articles) + len(seen_urls) - len(articles))
    return articles
