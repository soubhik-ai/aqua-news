"""Tests for the statistical analysis & synthesis layer."""

import pytest
from src.acquisition import ArticleRecord
from src.processing import Cluster
from src.analysis import select_lead, summarize_text, compute_bias_metrics, analyze_clusters


def _art(title="T", bias=0, text="Some text here.", domain="test.com"):
    return ArticleRecord(
        title=title, url="http://t.co", text=text,
        publish_date=None, top_image=None,
        domain=domain, region="IN", category="general", bias_score=bias,
    )


# ── Lead selection ───────────────────────────────────────────────────────────


def test_select_lead_picks_lowest_abs_bias():
    articles = [_art(bias=-5), _art(bias=2), _art(bias=0), _art(bias=7)]
    lead = select_lead(articles)
    assert lead.bias_score == 0


def test_select_lead_negative_and_positive():
    articles = [_art(bias=-1), _art(bias=1)]
    lead = select_lead(articles)
    assert abs(lead.bias_score) == 1  # both are equal, picks first


def test_select_lead_single_article():
    articles = [_art(bias=5)]
    lead = select_lead(articles)
    assert lead.bias_score == 5


# ── Summarization ────────────────────────────────────────────────────────────


def test_summarize_returns_string():
    text = (
        "The border standoff escalated today. "
        "Troops were deployed to the region. "
        "Diplomatic talks are expected to resume. "
        "Both sides called for restraint. "
        "The situation remains tense."
    )
    result = summarize_text(text, sentence_count=3)
    assert isinstance(result, str)
    assert len(result) > 0


def test_summarize_short_text_does_not_crash():
    result = summarize_text("Short.", sentence_count=3)
    assert isinstance(result, str)


# ── Bias metrics ─────────────────────────────────────────────────────────────


def test_bias_metrics_basic():
    articles = [_art(bias=-4), _art(bias=0), _art(bias=6)]
    m = compute_bias_metrics(articles)
    assert m.min_score == -4
    assert m.max_score == 6
    assert m.scores == [-4, 0, 6]
    assert abs(m.mean - 0.67) < 0.1
    assert m.std > 0


def test_bias_metrics_single():
    m = compute_bias_metrics([_art(bias=3)])
    assert m.mean == 3.0
    assert m.std == 0.0
    assert m.min_score == 3
    assert m.max_score == 3


def test_bias_metrics_identical_scores():
    m = compute_bias_metrics([_art(bias=2), _art(bias=2), _art(bias=2)])
    assert m.mean == 2.0
    assert m.std == 0.0


# ── Full cluster analysis ───────────────────────────────────────────────────


def test_analyze_clusters_produces_summaries():
    cluster = Cluster(
        label=0,
        articles=[
            _art("Article A", bias=-3, text="India and China held talks on the border standoff in Ladakh. " * 5, domain="a.com"),
            _art("Article B", bias=1, text="Border tensions continued as India deployed troops to Ladakh. " * 5, domain="b.com"),
            _art("Article C", bias=5, text="The India China Ladakh crisis entered its third day today. " * 5, domain="c.com"),
        ],
    )
    summaries = analyze_clusters([cluster], sentence_count=2)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.lead_article.bias_score == 1  # lowest abs
    assert s.article_count == 3
    assert "a.com" in s.sources
    assert isinstance(s.summary, str)
    assert len(s.summary) > 0
    assert s.bias_metrics.min_score == -3
    assert s.bias_metrics.max_score == 5


def test_analyze_clusters_sorted_by_size():
    c1 = Cluster(label=0, articles=[_art(text="text a " * 30), _art(text="text a " * 30)])
    c2 = Cluster(label=1, articles=[_art(text="text b " * 30)] * 5)
    summaries = analyze_clusters([c1, c2], sentence_count=1)
    assert summaries[0].article_count >= summaries[1].article_count


def test_analyze_clusters_regions_and_categories():
    a1 = ArticleRecord("T1", "http://a", "text " * 30, None, None, "a.com", "IN", "geopolitics", -2)
    a2 = ArticleRecord("T2", "http://b", "text " * 30, None, None, "b.com", "HK", "finance", 1)
    cluster = Cluster(label=0, articles=[a1, a2])
    summaries = analyze_clusters([cluster])
    s = summaries[0]
    assert "IN" in s.regions
    assert "HK" in s.regions
    assert "geopolitics" in s.categories
    assert "finance" in s.categories
