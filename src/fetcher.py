"""Daily fetch job - runs the full pipeline and uploads results to GCS.

Results are cached locally by date so the pipeline only scrapes feeds once
per day.  Subsequent runs on the same day reuse the local cache.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from google.cloud import storage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.acquisition import load_config, ingest_all, ArticleRecord
from src.processing import vectorize, cluster_articles
from src.analysis import analyze_clusters

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BUCKET_NAME = os.environ["GCS_BUCKET"]
BLOB_NAME = os.environ.get("GCS_BLOB", "latest.json")
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


# ── Local daily article cache ────────────────────────────────────────────────

def _cache_path_for_today() -> Path:
    return CACHE_DIR / f"articles_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"


def _load_cached_articles() -> list[ArticleRecord] | None:
    """Return today's cached articles, or None if no cache exists."""
    path = _cache_path_for_today()
    if not path.exists():
        return None
    try:
        with open(path) as f:
            rows = json.load(f)
        articles = [ArticleRecord(**row) for row in rows]
        logger.info("Loaded %d articles from local cache %s", len(articles), path.name)
        return articles
    except Exception as e:
        logger.warning("Failed to read cache %s: %s", path, e)
        return None


def _save_articles_cache(articles: list[ArticleRecord]) -> None:
    """Persist today's articles to a local JSON file."""
    CACHE_DIR.mkdir(exist_ok=True)
    path = _cache_path_for_today()
    with open(path, "w") as f:
        json.dump([a.to_dict() for a in articles], f, ensure_ascii=False)
    logger.info("Saved %d articles to local cache %s", len(articles), path.name)


# ── Pipeline ─────────────────────────────────────────────────────────────────

def _fetch_articles(sources, settings) -> list[ArticleRecord]:
    """Return articles from local cache if available, otherwise scrape feeds."""
    cached = _load_cached_articles()
    if cached is not None:
        return cached

    articles = asyncio.run(
        ingest_all(sources, max_articles=settings.get("max_articles_per_feed", 20))
    )
    if articles:
        _save_articles_cache(articles)
    return articles


def run_pipeline() -> list[dict]:
    sources, settings = load_config("config/feeds.json")
    articles = _fetch_articles(sources, settings)
    logger.info("Ingested %d articles", len(articles))

    if len(articles) < 2:
        return []

    tfidf = vectorize(articles, min_df=settings.get("min_document_frequency", 2))
    clusters = cluster_articles(
        articles, tfidf, similarity_threshold=settings.get("similarity_threshold", 0.7)
    )
    summaries = analyze_clusters(
        clusters, sentence_count=settings.get("summary_sentences", 3)
    )

    results = []
    for cs in summaries:
        results.append(
            {
                "cluster_label": cs.cluster_label,
                "lead_article": cs.lead_article.to_dict(),
                "summary": cs.summary,
                "bias_metrics": {
                    "mean": cs.bias_metrics.mean,
                    "std": cs.bias_metrics.std,
                    "min_score": cs.bias_metrics.min_score,
                    "max_score": cs.bias_metrics.max_score,
                    "scores": cs.bias_metrics.scores,
                },
                "article_count": cs.article_count,
                "sources": cs.sources,
                "all_articles": [a.to_dict() for a in cs.all_articles],
                "regions": cs.regions,
                "categories": cs.categories,
            }
        )
    return results


def upload_to_gcs(data: list[dict]) -> None:
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "cluster_count": len(data),
        "clusters": data,
    }
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(BLOB_NAME)
    def _default(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    blob.upload_from_string(
        json.dumps(payload, ensure_ascii=False, default=_default),
        content_type="application/json",
    )
    logger.info("Uploaded %d clusters to gs://%s/%s", len(data), BUCKET_NAME, BLOB_NAME)


def main():
    logger.info("Starting daily fetch...")
    results = run_pipeline()
    if not results:
        logger.warning("No clusters produced - skipping upload")
        return
    upload_to_gcs(results)
    logger.info("Done.")


if __name__ == "__main__":
    main()
