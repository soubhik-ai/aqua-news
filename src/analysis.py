"""Statistical Analysis & Synthesis — lead selection, summarization, bias metrics."""

import logging
from dataclasses import dataclass

import numpy as np
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

from src.acquisition import ArticleRecord
from src.processing import Cluster

logger = logging.getLogger(__name__)

_summarizer = LexRankSummarizer()


@dataclass
class BiasMetrics:
    mean: float
    std: float
    min_score: int
    max_score: int
    scores: list[int]


@dataclass
class ClusterSummary:
    cluster_label: int
    lead_article: ArticleRecord
    summary: str
    bias_metrics: BiasMetrics
    article_count: int
    sources: list[str]
    all_articles: list[ArticleRecord]
    regions: list[str]
    categories: list[str]


def select_lead(articles: list[ArticleRecord]) -> ArticleRecord:
    """Pick the article with the lowest absolute bias score."""
    return min(articles, key=lambda a: abs(a.bias_score))


def summarize_text(text: str, sentence_count: int = 3) -> str:
    """Extract *sentence_count* sentences using LexRank."""
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        sentences = _summarizer(parser.document, sentence_count)
        return " ".join(str(s) for s in sentences)
    except Exception as e:
        logger.warning("Summarization failed: %s", e)
        parts = text.replace("\n", " ").split(". ")
        return ". ".join(parts[:sentence_count]) + "."


def compute_bias_metrics(articles: list[ArticleRecord]) -> BiasMetrics:
    """Calculate spectrum coverage statistics for a cluster."""
    scores = [a.bias_score for a in articles]
    return BiasMetrics(
        mean=round(float(np.mean(scores)), 2),
        std=round(float(np.std(scores)), 2),
        min_score=min(scores),
        max_score=max(scores),
        scores=scores,
    )


def analyze_clusters(
    clusters: list[Cluster], sentence_count: int = 3
) -> list[ClusterSummary]:
    """Produce a ClusterSummary for each cluster."""
    summaries: list[ClusterSummary] = []

    for cluster in clusters:
        lead = select_lead(cluster.articles)
        summary_text = summarize_text(lead.text, sentence_count)
        metrics = compute_bias_metrics(cluster.articles)

        summaries.append(
            ClusterSummary(
                cluster_label=cluster.label,
                lead_article=lead,
                summary=summary_text,
                bias_metrics=metrics,
                article_count=len(cluster.articles),
                sources=list({a.domain for a in cluster.articles}),
                all_articles=cluster.articles,
                regions=list({a.region for a in cluster.articles}),
                categories=list({a.category for a in cluster.articles}),
            )
        )

    summaries.sort(key=lambda s: s.article_count, reverse=True)
    logger.info("Analyzed %d clusters", len(summaries))
    return summaries
