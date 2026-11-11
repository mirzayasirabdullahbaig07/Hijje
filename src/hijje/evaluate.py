"""The experiment: how much does each retriever lose when queries are respelled?

Design in one paragraph. Documents are never changed. Each query is searched
once as written ("clean") and then as several respelled variants. A retriever
is robust if its score on the variants stays close to its clean score. All
retrievers see exactly the same variants, so differences between retrievers
are differences between methods, not between random draws.
"""

from __future__ import annotations

import platform
from dataclasses import asdict, dataclass
from typing import Optional, Sequence, Union

from . import __version__
from .data import Dataset
from .metrics import (
    bootstrap_ci,
    jaccard,
    mean,
    mrr_at_k,
    ndcg_at_k,
    paired_bootstrap_diff,
    recall_at_k,
)
from .retrievers import BaseRetriever, build_retriever
from .variation import RULES, VariationModel, derive_seed


@dataclass(frozen=True)
class EvalConfig:
    k: int = 10                  # cutoff for all metrics
    rates: tuple = (0.5, 1.0)    # share of eligible words respelled per query
    n_variants: int = 5          # respelled versions per query per rate
    seed: int = 13
    max_edits: int = 1           # edits stacked on one word
    n_boot: int = 2000           # bootstrap resamples for confidence intervals


def condition_name(rate: float) -> str:
    return f"respelled_{int(round(rate * 100))}"


def _ids(ranking) -> list:
    return [doc_id for doc_id, _ in ranking]


def make_variants(ds: Dataset, model: VariationModel, config: EvalConfig, qids: Sequence[str]) -> dict:
    """Respelled queries: {rate: {query_id: [Perturbed, ...]}}."""
    return {
        rate: {
            qid: [
                model.perturb(
                    ds.queries[qid],
                    rate=rate,
                    seed=derive_seed(config.seed, qid, rate, v),
                    max_edits=config.max_edits,
                )
                for v in range(config.n_variants)
            ]
            for qid in qids
        }
        for rate in config.rates
    }


def rule_impact(ds, retrievers, model, config, qids, clean_ndcg) -> dict:
    """Change in nDCG when exactly one rule is applied to every word it can change.

    Only queries that the rule actually changes are counted, so a rare rule
    is not diluted by the queries it never touches.
    """
    out = {}
    examples = {r.name: r.example for r in RULES}
    for rule in model.rule_names():
        changed, texts, n_words = [], [], 0
        for qid in qids:
            p = model.perturb(
                ds.queries[qid],
                rate=1.0,
                seed=derive_seed(config.seed, qid, "rule", rule),
                only_rules=[rule],
                ensure_change=False,
            )
            if p.edits:
                changed.append(qid)
                texts.append(p.text)
                n_words += len(p.edits)
        entry = {
            "example": list(examples.get(rule, ("", ""))),
            "queries_changed": len(changed),
            "words_changed": n_words,
            "ndcg_change": {},
        }
        for retriever in retrievers:
            if not changed:
                entry["ndcg_change"][retriever.name] = None
                continue
            runs = retriever.search_batch(texts, config.k)
            deltas = [
                ndcg_at_k(_ids(run), ds.qrels[qid], config.k) - clean_ndcg[retriever.name][qid]
                for qid, run in zip(changed, runs)
            ]
            entry["ndcg_change"][retriever.name] = mean(deltas)
        out[rule] = entry
    return out


def evaluate(
    ds: Dataset,
    retrievers: Sequence[Union[str, BaseRetriever]],
    config: EvalConfig = EvalConfig(),
    model: Optional[VariationModel] = None,
    with_rule_impact: bool = True,
) -> dict:
    """Run the full experiment and return a JSON-serialisable result."""
    model = model or VariationModel(protect=ds.protected)
    built = [build_retriever(r) if isinstance(r, str) else r for r in retrievers]
    if not built:
        raise ValueError("at least one retriever is required")
    names = [r.name for r in built]
    if len(set(names)) != len(names):
        raise ValueError(f"retriever names must be unique, got {names}")

    qids = sorted(q for q in ds.queries if any(g > 0 for g in ds.qrels.get(q, {}).values()))
    if not qids:
        raise ValueError("no query has a relevant document")
    doc_ids = sorted(ds.corpus)
    doc_texts = [ds.corpus[d] for d in doc_ids]
    variants = make_variants(ds, model, config, qids)
    k = config.k

    per_query: dict = {}
    for retriever in built:
        retriever.index(doc_ids, doc_texts)
        clean_runs = retriever.search_batch([ds.queries[q] for q in qids], k)
        clean_ids = {q: _ids(run) for q, run in zip(qids, clean_runs)}
        rows = {
            "clean": {
                q: {
                    "ndcg": ndcg_at_k(clean_ids[q], ds.qrels[q], k),
                    "recall": recall_at_k(clean_ids[q], ds.qrels[q], k),
                    "mrr": mrr_at_k(clean_ids[q], ds.qrels[q], k),
                }
                for q in qids
            }
        }
        for rate in config.rates:
            flat = [p.text for q in qids for p in variants[rate][q]]
            runs = retriever.search_batch(flat, k)
            cond = {}
            for i, q in enumerate(qids):
                ids = [_ids(r) for r in runs[i * config.n_variants:(i + 1) * config.n_variants]]
                ndcgs = [ndcg_at_k(x, ds.qrels[q], k) for x in ids]
                cond[q] = {
                    "ndcg": mean(ndcgs),
                    "worst_ndcg": min(ndcgs),
                    "recall": mean([recall_at_k(x, ds.qrels[q], k) for x in ids]),
                    "mrr": mean([mrr_at_k(x, ds.qrels[q], k) for x in ids]),
                    "stability": mean([jaccard(clean_ids[q], x) for x in ids]),
                }
            rows[condition_name(rate)] = cond
        per_query[retriever.name] = rows

    conditions = ["clean"] + [condition_name(r) for r in config.rates]
    summary: dict = {}
    for name in names:
        summary[name] = {}
        clean_mean = mean([per_query[name]["clean"][q]["ndcg"] for q in qids])
        for cond in conditions:
            rows = per_query[name][cond]
            ndcgs = [rows[q]["ndcg"] for q in qids]
            lo, hi = bootstrap_ci(ndcgs, config.n_boot, seed=derive_seed(config.seed, "ci", name, cond))
            entry = {
                "ndcg": mean(ndcgs),
                "ndcg_ci": [lo, hi],
                "recall": mean([rows[q]["recall"] for q in qids]),
                "mrr": mean([rows[q]["mrr"] for q in qids]),
            }
            if cond != "clean":
                entry["worst_ndcg"] = mean([rows[q]["worst_ndcg"] for q in qids])
                entry["stability"] = mean([rows[q]["stability"] for q in qids])
                entry["drop_pct"] = 100.0 * (clean_mean - entry["ndcg"]) / clean_mean if clean_mean else 0.0
            summary[name][cond] = entry

    baseline = names[0]
    comparisons: dict = {}
    for name in names[1:]:
        comparisons[name] = {}
        for cond in conditions:
            a = [per_query[name][cond][q]["ndcg"] for q in qids]
            b = [per_query[baseline][cond][q]["ndcg"] for q in qids]
            diff, lo, hi = paired_bootstrap_diff(
                a, b, config.n_boot, seed=derive_seed(config.seed, "diff", name, cond)
            )
            comparisons[name][cond] = {"diff": diff, "ci": [lo, hi]}

    result = {
        "meta": {
            "hijje_version": __version__,
            "python": platform.python_version(),
            "dataset": ds.stats(),
            "queries_evaluated": len(qids),
            "config": {**asdict(config), "rates": list(config.rates)},
            "retrievers": names,
            "baseline": baseline,
            "conditions": conditions,
        },
        "summary": summary,
        "comparisons": comparisons,
        "per_query_ndcg": {
            name: {cond: {q: per_query[name][cond][q]["ndcg"] for q in qids} for cond in conditions}
            for name in names
        },
        "variants": [
            {
                "query_id": q,
                "rate": rate,
                "original": ds.queries[q],
                "variant": p.text,
                "edits": [{"from": e.original, "to": e.variant, "rule": e.rule} for e in p.edits],
            }
            for rate in config.rates
            for q in qids
            for p in variants[rate][q]
        ],
    }
    if with_rule_impact:
        clean_ndcg = {n: result["per_query_ndcg"][n]["clean"] for n in names}
        result["rule_impact"] = rule_impact(ds, built, model, config, qids, clean_ndcg)
    return result
