import math

import pytest

from hijje.metrics import (
    bootstrap_ci,
    jaccard,
    mean,
    mrr_at_k,
    ndcg_at_k,
    paired_bootstrap_diff,
    recall_at_k,
)


def test_ndcg_perfect_and_empty():
    assert ndcg_at_k(["a", "b"], {"a": 1}) == 1.0
    assert ndcg_at_k([], {"a": 1}) == 0.0
    assert ndcg_at_k(["a"], {}) == 0.0


def test_ndcg_single_relevant_at_rank_two():
    assert ndcg_at_k(["x", "a"], {"a": 1}) == pytest.approx(1 / math.log2(3))


def test_ndcg_graded_hand_computed():
    # ranked b (grade 1) then a (grade 2); ideal order is a then b
    dcg = 1 / math.log2(2) + 3 / math.log2(3)
    idcg = 3 / math.log2(2) + 1 / math.log2(3)
    value = ndcg_at_k(["b", "a"], {"a": 2, "b": 1})
    assert value == pytest.approx(dcg / idcg)
    assert value == pytest.approx(0.7967, abs=1e-4)


def test_ndcg_respects_cutoff():
    assert ndcg_at_k(["x", "y", "a"], {"a": 1}, k=2) == 0.0


def test_recall():
    qrels = {"a": 1, "b": 2, "c": 0}
    assert recall_at_k(["a", "x"], qrels, k=2) == 0.5
    assert recall_at_k(["a", "b"], qrels, k=2) == 1.0
    assert recall_at_k(["c"], qrels, k=1) == 0.0
    assert recall_at_k(["a"], {}, k=1) == 0.0


def test_mrr():
    assert mrr_at_k(["x", "y", "a"], {"a": 1}) == pytest.approx(1 / 3)
    assert mrr_at_k(["x", "y", "a"], {"a": 1}, k=2) == 0.0


def test_jaccard():
    assert jaccard(["a", "b"], ["b", "c"]) == pytest.approx(1 / 3)
    assert jaccard([], []) == 1.0
    assert jaccard(["a"], []) == 0.0


def test_bootstrap_ci_brackets_the_mean_and_is_deterministic():
    values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.0, 0.5, 0.3, 0.9]
    lo, hi = bootstrap_ci(values, n_boot=500, seed=1)
    assert lo <= mean(values) <= hi
    assert lo < hi
    assert (lo, hi) == bootstrap_ci(values, n_boot=500, seed=1)


def test_bootstrap_ci_degenerate_cases():
    assert bootstrap_ci([], n_boot=10) == (0.0, 0.0)
    assert bootstrap_ci([0.5] * 8, n_boot=50) == (0.5, 0.5)


def test_paired_bootstrap_diff():
    a = [0.9, 0.8, 0.7, 1.0, 0.6, 0.9]
    assert paired_bootstrap_diff(a, a, n_boot=100) == (0.0, 0.0, 0.0)
    b = [x - 0.5 for x in a]
    diff, lo, hi = paired_bootstrap_diff(a, b, n_boot=200)
    assert diff == pytest.approx(0.5) and lo == pytest.approx(0.5) and hi == pytest.approx(0.5)
    with pytest.raises(ValueError):
        paired_bootstrap_diff([1.0], [1.0, 2.0])
