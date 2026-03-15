"""Interface Layer — Streamlit dashboard with mobile-first responsive design."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import html
import json
import logging
import math
from urllib.parse import quote

import streamlit as st
from google.cloud import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="aqua news",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Minimal B&W CSS ──────────────────────────────────────────────────────────

_CSS = """\
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#ffffff">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
html, body, [class*="st-"] {
font-family: 'Inter', sans-serif !important;
background-color: #ffffff !important;
color: #000000;
}
.main .block-container {
max-width: 760px;
padding: 1.5rem 1.2rem 4rem 1.2rem;
}
.stApp { background-color: #ffffff; }

/* ── Header ── */
.app-header {
border-bottom: 3px solid #000000;
padding-bottom: 0.75rem;
margin-bottom: 1.5rem;
}
.app-header h1 {
color: #000000;
font-family: 'Inter', sans-serif;
font-size: 1.6rem;
font-weight: 700;
letter-spacing: 0.08em;
margin: 0;
}
.app-header p {
color: #555555;
font-family: 'Inter', sans-serif;
font-size: 0.8rem;
margin: 0.3rem 0 0 0;
}

/* ── Search ── */
.stTextInput > div > div > input {
border: 1px solid #000 !important;
border-radius: 0 !important;
font-family: 'Inter', sans-serif !important;
font-size: 0.88rem !important;
padding: 0.6rem 0.9rem !important;
}
.stTextInput > div > div > input:focus {
border-color: #000 !important;
box-shadow: 0 0 0 1px #000 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
gap: 0;
border-bottom: 1px solid #e0e0e0;
}
.stTabs [data-baseweb="tab"] {
font-family: 'IBM Plex Mono', monospace !important;
font-size: 0.78rem !important;
text-transform: uppercase;
letter-spacing: 0.04em;
padding: 0.6rem 1rem !important;
color: #777 !important;
border-bottom: 2px solid transparent;
background: transparent !important;
}
.stTabs [aria-selected="true"] {
color: #000 !important;
border-bottom: 2px solid #000 !important;
font-weight: 600 !important;
}

/* ── Stats bar ── */
.stats-bar {
display: flex;
gap: 1.5rem;
padding: 0.8rem 0;
margin-bottom: 1rem;
border-bottom: 1px solid #e0e0e0;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.74rem;
color: #555;
}
.stats-bar .stat-val {
color: #000;
font-weight: 600;
font-size: 0.88rem;
}

/* ── Section header ── */
.section-header {
font-family: 'IBM Plex Mono', monospace;
font-size: 0.72rem;
text-transform: uppercase;
letter-spacing: 0.08em;
color: #999;
margin: 1.5rem 0 0.8rem 0;
padding-bottom: 0.4rem;
border-bottom: 1px solid #e0e0e0;
}

/* ── Cluster card ── */
.cluster-card {
background: #ffffff;
border: 1px solid #e0e0e0;
border-radius: 2px;
padding: 1.5rem;
margin-bottom: 1rem;
transition: border-color 0.15s;
}
.cluster-card:hover {
border-color: #000000;
}
.cluster-card .lead-title {
color: #000000;
font-family: 'Inter', sans-serif;
font-size: 1.05rem;
font-weight: 600;
line-height: 1.4;
margin: 0 0 0.6rem 0;
}
.cluster-card .lead-title a {
color: #000000;
text-decoration: none;
}
.cluster-card .lead-title a:hover {
border-bottom: 1px solid #000000;
}
.cluster-card .meta {
color: #777;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.72rem;
margin-bottom: 0.6rem;
display: flex;
flex-wrap: wrap;
gap: 0.2rem 0.8rem;
}
.tag {
display: inline-block;
background: #f5f5f5;
border: 1px solid #ddd;
border-radius: 2px;
padding: 0.1rem 0.45rem;
font-size: 0.65rem;
font-family: 'IBM Plex Mono', monospace;
color: #555;
text-transform: uppercase;
letter-spacing: 0.04em;
}
.cluster-card .summary {
color: #333333;
font-family: 'Inter', sans-serif;
font-size: 0.88rem;
line-height: 1.65;
margin: 0.8rem 0;
}

/* ── Bias bar ── */
.bias-bar-wrap { margin-top: 0.8rem; }
.bias-bar-container {
position: relative;
background: #f5f5f5;
height: 28px;
border-radius: 2px;
border: 1px solid #e0e0e0;
overflow: visible;
}
.bias-bar-center {
position: absolute;
left: 50%;
top: 0;
bottom: 0;
width: 1px;
background: #ccc;
}
.bias-marker {
position: absolute;
top: 50%;
width: 10px;
height: 10px;
background: #000000;
border-radius: 50%;
transform: translate(-50%, -50%);
transition: transform 0.15s;
}
.bias-marker:hover {
transform: translate(-50%, -50%) scale(1.5);
}
.bias-legend {
display: flex;
justify-content: space-between;
color: #999;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.62rem;
margin-top: 0.25rem;
}
.metric-row {
display: flex;
flex-wrap: wrap;
gap: 0.2rem 1.2rem;
color: #777;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.72rem;
margin-top: 0.6rem;
}

/* ── Source links ── */
.source-links {
margin-top: 0.8rem;
padding-top: 0.8rem;
border-top: 1px solid #f0f0f0;
}
.source-links summary {
color: #555;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.72rem;
text-transform: uppercase;
letter-spacing: 0.04em;
cursor: pointer;
-webkit-tap-highlight-color: transparent;
padding: 0.3rem 0;
}
.source-links .link-row {
display: flex;
justify-content: space-between;
align-items: center;
padding: 0.4rem 0;
border-bottom: 1px solid #f8f8f8;
}
.source-links .link-row:last-child { border-bottom: none; }
.source-links a {
color: #333333;
text-decoration: none;
font-family: 'Inter', sans-serif;
font-size: 0.76rem;
word-break: break-word;
}
.source-links a:hover {
color: #000000;
border-bottom: 1px solid #000;
}
.source-links .link-bias {
color: #999;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.68rem;
white-space: nowrap;
margin-left: 0.75rem;
}

/* ── Share buttons ── */
.share-row {
display: flex;
flex-wrap: wrap;
gap: 0.4rem;
margin-top: 0.8rem;
}
.share-btn {
display: inline-flex;
align-items: center;
gap: 0.35rem;
background: #fff;
border: 1px solid #ddd;
border-radius: 2px;
padding: 0.4rem 0.65rem;
color: #555;
font-size: 0.68rem;
font-family: 'IBM Plex Mono', monospace;
text-decoration: none;
-webkit-tap-highlight-color: transparent;
cursor: pointer;
min-height: 36px;
min-width: 36px;
justify-content: center;
transition: all 0.12s;
}
.share-btn:hover {
background: #000;
color: #fff;
border-color: #000;
}
.share-btn svg {
width: 14px;
height: 14px;
fill: currentColor;
flex-shrink: 0;
}

/* ── Pagination ── */
.page-nav {
display: flex;
justify-content: center;
align-items: center;
gap: 0.8rem;
padding: 1rem 0;
margin-top: 0.5rem;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.76rem;
color: #555;
}

/* ── Empty state ── */
.empty-state {
text-align: center;
padding: 3rem 1rem;
color: #999;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.82rem;
}

@media (max-width: 640px) {
.main .block-container {
padding: 0.8rem 0.8rem 3rem 0.8rem;
}
.cluster-card { padding: 1.1rem; }
.cluster-card .lead-title { font-size: 0.95rem; }
.share-btn {
padding: 0.35rem 0.5rem;
font-size: 0.65rem;
}
.stats-bar { gap: 1rem; font-size: 0.7rem; }
}
#MainMenu, header, footer { visibility: hidden; }
.stDeployButton { display: none; }
</style>"""

st.markdown(_CSS, unsafe_allow_html=True)


# ── SVG icons ────────────────────────────────────────────────────────────────

_ICON_WA = '<svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'
_ICON_TG = '<svg viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>'
_ICON_X = '<svg viewBox="0 0 24 24"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>'
_ICON_EM = '<svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>'
_ICON_LN = '<svg viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>'

ITEMS_PER_PAGE = 5

# Category display config
_CATEGORY_LABELS = {
    "general": "Top Stories",
    "geopolitics": "World & Politics",
    "finance": "Business & Finance",
    "technology": "Technology",
    "science": "Science",
    "culture": "Culture & Entertainment",
}
_CATEGORY_ORDER = ["general", "geopolitics", "finance", "technology", "science", "culture"]


# ── HTML builders ────────────────────────────────────────────────────────────


def _safe_url(url: str) -> str:
    """Sanitize a URL for use in href attributes."""
    escaped = html.escape(url, quote=True)
    if escaped.lower().startswith(("http://", "https://")):
        return escaped
    return ""


def _share_buttons_html(title: str, url: str) -> str:
    t = quote(title)
    u = quote(url)
    safe = _safe_url(url)
    wa = f"https://api.whatsapp.com/send?text={t}%20{u}"
    tg = f"https://t.me/share/url?url={u}&text={t}"
    xr = f"https://twitter.com/intent/tweet?text={t}&url={u}"
    em = f"mailto:?subject={t}&body={t}%0A%0A{u}"
    parts = [
        f'<a class="share-btn" href="{wa}" target="_blank" rel="noopener">{_ICON_WA} WhatsApp</a>',
        f'<a class="share-btn" href="{tg}" target="_blank" rel="noopener">{_ICON_TG} Telegram</a>',
        f'<a class="share-btn" href="{xr}" target="_blank" rel="noopener">{_ICON_X} Post</a>',
        f'<a class="share-btn" href="{em}">{_ICON_EM} Email</a>',
        f'<a class="share-btn" href="{safe}" target="_blank" rel="noopener">{_ICON_LN} Open</a>',
    ]
    return '<div class="share-row">' + "".join(parts) + "</div>"


def _bias_bar_html(scores: list[int]) -> str:
    markers = []
    for score in scores:
        pct = (score + 10) / 20 * 100
        markers.append(
            f'<span class="bias-marker" title="Bias: {score:+d}" style="left:{pct:.1f}%"></span>'
        )
    inner = '<div class="bias-bar-center"></div>' + "".join(markers)
    bar = f'<div class="bias-bar-container">{inner}</div>'
    legend = (
        '<div class="bias-legend">'
        "<span>Left</span>"
        "<span>Center</span>"
        "<span>Right</span>"
        "</div>"
    )
    return f'<div class="bias-bar-wrap">{bar}{legend}</div>'


def _source_links_html(articles: list[dict]) -> str:
    rows = []
    for a in articles:
        title_safe = html.escape(a["title"][:80])
        url_safe = _safe_url(a["url"])
        rows.append(
            f'<div class="link-row">'
            f'<a href="{url_safe}" target="_blank" rel="noopener">{a["domain"]}: {title_safe}</a>'
            f'<span class="link-bias">{a["bias_score"]:+d}</span>'
            f"</div>"
        )
    inner = "".join(rows)
    return (
        f'<div class="source-links">'
        f"<details>"
        f"<summary>All {len(articles)} sources</summary>"
        f"{inner}"
        f"</details>"
        f"</div>"
    )


def _render_cluster(d: dict) -> None:
    lead = d["lead_article"]
    bm = d["bias_metrics"]

    title_safe = html.escape(lead["title"])
    url_safe = _safe_url(lead["url"])
    summary_safe = html.escape(d["summary"])

    tags = "".join(
        f'<span class="tag">{html.escape(t)}</span> '
        for t in d["regions"] + d["categories"]
    )

    meta = (
        f'<span>{html.escape(lead["domain"])}</span>'
        f'<span>Bias: {lead["bias_score"]:+d}</span>'
        f'<span>{d["article_count"]} sources</span>'
    )

    metrics = (
        f'<span>Mean: {bm["mean"]:+.1f}</span>'
        f'<span>Std: {bm["std"]:.1f}</span>'
        f'<span>[{bm["min_score"]:+d}, {bm["max_score"]:+d}]</span>'
    )

    card = (
        '<div class="cluster-card">'
        f'<div class="lead-title"><a href="{url_safe}" target="_blank" rel="noopener">{title_safe}</a></div>'
        f'<div class="meta">{meta}</div>'
        f'<div style="margin-bottom:0.6rem">{tags}</div>'
        f'<div class="summary">{summary_safe}</div>'
        f'<div class="metric-row">{metrics}</div>'
        f'{_bias_bar_html(bm["scores"])}'
        f'{_source_links_html(d["all_articles"])}'
        f'{_share_buttons_html(lead["title"], lead["url"])}'
        "</div>"
    )
    st.markdown(card, unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────────────────

BUCKET_NAME = "aqua-news-cache"
BLOB_NAME = "latest.json"


@st.cache_data(ttl=3600, show_spinner=False)
def load_cached_results() -> tuple[list[dict], str]:
    """Load pre-computed results from GCS."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(BLOB_NAME)
    if not blob.exists():
        return [], ""
    payload = json.loads(blob.download_as_text())
    return payload.get("clusters", []), payload.get("fetched_at", "")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _primary_category(d: dict) -> str:
    """Pick the best category for a cluster based on priority order."""
    cats = set(d.get("categories", []))
    for cat in _CATEGORY_ORDER:
        if cat in cats:
            return cat
    return "general"


def _matches_search(d: dict, query: str) -> bool:
    """Check if a cluster matches the search query."""
    if not query:
        return True
    q = query.lower()
    lead = d["lead_article"]
    if q in lead["title"].lower():
        return True
    if q in d["summary"].lower():
        return True
    if q in lead["domain"].lower():
        return True
    for a in d["all_articles"]:
        if q in a["title"].lower():
            return True
    return False


def _paginate(items: list, page: int, per_page: int) -> tuple[list, int]:
    """Return a page slice and total page count."""
    total_pages = max(1, math.ceil(len(items) / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return items[start : start + per_page], total_pages


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    st.markdown(
        '<div class="app-header">'
        "<h1>AQUA NEWS</h1>"
        "<p>Multi-source clustering with bias spectrum analysis</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Reload cache"):
        st.cache_data.clear()

    results, fetched_at = load_cached_results()

    if not results:
        st.warning("No data yet. The daily fetch hasn't run or produced no clusters.")
        return

    # ── Search bar ───────────────────────────────────────────────────────
    search_query = st.text_input(
        "Search stories",
        placeholder="Search by keyword, topic, or source...",
        label_visibility="collapsed",
    )

    # ── Sidebar filters ──────────────────────────────────────────────────
    all_regions = sorted({r for d in results for r in d["regions"]})
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Region filter**")
    selected_regions = st.sidebar.multiselect(
        "Regions", all_regions, default=all_regions, label_visibility="collapsed"
    )

    # ── Apply filters ────────────────────────────────────────────────────
    filtered = [
        d
        for d in results
        if any(r in selected_regions for r in d["regions"])
        and _matches_search(d, search_query)
    ]

    # ── Stats bar ────────────────────────────────────────────────────────
    total_sources = sum(d["article_count"] for d in filtered)
    ts_display = fetched_at[:16].replace("T", " ") + " UTC" if fetched_at else ""
    st.markdown(
        f'<div class="stats-bar">'
        f'<div><span class="stat-val">{len(filtered)}</span> stories</div>'
        f'<div><span class="stat-val">{total_sources}</span> sources</div>'
        f"<div>{ts_display}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not filtered:
        st.markdown(
            '<div class="empty-state">No stories match your search.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Group by category ────────────────────────────────────────────────
    by_category: dict[str, list[dict]] = {}
    for d in filtered:
        cat = _primary_category(d)
        by_category.setdefault(cat, []).append(d)

    # Build tab list in display order, only for categories with results
    active_cats = [c for c in _CATEGORY_ORDER if c in by_category]
    active_cats.append("all")
    tab_labels = [
        f"{_CATEGORY_LABELS.get(c, c)}  ({len(by_category[c])})"
        if c != "all"
        else f"All  ({len(filtered)})"
        for c in active_cats
    ]

    tabs = st.tabs(tab_labels)

    for tab, cat_key in zip(tabs, active_cats):
        with tab:
            if cat_key == "all":
                items = filtered
            else:
                items = by_category[cat_key]

            # Pagination
            page_key = f"page_{cat_key}"
            if page_key not in st.session_state:
                st.session_state[page_key] = 1

            page_items, total_pages = _paginate(
                items, st.session_state[page_key], ITEMS_PER_PAGE
            )

            for d in page_items:
                _render_cluster(d)

            # Page controls
            if total_pages > 1:
                cols = st.columns([1, 2, 1])
                with cols[0]:
                    if st.button(
                        "Prev", key=f"prev_{cat_key}",
                        disabled=st.session_state[page_key] <= 1,
                    ):
                        st.session_state[page_key] -= 1
                        st.rerun()
                with cols[1]:
                    st.markdown(
                        f'<div class="page-nav">'
                        f'{st.session_state[page_key]} / {total_pages}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with cols[2]:
                    if st.button(
                        "Next", key=f"next_{cat_key}",
                        disabled=st.session_state[page_key] >= total_pages,
                    ):
                        st.session_state[page_key] += 1
                        st.rerun()


if __name__ == "__main__":
    main()
