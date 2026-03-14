"""Tests for the data acquisition layer."""

import json
import pytest
from src.acquisition import load_config, FeedSource, ArticleRecord


def test_load_config_parses_all_feeds(tmp_path):
    cfg = tmp_path / "feeds.json"
    cfg.write_text(json.dumps({
        "feeds": [
            {"url": "http://a.com/rss", "domain": "a.com", "region": "IN", "category": "general", "bias_score": -2},
            {"url": "http://b.com/rss", "domain": "b.com", "region": "HK", "category": "tech", "bias_score": 3},
        ],
        "settings": {"similarity_threshold": 0.7}
    }))
    sources, settings = load_config(str(cfg))
    assert len(sources) == 2
    assert all(isinstance(s, FeedSource) for s in sources)
    assert settings["similarity_threshold"] == 0.7


def test_load_config_fields(tmp_path):
    cfg = tmp_path / "feeds.json"
    cfg.write_text(json.dumps({
        "feeds": [
            {"url": "http://x.com/rss", "domain": "x.com", "region": "GLOBAL", "category": "science", "bias_score": 0},
        ],
        "settings": {}
    }))
    sources, _ = load_config(str(cfg))
    s = sources[0]
    assert s.url == "http://x.com/rss"
    assert s.domain == "x.com"
    assert s.region == "GLOBAL"
    assert s.category == "science"
    assert s.bias_score == 0


def test_article_record_to_dict():
    a = ArticleRecord(
        title="Test", url="http://t.co", text="body",
        publish_date="2026-01-01", top_image=None,
        domain="t.co", region="IN", category="general", bias_score=-1,
    )
    d = a.to_dict()
    assert d["title"] == "Test"
    assert d["bias_score"] == -1
    assert d["category"] == "general"
    assert isinstance(d, dict)


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path.json")
