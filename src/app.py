"""Interface Layer — Streamlit dashboard with mobile-first responsive design."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import html
import json
import logging
from urllib.parse import quote

import streamlit as st
from google.cloud import storage

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

# ── Minimal B&W CSS + PWA meta ──────────────────────────────────────────────

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
.stApp {
background-color: #ffffff;
}
.app-header {
border-bottom: 3px solid #000000;
padding-bottom: 0.75rem;
margin-bottom: 2rem;
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
.cluster-card {
background: #ffffff;
border: 1px solid #000000;
border-radius: 0;
padding: 2rem;
margin-bottom: 2rem;
}
.cluster-card .lead-title {
color: #000000;
font-family: 'Inter', sans-serif;
font-size: 1.15rem;
font-weight: 600;
line-height: 1.4;
margin: 0 0 1rem 0;
}
.cluster-card .lead-title a {
color: #000000;
text-decoration: none;
border-bottom: 1px solid #999999;
}
.cluster-card .lead-title a:hover {
border-bottom-color: #000000;
}
.cluster-card .meta {
color: #555555;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.76rem;
margin-bottom: 1rem;
display: flex;
flex-wrap: wrap;
gap: 0.3rem 1rem;
}
.tag {
display: inline-block;
background: #ffffff;
border: 1px solid #000000;
border-radius: 0;
padding: 0.15rem 0.5rem;
font-size: 0.68rem;
font-family: 'IBM Plex Mono', monospace;
color: #000000;
text-transform: uppercase;
letter-spacing: 0.05em;
}
.cluster-card .summary {
color: #333333;
font-family: 'Inter', sans-serif;
font-size: 0.92rem;
line-height: 1.7;
margin: 1.2rem 0;
}
.bias-bar-wrap {
margin-top: 1rem;
}
.bias-bar-container {
position: relative;
background: #f0f0f0;
height: 36px;
border-radius: 0;
border: 1px solid #000000;
overflow: visible;
}
.bias-bar-center {
position: absolute;
left: 50%;
top: 0;
bottom: 0;
width: 2px;
background: #000000;
}
.bias-marker {
position: absolute;
top: 50%;
width: 12px;
height: 12px;
background: #000000;
transform: translate(-50%, -50%);
transition: transform 0.15s;
}
.bias-marker:hover {
transform: translate(-50%, -50%) scale(1.4);
}
.bias-legend {
display: flex;
justify-content: space-between;
color: #555555;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.68rem;
margin-top: 0.35rem;
}
.metric-row {
display: flex;
flex-wrap: wrap;
gap: 0.3rem 1.5rem;
color: #555555;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.76rem;
margin-top: 0.75rem;
}
.source-links {
margin-top: 1.2rem;
padding-top: 1rem;
border-top: 1px solid #e0e0e0;
}
.source-links summary {
color: #333333;
font-family: 'Inter', sans-serif;
font-size: 0.8rem;
font-weight: 500;
cursor: pointer;
-webkit-tap-highlight-color: transparent;
padding: 0.3rem 0;
}
.source-links .link-row {
display: flex;
justify-content: space-between;
align-items: center;
padding: 0.5rem 0;
border-bottom: 1px solid #f0f0f0;
}
.source-links .link-row:last-child {
border-bottom: none;
}
.source-links a {
color: #333333;
text-decoration: none;
font-family: 'Inter', sans-serif;
font-size: 0.78rem;
word-break: break-word;
}
.source-links a:hover {
color: #000000;
border-bottom: 1px solid #000000;
}
.source-links .link-bias {
color: #555555;
font-family: 'IBM Plex Mono', monospace;
font-size: 0.72rem;
white-space: nowrap;
margin-left: 0.75rem;
}
.share-row {
display: flex;
flex-wrap: wrap;
gap: 0.5rem;
margin-top: 1.2rem;
}
.share-btn {
display: inline-flex;
align-items: center;
gap: 0.4rem;
background: #ffffff;
border: 1px solid #000000;
border-radius: 0;
padding: 0.5rem 0.8rem;
color: #000000;
font-size: 0.75rem;
font-family: 'IBM Plex Mono', monospace;
text-decoration: none;
-webkit-tap-highlight-color: transparent;
cursor: pointer;
min-height: 44px;
min-width: 44px;
justify-content: center;
transition: background 0.12s, color 0.12s;
}
.share-btn:hover {
background: #000000;
color: #ffffff;
}
.share-btn svg {
width: 16px;
height: 16px;
fill: currentColor;
flex-shrink: 0;
}
@media (max-width: 640px) {
.main .block-container {
padding: 0.8rem 0.8rem 3rem 0.8rem;
}
.cluster-card {
padding: 1.4rem;
}
.cluster-card .lead-title {
font-size: 1rem;
}
.metric-row {
gap: 0.2rem 0.8rem;
}
.share-btn {
padding: 0.45rem 0.6rem;
font-size: 0.7rem;
}
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


# ── HTML builders (no indentation — critical for Streamlit rendering) ────────


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
    # Copy link: plain link that shows the URL — no inline JS to avoid Streamlit escaping
    parts = [
        f'<a class="share-btn" href="{wa}" target="_blank" rel="noopener">{_ICON_WA} WhatsApp</a>',
        f'<a class="share-btn" href="{tg}" target="_blank" rel="noopener">{_ICON_TG} Telegram</a>',
        f'<a class="share-btn" href="{xr}" target="_blank" rel="noopener">{_ICON_X} Post</a>',
        f'<a class="share-btn" href="{em}">{_ICON_EM} Email</a>',
        f'<a class="share-btn" href="{safe}" target="_blank" rel="noopener">{_ICON_LN} Open link</a>',
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
        "<span>Left (-10)</span>"
        "<span>Center</span>"
        "<span>Right (+10)</span>"
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
        f'<span>Lead bias: {lead["bias_score"]:+d}</span>'
        f'<span>{d["article_count"]} sources</span>'
    )

    metrics = (
        f'<span>Mean bias: {bm["mean"]:+.2f}</span>'
        f'<span>Std: {bm["std"]:.2f}</span>'
        f'<span>Range: [{bm["min_score"]:+d}, {bm["max_score"]:+d}]</span>'
    )

    card = (
        '<div class="cluster-card">'
        f'<div class="lead-title"><a href="{url_safe}" target="_blank" rel="noopener">{title_safe}</a></div>'
        f'<div class="meta">{meta}</div>'
        f'<div style="margin-bottom:1rem">{tags}</div>'
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


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    st.markdown(
        '<div class="app-header">'
        "<h1>NEWS AGGREGATOR</h1>"
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

    if fetched_at:
        st.caption(f"Last updated: {fetched_at[:19].replace('T', ' ')} UTC")

    all_regions = sorted({r for d in results for r in d["regions"]})
    all_categories = sorted({c for d in results for c in d["categories"]})

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")
    selected_regions = st.sidebar.multiselect(
        "Regions", all_regions, default=all_regions
    )
    selected_categories = st.sidebar.multiselect(
        "Categories", all_categories, default=all_categories
    )

    filtered = [
        d
        for d in results
        if any(r in selected_regions for r in d["regions"])
        and any(c in selected_categories for c in d["categories"])
    ]

    st.markdown(
        f'**{len(filtered)} story cluster{"s" if len(filtered) != 1 else ""}** '
        f'<span style="color:#555;font-size:0.82rem">({len(results)} total)</span>',
        unsafe_allow_html=True,
    )

    for d in filtered:
        _render_cluster(d)


if __name__ == "__main__":
    main()
