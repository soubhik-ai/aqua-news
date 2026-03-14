"""Interface Layer — Streamlit dashboard with mobile-first responsive design."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import logging
from urllib.parse import quote

import streamlit as st

from src.acquisition import load_config, ingest_all, ArticleRecord
from src.processing import vectorize, cluster_articles
from src.analysis import analyze_clusters, ClusterSummary, BiasMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="News Aggregator",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Mobile-first, high-contrast, monochromatic CSS + PWA meta ───────────────

st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#0e0e0e">

    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    html, body, [class*="st-"] {
        font-family: 'IBM Plex Mono', monospace !important;
    }

    .main .block-container {
        max-width: 760px;
        padding: 1rem 1rem 4rem 1rem;
    }

    /* ── Header ── */
    .app-header {
        border-bottom: 2px solid #ffffff;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .app-header h1 {
        color: #ffffff;
        font-size: 1.5rem;
        letter-spacing: 0.06em;
        margin: 0;
    }
    .app-header p {
        color: #777777;
        font-size: 0.78rem;
        margin: 0.25rem 0 0 0;
    }

    /* ── Cluster card ── */
    .cluster-card {
        background: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }

    .cluster-card .lead-title {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 600;
        line-height: 1.35;
        margin: 0 0 0.5rem 0;
    }

    .cluster-card .lead-title a {
        color: #ffffff;
        text-decoration: none;
        border-bottom: 1px solid #555555;
    }
    .cluster-card .lead-title a:hover {
        border-bottom-color: #ffffff;
    }

    .cluster-card .meta {
        color: #999999;
        font-size: 0.78rem;
        margin-bottom: 0.6rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem 0.8rem;
    }

    .tag {
        display: inline-block;
        background: #2a2a2a;
        border: 1px solid #444444;
        border-radius: 3px;
        padding: 0.1rem 0.45rem;
        font-size: 0.7rem;
        color: #bbbbbb;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .cluster-card .summary {
        color: #cccccc;
        font-size: 0.88rem;
        line-height: 1.6;
        margin: 0.8rem 0;
    }

    /* ── Bias bar ── */
    .bias-bar-container {
        position: relative;
        background: #2a2a2a;
        height: 32px;
        border-radius: 4px;
        margin-top: 0.6rem;
        overflow: visible;
    }

    .bias-bar-center {
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 1px;
        background: #555555;
    }

    .bias-dot {
        position: absolute;
        top: 50%;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #ffffff;
        transform: translate(-50%, -50%);
        border: 1px solid #888888;
        transition: transform 0.15s;
    }
    .bias-dot:hover {
        transform: translate(-50%, -50%) scale(1.3);
    }

    .bias-legend {
        display: flex;
        justify-content: space-between;
        color: #666666;
        font-size: 0.68rem;
        margin-top: 0.2rem;
    }

    .metric-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem 1.5rem;
        color: #aaaaaa;
        font-size: 0.78rem;
        margin-top: 0.5rem;
    }

    /* ── Source links ── */
    .source-links {
        margin-top: 0.7rem;
        padding-top: 0.6rem;
        border-top: 1px solid #2a2a2a;
    }
    .source-links summary {
        color: #888888;
        font-size: 0.78rem;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
    }
    .source-links .link-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0;
        border-bottom: 1px solid #1f1f1f;
    }
    .source-links .link-row:last-child { border-bottom: none; }
    .source-links a {
        color: #aaaaaa;
        text-decoration: none;
        font-size: 0.78rem;
        word-break: break-all;
    }
    .source-links a:hover { color: #ffffff; }
    .source-links .link-bias {
        color: #666666;
        font-size: 0.72rem;
        white-space: nowrap;
        margin-left: 0.5rem;
    }

    /* ── Share buttons ── */
    .share-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.8rem;
    }
    .share-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #2a2a2a;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 0.4rem 0.7rem;
        color: #cccccc;
        font-size: 0.75rem;
        font-family: 'IBM Plex Mono', monospace;
        text-decoration: none;
        -webkit-tap-highlight-color: transparent;
        cursor: pointer;
        min-height: 44px;
        min-width: 44px;
        justify-content: center;
        transition: background 0.15s, border-color 0.15s;
    }
    .share-btn:hover {
        background: #3a3a3a;
        border-color: #666666;
        color: #ffffff;
    }
    .share-btn svg {
        width: 16px;
        height: 16px;
        fill: currentColor;
        flex-shrink: 0;
    }

    /* ── Responsive ── */
    @media (max-width: 640px) {
        .main .block-container {
            padding: 0.6rem 0.6rem 3rem 0.6rem;
        }
        .cluster-card {
            padding: 1rem;
            border-radius: 4px;
        }
        .cluster-card .lead-title { font-size: 1rem; }
        .metric-row { gap: 0.2rem 0.8rem; }
        .share-btn { padding: 0.4rem 0.55rem; font-size: 0.7rem; }
    }

    /* Hide Streamlit chrome on mobile for app-like feel */
    #MainMenu, header, footer { visibility: hidden; }
    .stDeployButton { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── SVG icons (inline, no external deps) ────────────────────────────────────

_ICON_WHATSAPP = '<svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'

_ICON_TELEGRAM = '<svg viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>'

_ICON_X = '<svg viewBox="0 0 24 24"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>'

_ICON_EMAIL = '<svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>'

_ICON_LINK = '<svg viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>'


# ── Helpers ──────────────────────────────────────────────────────────────────


def _share_buttons_html(title: str, url: str) -> str:
    """Generate share buttons for WhatsApp, Telegram, X, Email, and copy-link."""
    share_text = quote(f"{title}")
    share_url = quote(url)

    wa = f"https://api.whatsapp.com/send?text={share_text}%20{share_url}"
    tg = f"https://t.me/share/url?url={share_url}&text={share_text}"
    xr = f"https://twitter.com/intent/tweet?text={share_text}&url={share_url}"
    em = f"mailto:?subject={share_text}&body={share_text}%0A%0A{share_url}"

    # Copy-link uses a small inline JS snippet
    copy_js = f"navigator.clipboard.writeText('{url}');this.textContent='Copied!';setTimeout(()=>this.innerHTML='{_ICON_LINK} Copy link',1500);return false;"

    return f"""
    <div class="share-row">
        <a class="share-btn" href="{wa}" target="_blank" rel="noopener">{_ICON_WHATSAPP} WhatsApp</a>
        <a class="share-btn" href="{tg}" target="_blank" rel="noopener">{_ICON_TELEGRAM} Telegram</a>
        <a class="share-btn" href="{xr}" target="_blank" rel="noopener">{_ICON_X} Post</a>
        <a class="share-btn" href="{em}">{_ICON_EMAIL} Email</a>
        <a class="share-btn" href="#" onclick="{copy_js}">{_ICON_LINK} Copy link</a>
    </div>
    """


def _bias_bar_html(scores: list[int]) -> str:
    """Horizontal bar with a dot per source bias score."""
    dots = ""
    for score in scores:
        pct = (score + 10) / 20 * 100
        dots += f'<span class="bias-dot" title="Bias: {score:+d}" style="left:{pct:.1f}%"></span>'

    return f"""
    <div class="bias-bar-container">
        <div class="bias-bar-center"></div>
        {dots}
    </div>
    <div class="bias-legend">
        <span>&larr; Left (-10)</span>
        <span>Center (0)</span>
        <span>Right (+10) &rarr;</span>
    </div>
    """


def _source_links_html(articles: list[dict]) -> str:
    """Expandable list of all articles in the cluster with links."""
    rows = ""
    for a in articles:
        bias = a["bias_score"]
        rows += f"""
        <div class="link-row">
            <a href="{a['url']}" target="_blank" rel="noopener">{a['domain']}: {a['title'][:80]}</a>
            <span class="link-bias">{bias:+d}</span>
        </div>"""

    return f"""
    <div class="source-links">
        <details>
            <summary>All {len(articles)} sources</summary>
            {rows}
        </details>
    </div>
    """


def _render_cluster(d: dict) -> None:
    """Render a single cluster card from its dict representation."""
    lead = d["lead_article"]
    bm = d["bias_metrics"]
    regions = d["regions"]
    categories = d["categories"]

    tags_html = " ".join(
        f'<span class="tag">{t}</span>' for t in regions + categories
    )

    card = f"""
    <div class="cluster-card">
        <div class="lead-title">
            <a href="{lead['url']}" target="_blank" rel="noopener">{lead['title']}</a>
        </div>
        <div class="meta">
            <span>{lead['domain']}</span>
            <span>Lead bias: {lead['bias_score']:+d}</span>
            <span>{d['article_count']} sources</span>
        </div>
        <div style="margin-bottom:0.5rem">{tags_html}</div>
        <div class="summary">{d['summary']}</div>
        <div class="metric-row">
            <span>Mean bias: {bm['mean']:+.2f}</span>
            <span>Std: {bm['std']:.2f}</span>
            <span>Range: [{bm['min_score']:+d}, {bm['max_score']:+d}]</span>
        </div>
        {_bias_bar_html(bm['scores'])}
        {_source_links_html(d['all_articles'])}
        {_share_buttons_html(lead['title'], lead['url'])}
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)


# ── Pipeline ─────────────────────────────────────────────────────────────────


@st.cache_data(ttl=900, show_spinner=False)
def run_pipeline(config_path: str) -> list[dict]:
    """Execute full ingestion -> clustering -> analysis pipeline."""
    sources, settings = load_config(config_path)
    articles = asyncio.run(
        ingest_all(sources, max_articles=settings.get("max_articles_per_feed", 20))
    )
    if len(articles) < 2:
        return []

    tfidf = vectorize(articles, min_df=settings.get("min_document_frequency", 2))
    clusters = cluster_articles(
        articles, tfidf, similarity_threshold=settings.get("similarity_threshold", 0.7)
    )
    summaries = analyze_clusters(
        clusters, sentence_count=settings.get("summary_sentences", 3)
    )
    return [_summary_to_dict(s) for s in summaries]


def _summary_to_dict(cs: ClusterSummary) -> dict:
    return {
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


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    st.markdown(
        '<div class="app-header"><h1>NEWS AGGREGATOR</h1>'
        "<p>Multi-source clustering with bias spectrum analysis</p></div>",
        unsafe_allow_html=True,
    )

    # Sidebar controls
    if st.sidebar.button("Refresh feeds"):
        st.cache_data.clear()

    with st.spinner("Ingesting feeds and clustering..."):
        results = run_pipeline("config/feeds.json")

    if not results:
        st.warning("No article clusters found. Try again later or check feed URLs.")
        return

    # Collect all regions and categories across results for filters
    all_regions = sorted({r for d in results for r in d["regions"]})
    all_categories = sorted({c for d in results for c in d["categories"]})

    # Sidebar filters
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")

    selected_regions = st.sidebar.multiselect(
        "Regions", all_regions, default=all_regions
    )
    selected_categories = st.sidebar.multiselect(
        "Categories", all_categories, default=all_categories
    )

    # Filter results
    filtered = [
        d
        for d in results
        if any(r in selected_regions for r in d["regions"])
        and any(c in selected_categories for c in d["categories"])
    ]

    st.markdown(
        f"**{len(filtered)} story cluster{'s' if len(filtered) != 1 else ''}** "
        f"<span style='color:#666;font-size:0.82rem'>({len(results)} total)</span>",
        unsafe_allow_html=True,
    )

    for d in filtered:
        _render_cluster(d)


if __name__ == "__main__":
    main()
