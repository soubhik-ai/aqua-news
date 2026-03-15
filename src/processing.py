"""Processing & Clustering Layer - TF-IDF vectorization + similarity clustering."""

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN

from src.acquisition import ArticleRecord

logger = logging.getLogger(__name__)


@dataclass
class Cluster:
    label: int
    articles: list[ArticleRecord]


def vectorize(articles: list[ArticleRecord], min_df: int = 2) -> np.ndarray:
    """Build a TF-IDF matrix from article texts.

    When fewer documents than min_df are present, falls back to min_df=1
    so the pipeline can still operate on small collections.
    """
    texts = [a.text for a in articles]
    effective_min_df = min(min_df, len(texts)) if len(texts) < min_df else min_df
    vectorizer = TfidfVectorizer(stop_words="english", min_df=effective_min_df)
    matrix = vectorizer.fit_transform(texts)
    logger.info("TF-IDF matrix shape: %s", matrix.shape)
    return matrix


def cluster_articles(
    articles: list[ArticleRecord],
    tfidf_matrix: np.ndarray,
    similarity_threshold: float = 0.7,
) -> list[Cluster]:
    """Cluster articles using DBSCAN on cosine distance.

    The cosine distance is 1 - cosine_similarity.  Articles whose pairwise
    cosine similarity exceeds *similarity_threshold* end up in the same
    neighbourhood, so eps = 1 - similarity_threshold.
    """
    if len(articles) == 0:
        return []

    distance_matrix = 1 - cosine_similarity(tfidf_matrix)
    np.clip(distance_matrix, 0, None, out=distance_matrix)
    np.fill_diagonal(distance_matrix, 0)

    eps = 1 - similarity_threshold
    db = DBSCAN(eps=eps, min_samples=2, metric="precomputed")
    labels = db.fit_predict(distance_matrix)

    clusters_map: dict[int, list[ArticleRecord]] = {}
    for label, article in zip(labels, articles):
        if label == -1:
            continue  # noise - unclustered singleton
        clusters_map.setdefault(label, []).append(article)

    clusters = [
        Cluster(label=label, articles=arts)
        for label, arts in sorted(clusters_map.items())
    ]
    logger.info(
        "Formed %d clusters (%d unclustered articles)",
        len(clusters),
        sum(1 for l in labels if l == -1),
    )
    return clusters
