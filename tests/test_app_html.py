"""Tests for Streamlit HTML generation — verifies no rendering bugs."""

import pytest

# Import the builder functions directly
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Prevent Streamlit from running during import
from unittest.mock import MagicMock
sys.modules["streamlit"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.storage"] = MagicMock()

from src.app import _share_buttons_html, _bias_bar_html, _source_links_html, _render_cluster


# ── Share buttons ────────────────────────────────────────────────────────────


def test_share_buttons_no_leading_whitespace():
    html = _share_buttons_html("Test Title", "http://example.com")
    # Streamlit treats lines starting with 4+ spaces as code blocks
    for line in html.split("\n"):
        stripped = line.lstrip()
        if stripped:  # skip empty lines
            leading_spaces = len(line) - len(stripped)
            assert leading_spaces < 4, f"Line has {leading_spaces} leading spaces: {line!r}"


def test_share_buttons_no_onclick():
    """Inline JS onclick breaks in Streamlit markdown."""
    html = _share_buttons_html("Title", "http://example.com")
    assert "onclick" not in html


def test_share_buttons_contains_all_platforms():
    html = _share_buttons_html("Title", "http://example.com")
    assert "whatsapp" in html.lower()
    assert "telegram" in html.lower() or "t.me" in html
    assert "twitter" in html.lower()
    assert "mailto" in html


def test_share_buttons_encodes_special_chars():
    html = _share_buttons_html("Title with spaces & symbols", "http://example.com/path?a=1&b=2")
    assert "Title%20with%20spaces" in html
    assert "%26" in html  # & encoded


# ── Bias bar ─────────────────────────────────────────────────────────────────


def test_bias_bar_no_leading_whitespace():
    html = _bias_bar_html([-5, 0, 3])
    for line in html.split("\n"):
        stripped = line.lstrip()
        if stripped:
            leading_spaces = len(line) - len(stripped)
            assert leading_spaces < 4, f"Line has {leading_spaces} leading spaces: {line!r}"


def test_bias_bar_marker_positions():
    html = _bias_bar_html([-10, 0, 10])
    assert "left:0.0%" in html    # -10 maps to 0%
    assert "left:50.0%" in html   # 0 maps to 50%
    assert "left:100.0%" in html  # 10 maps to 100%


def test_bias_bar_uses_square_markers():
    html = _bias_bar_html([0])
    assert "bias-marker" in html
    assert "bias-dot" not in html  # old class name should not appear


def test_bias_bar_single_score():
    html = _bias_bar_html([5])
    assert "bias-marker" in html
    assert "left:75.0%" in html  # 5 -> (5+10)/20*100 = 75%


# ── Source links ─────────────────────────────────────────────────────────────


def test_source_links_no_leading_whitespace():
    articles = [
        {"url": "http://a.com/1", "domain": "a.com", "title": "Article One", "bias_score": -2},
    ]
    html = _source_links_html(articles)
    for line in html.split("\n"):
        stripped = line.lstrip()
        if stripped:
            leading_spaces = len(line) - len(stripped)
            assert leading_spaces < 4, f"Line has {leading_spaces} leading spaces: {line!r}"


def test_source_links_contains_all_articles():
    articles = [
        {"url": "http://a.com/1", "domain": "a.com", "title": "First Article", "bias_score": -2},
        {"url": "http://b.com/2", "domain": "b.com", "title": "Second Article", "bias_score": 3},
    ]
    html = _source_links_html(articles)
    assert "a.com" in html
    assert "b.com" in html
    assert "First Article" in html
    assert "Second Article" in html
    assert "All 2 sources" in html


def test_source_links_escapes_html_in_titles():
    articles = [
        {"url": "http://a.com", "domain": "a.com", "title": "Title <script>alert(1)</script>", "bias_score": 0},
    ]
    html = _source_links_html(articles)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_source_links_uses_details_tag():
    articles = [
        {"url": "http://a.com", "domain": "a.com", "title": "T", "bias_score": 0},
    ]
    html = _source_links_html(articles)
    assert "<details>" in html
    assert "<summary>" in html


# ── Full render (smoke test) ─────────────────────────────────────────────────


def test_render_cluster_no_crash():
    d = {
        "cluster_label": 0,
        "lead_article": {
            "title": "Test Lead <b>Article</b>",
            "url": "http://lead.com/1",
            "domain": "lead.com",
            "bias_score": 0,
            "text": "Some text",
            "publish_date": None,
            "top_image": None,
            "region": "IN",
            "category": "general",
        },
        "summary": "This is the summary. <script>xss</script>",
        "bias_metrics": {
            "mean": -1.0,
            "std": 2.5,
            "min_score": -5,
            "max_score": 3,
            "scores": [-5, 0, 3],
        },
        "article_count": 3,
        "sources": ["a.com", "b.com"],
        "all_articles": [
            {"url": "http://a.com/1", "domain": "a.com", "title": "Art A", "bias_score": -5},
            {"url": "http://b.com/2", "domain": "b.com", "title": "Art B", "bias_score": 3},
        ],
        "regions": ["IN", "GLOBAL"],
        "categories": ["general", "geopolitics"],
    }
    # Should not raise — st.markdown is mocked
    _render_cluster(d)


def test_render_cluster_escapes_xss():
    d = {
        "cluster_label": 0,
        "lead_article": {
            "title": '<img src=x onerror="alert(1)">',
            "url": "http://evil.com",
            "domain": "evil.com",
            "bias_score": 0,
            "text": "text",
            "publish_date": None,
            "top_image": None,
            "region": "IN",
            "category": "general",
        },
        "summary": '<script>alert("xss")</script>',
        "bias_metrics": {"mean": 0, "std": 0, "min_score": 0, "max_score": 0, "scores": [0]},
        "article_count": 1,
        "sources": ["evil.com"],
        "all_articles": [
            {"url": "http://evil.com", "domain": "evil.com", "title": "T", "bias_score": 0},
        ],
        "regions": ["IN"],
        "categories": ["general"],
    }
    # Capture what st.markdown was called with
    import src.app as app_mod
    calls = []
    app_mod.st.markdown = lambda html, **kw: calls.append(html)
    _render_cluster(d)
    rendered = calls[0]
    assert "<script>" not in rendered
    # onerror appears as escaped text (&quot;), not as a live attribute
    assert 'onerror=' not in rendered.replace("onerror=&quot;", "")
