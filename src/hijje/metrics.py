"""Ranking metrics and uncertainty estimates.

qrels for one query are a dict {doc_id: relevance grade}; grade 0 or a
missing doc means "not relevant".
"""

from __future__ import annotations

import math
import random
from typing import Mapping, Sequence


def ndcg_at_k(ranked: Sequence[str], qrels: Mapping[str, int], k: int = 10) -> float:
    """Normalised discounted cumulative gain with gain 2^grade - 1."""
    dcg = sum(
        (2 ** qrels.get(doc, 0) - 1) / math.log2(i + 2) for i, doc in enumerate(ranked[:k])
    )
    ideal = sorted((g for g in qrels.values() if g > 0), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(ranked: Sequence[str], qrels: Mapping[str, int], k: int = 10) -> float:
    relevant = {doc for doc, g in qrels.items() if g > 0}
    if not relevant:
        return 0.0
    return len(relevant.intersection(ranked[:k])) / len(relevant)


def mrr_at_k(ranked: Sequence[str], qrels: Mapping[str, int], k: int = 10) -> float:
    for i, doc in enumerate(ranked[:k]):
        if qrels.get(doc, 0) > 0:
            return 1.0 / (i + 1)
    return 0.0


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """Overlap of two result lists, ignoring order. Two empty lists count as equal."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def bootstrap_ci(
    values: Sequence[float], n_boot: int = 2000, alpha: float = 0.05, seed: int = 0
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval for the mean over queries."""
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        means.append(sum(values[int(rng.random() * n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return (lo, hi)


def paired_bootstrap_diff(
    a: Sequence[float], b: Sequence[float], n_boot: int = 2000, alpha: float = 0.05, seed: int = 0
) -> tuple[float, float, float]:
    """Mean of (a - b) per query with a bootstrap confidence interval.

    The two systems are compared on the same queries, so the queries are
    resampled as pairs. If the interval excludes 0, the difference is unlikely
    to be noise from which queries happened to be in the test set.
    """
    if len(a) != len(b):
        raise ValueError("paired comparison needs equal-length lists")
    diffs = [x - y for x, y in zip(a, b)]
    lo, hi = bootstrap_ci(diffs, n_boot=n_boot, alpha=alpha, seed=seed)
    return (mean(diffs), lo, hi)
