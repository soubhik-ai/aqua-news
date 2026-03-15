"""Aqua News MCP Server - exposes clustered news data to AI assistants."""

import json
import os
from datetime import datetime

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "aqua-news",
    instructions="Query clustered news stories with bias analysis from 28+ global sources.",
)

# ── Data loader ──────────────────────────────────────────────────────────────

_cache: dict = {}
_cache_ts: float = 0
_CACHE_TTL = 300  # 5 minutes


def _get_data() -> dict:
    """Fetch the latest cluster data, with in-memory caching."""
    global _cache, _cache_ts
    import time

    now = time.time()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        return _cache

    bucket = os.environ.get("GCS_BUCKET")
    blob = os.environ.get("GCS_BLOB", "latest.json")

    if bucket:
        url = f"https://storage.googleapis.com/{bucket}/{blob}"
    else:
        url = os.environ.get(
            "AQUA_NEWS_URL",
            "https://storage.googleapis.com/aqua-news-cache/latest.json",
        )

    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    _cache = resp.json()
    _cache_ts = now
    return _cache


# ── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool()
def get_stories(
    category: str | None = None,
    region: str | None = None,
    min_sources: int = 1,
    limit: int = 10,
) -> str:
    """Get today's news story clusters, optionally filtered by category or region.

    Args:
        category: Filter by category (general, geopolitics, finance, technology, science, culture)
        region: Filter by region (IN, HK, GLOBAL)
        min_sources: Minimum number of sources covering a story (default: 1)
        limit: Max stories to return (default: 10)
    """
    data = _get_data()
    clusters = data.get("clusters", [])

    results = []
    for c in clusters:
        if category and category.lower() not in [
            cat.lower() for cat in c.get("categories", [])
        ]:
            continue
        if region and region.upper() not in [
            r.upper() for r in c.get("regions", [])
        ]:
            continue
        if c.get("article_count", 0) < min_sources:
            continue
        results.append(c)

    results = results[:limit]

    output = []
    for c in results:
        lead = c["lead_article"]
        bm = c["bias_metrics"]
        sources = [
            f"  - {a['domain']}: {a['title'][:80]} (bias: {a['bias_score']:+d})"
            for a in c.get("all_articles", [])
        ]
        output.append(
            f"## {lead['title']}\n"
            f"Lead source: {lead['domain']} (bias: {lead['bias_score']:+d})\n"
            f"Categories: {', '.join(c.get('categories', []))}\n"
            f"Regions: {', '.join(c.get('regions', []))}\n"
            f"Sources: {c['article_count']}\n"
            f"Bias - mean: {bm['mean']:+.1f}, range: [{bm['min_score']:+d}, {bm['max_score']:+d}]\n\n"
            f"Summary: {c['summary']}\n\n"
            f"All sources:\n" + "\n".join(sources)
        )

    fetched = data.get("fetched_at", "unknown")
    header = f"Data as of: {fetched}\nShowing {len(results)} of {len(data.get('clusters', []))} story clusters.\n\n"
    return header + "\n\n---\n\n".join(output) if output else "No stories match the filters."


@mcp.tool()
def search_stories(query: str, limit: int = 5) -> str:
    """Search news stories by keyword across titles, summaries, and sources.

    Args:
        query: Search keyword or phrase
        limit: Max results (default: 5)
    """
    data = _get_data()
    clusters = data.get("clusters", [])
    q = query.lower()

    matches = []
    for c in clusters:
        lead = c["lead_article"]
        searchable = " ".join(
            [
                lead.get("title", ""),
                c.get("summary", ""),
                lead.get("domain", ""),
            ]
            + [a.get("title", "") for a in c.get("all_articles", [])]
        ).lower()

        if q in searchable:
            matches.append(c)

    matches = matches[:limit]

    output = []
    for c in matches:
        lead = c["lead_article"]
        bm = c["bias_metrics"]
        output.append(
            f"## {lead['title']}\n"
            f"Lead: {lead['domain']} (bias: {lead['bias_score']:+d}) | "
            f"{c['article_count']} sources | "
            f"Bias range: [{bm['min_score']:+d}, {bm['max_score']:+d}]\n\n"
            f"{c['summary']}\n\n"
            f"URL: {lead['url']}"
        )

    return (
        f"Found {len(matches)} stories matching '{query}':\n\n"
        + "\n\n---\n\n".join(output)
        if output
        else f"No stories found matching '{query}'."
    )


@mcp.tool()
def get_bias_analysis(
    sort_by: str = "spread",
    limit: int = 5,
) -> str:
    """Analyze bias across today's story clusters. Find the most polarizing or most consensus-driven stories.

    Args:
        sort_by: "spread" for widest bias range, "consensus" for narrowest, "left" for most left-leaning, "right" for most right-leaning
        limit: Max results (default: 5)
    """
    data = _get_data()
    clusters = data.get("clusters", [])

    if not clusters:
        return "No stories available."

    if sort_by == "spread":
        clusters = sorted(
            clusters,
            key=lambda c: c["bias_metrics"]["max_score"] - c["bias_metrics"]["min_score"],
            reverse=True,
        )
    elif sort_by == "consensus":
        clusters = sorted(
            clusters,
            key=lambda c: c["bias_metrics"]["std"],
        )
    elif sort_by == "left":
        clusters = sorted(
            clusters, key=lambda c: c["bias_metrics"]["mean"]
        )
    elif sort_by == "right":
        clusters = sorted(
            clusters, key=lambda c: c["bias_metrics"]["mean"], reverse=True
        )

    results = clusters[:limit]

    output = []
    for c in results:
        lead = c["lead_article"]
        bm = c["bias_metrics"]
        sources_bias = ", ".join(
            f"{a['domain']}({a['bias_score']:+d})"
            for a in c.get("all_articles", [])
        )
        output.append(
            f"## {lead['title']}\n"
            f"Mean bias: {bm['mean']:+.1f} | Std: {bm['std']:.1f} | "
            f"Range: [{bm['min_score']:+d}, {bm['max_score']:+d}] | "
            f"Spread: {bm['max_score'] - bm['min_score']}\n"
            f"Sources: {sources_bias}\n\n"
            f"{c['summary']}"
        )

    label = {
        "spread": "most polarizing",
        "consensus": "most consensus",
        "left": "most left-leaning",
        "right": "most right-leaning",
    }.get(sort_by, sort_by)

    return (
        f"Top {len(results)} {label} stories:\n\n"
        + "\n\n---\n\n".join(output)
    )


if __name__ == "__main__":
    mcp.run()
