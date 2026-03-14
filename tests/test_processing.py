"""Tests for the processing & clustering layer."""

import numpy as np
import pytest
from src.acquisition import ArticleRecord
from src.processing import vectorize, cluster_articles


def _make_article(text, domain="test.com", bias=0):
    return ArticleRecord(
        title="T", url="http://t.co", text=text,
        publish_date=None, top_image=None,
        domain=domain, region="IN", category="general", bias_score=bias,
    )


# ── Vectorization ────────────────────────────────────────────────────────────


def test_vectorize_shape():
    articles = [_make_article("hello world foo bar"), _make_article("hello world baz qux")]
    mat = vectorize(articles, min_df=1)
    assert mat.shape[0] == 2
    assert mat.shape[1] > 0


def test_vectorize_min_df_fallback():
    """With only 1 article, min_df=2 should fall back to 1."""
    articles = [_make_article("some random text for testing")]
    mat = vectorize(articles, min_df=2)
    assert mat.shape[0] == 1


def test_vectorize_empty():
    """Empty list should still produce a matrix."""
    articles = []
    with pytest.raises(ValueError):
        vectorize(articles, min_df=1)


# ── Clustering ───────────────────────────────────────────────────────────────


def test_cluster_similar_articles():
    a1 = _make_article("The president signed a new trade deal with China on tariffs and imports")
    a2 = _make_article("The president signed a trade deal with China reducing tariffs on imports")
    a3 = _make_article("A football match ended in a penalty shootout in the World Cup finals")
    articles = [a1, a2, a3]
    mat = vectorize(articles, min_df=1)
    clusters = cluster_articles(articles, mat, similarity_threshold=0.3)
    # a1 and a2 should cluster; a3 should be noise
    assert len(clusters) >= 1
    cluster_texts = [a.text for a in clusters[0].articles]
    assert a1.text in cluster_texts
    assert a2.text in cluster_texts


def test_cluster_empty_articles():
    clusters = cluster_articles([], np.array([]), similarity_threshold=0.7)
    assert clusters == []


def test_cluster_no_negative_distance():
    """Cosine similarity can exceed 1.0 due to float precision.
    Verify DBSCAN doesn't crash from negative distances."""
    articles = [
        _make_article("identical text for testing " * 20),
        _make_article("identical text for testing " * 20),
        _make_article("completely different words about unrelated topics in science"),
    ]
    mat = vectorize(articles, min_df=1)
    # This previously crashed with "Negative values in data passed to precomputed distance matrix"
    clusters = cluster_articles(articles, mat, similarity_threshold=0.5)
    assert isinstance(clusters, list)


def test_high_threshold_yields_fewer_clusters():
    articles = [
        _make_article("India border tensions with China in Ladakh military standoff"),
        _make_article("India China border Ladakh tensions military troops deployed"),
        _make_article("Hong Kong tech startup raises funding in series B round"),
        _make_article("Hong Kong technology startup secures series B investment"),
    ]
    mat = vectorize(articles, min_df=1)
    clusters_low = cluster_articles(articles, mat, similarity_threshold=0.2)
    clusters_high = cluster_articles(articles, mat, similarity_threshold=0.8)
    assert len(clusters_high) <= len(clusters_low) or len(clusters_high) == 0
