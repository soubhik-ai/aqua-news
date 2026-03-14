"""Data Acquisition Layer — async RSS ingestion + full-text extraction."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import Optional

import feedparser
from newspaper import Article

logger = logging.getLogger(__name__)

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
    """Load feed sources and settings from JSON config."""
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


async def _fetch_one(entry: dict, source: FeedSource, loop: asyncio.AbstractEventLoop) -> Optional[ArticleRecord]:
    """Extract a single article from an RSS entry."""
    link = entry.get("link")
    if not link:
        return None

    article = await loop.run_in_executor(_executor, _extract_article, link)
    if article is None or not article.text or len(article.text) < 120:
        return None

    pub_date = None
    if article.publish_date:
        pub_date = str(article.publish_date)
    elif entry.get("published"):
        pub_date = entry["published"]

    return ArticleRecord(
        title=article.title or entry.get("title", "Untitled"),
        url=link,
        text=article.text,
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
    for result in results:
        if isinstance(result, Exception):
            logger.error("Feed ingestion error: %s", result)
            continue
        articles.extend(result)

    logger.info("Total articles ingested: %d", len(articles))
    return articles
