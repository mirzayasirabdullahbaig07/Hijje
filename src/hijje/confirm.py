"""The analysis fixed in ``docs/PREREGISTRATION.md`` (with the changes in ``docs/DEVIATIONS.md``).

Three query conditions are compared on the same prompts:

A constructed      the 4 most distinctive words of the sentence, spelled as in
                   the passage (what ``dakshina.build_collection`` does)
B volunteer words  the same 4 words, in the volunteer's own spelling, taken from
                   answers where the volunteer wrote out the whole sentence
C as written       every cleaned answer exactly as typed

Relevance: the sentence the prompt came from (grade 2). All numbers are nDCG@10,
averaged over a prompt's writers first. Intervals and p-values come from a
bootstrap over prompts (seed 13), with the three confirmatory tests corrected by
Holm's method.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Optional, Sequence

from .clean import constructed_words, volunteer_spelling_of
from .collect import read_native_sentences
from .metrics import mean, ndcg_at_k, recall_at_k
from .retrievers import build_retriever
from .variation import derive_seed

DEFAULT_SYSTEMS = ("bm25", "bm25-l1", "bm25-l2", "bm25-l3", "bm25-l4", "char", "fusion")


def boot_diff(a: Sequence[float], b: Sequence[float], n_boot: int = 2000, seed: int = 13) -> dict:
    """Paired bootstrap of mean(a) - mean(b) over prompts: estimate, 95% interval, two-sided p."""
    n = len(a)
    rng = random.Random(seed)
    d = [x - y for x, y in zip(a, b)]
    means = []
    for _ in range(n_boot):
        means.append(sum(d[int(rng.random() * n)] for _ in range(n)) / n)
    means.sort()
    below = sum(1 for m in means if m <= 0) / n_boot
    above = sum(1 for m in means if m >= 0) / n_boot
    return {"diff": mean(d), "lo": means[int(0.025 * n_boot)], "hi": means[min(n_boot - 1, int(0.975 * n_boot))],
            "p": min(1.0, 2 * min(below, above))}


def boot_relative_loss(clean: Sequence[float], noisy: Sequence[float], n_boot: int = 2000, seed: int = 13) -> tuple:
    """1 - mean(noisy)/mean(clean), with a 95% interval, resampling prompts as pairs."""
    n = len(clean)
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        idx = [int(rng.random() * n) for _ in range(n)]
        c = sum(clean[i] for i in idx)
        vals.append(1 - sum(noisy[i] for i in idx) / c if c else 0.0)
    vals.sort()
    return 1 - mean(noisy) / mean(clean), vals[int(0.025 * n_boot)], vals[min(n_boot - 1, int(0.975 * n_boot))]


def holm(pvalues: Sequence[float], alpha: float = 0.05) -> list:
    """Holm's step-down procedure: list of (adjusted p, rejected)."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adj = [0.0] * len(pvalues)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adj[i] = running
    return [(a, a < alpha) for a in adj]


def build_conditions(rows: Sequence[dict], src, min_writers: int = 3, core: Optional[set] = None) -> dict:
    sentences = [roman for _, roman in read_native_sentences(src)]
    words = constructed_words(sentences)
    b_rows = []
    for r in rows:
        if r["style"] != "transliteration" or r["prompt"] not in words:
            continue
        got = volunteer_spelling_of(words[r["prompt"]], r["query"], sentences[int(r["prompt"][1:]) - 1])
        if got:
            b_rows.append({"writer": r["writer"], "prompt": r["prompt"], "query": " ".join(got)})
    writers_b = defaultdict(set)
    for r in b_rows:
        writers_b[r["prompt"]].add(r["writer"])
    primary = sorted(p for p, w in writers_b.items() if len(w) >= min_writers and (core is None or p in core))
    return {
        "sentences": sentences, "words": words, "b_rows": b_rows,
        "c_rows": [{"writer": r["writer"], "prompt": r["prompt"], "query": r["query"]} for r in rows],
        "primary": primary, "writers_b": {p: len(w) for p, w in writers_b.items()},
    }


def _per_prompt(retriever, doc_ids, rows, prompts, k=10):
    keep = [r for r in rows if r["prompt"] in prompts]
    runs = retriever.search_batch([r["query"] for r in keep], k)
    acc = defaultdict(list)
    rec = defaultdict(list)
    for r, run in zip(keep, runs):
        ranked = [d for d, _ in run]
        acc[r["prompt"]].append(ndcg_at_k(ranked, {r["prompt"]: 2}, k))
        rec[r["prompt"]].append(recall_at_k(ranked, {r["prompt"]: 2}, k))
    return {p: mean(v) for p, v in acc.items()}, {p: mean(v) for p, v in rec.items()}


def run(rows: Sequence[dict], src, systems: Sequence[str] = DEFAULT_SYSTEMS, min_writers: int = 3,
        core: Optional[set] = None, n_boot: int = 2000, seed: int = 13) -> dict:
    cond = build_conditions(rows, src, min_writers, core)
    prompts = set(cond["primary"])
    sentences = cond["sentences"]
    doc_ids = [f"s{i + 1:05d}" for i in range(len(sentences))]
    a_rows = [{"writer": "constructed", "prompt": p, "query": " ".join(cond["words"][p])} for p in sorted(prompts)]
    out = {"prompts": len(prompts), "queries_b": sum(1 for r in cond["b_rows"] if r["prompt"] in prompts),
           "queries_c": sum(1 for r in cond["c_rows"] if r["prompt"] in prompts),
           "systems": {}, "min_writers": min_writers}
    per = {}
    for spec in systems:
        retriever = build_retriever(spec)
        retriever.index(doc_ids, sentences)
        per[spec] = {}
        for name, rws in (("A", a_rows), ("B", cond["b_rows"]), ("C", cond["c_rows"])):
            nd, rc = _per_prompt(retriever, doc_ids, rws, prompts)
            per[spec][name] = nd
            per[spec][name + "_recall"] = rc
    order = sorted(prompts)
    for spec in systems:
        entry = {}
        for name in "ABC":
            vals = [per[spec][name][p] for p in order if p in per[spec][name]]
            lo_hi = boot_diff(vals, [0.0] * len(vals), n_boot, derive_seed(seed, "ci", spec, name))
            entry[name] = {"ndcg": mean(vals), "lo": lo_hi["lo"], "hi": lo_hi["hi"], "n": len(vals)}
        out["systems"][spec] = entry
    out["_per_prompt"] = {s: {n: {p: per[s][n][p] for p in order if p in per[s][n]} for n in "ABC"} for s in systems}
    out["tests"] = _tests(out["_per_prompt"], order, n_boot, seed)
    return out


def _paired(per_spec_a, per_spec_b, order):
    common = [p for p in order if p in per_spec_a and p in per_spec_b]
    return [per_spec_a[p] for p in common], [per_spec_b[p] for p in common]


def _tests(per, order, n_boot, seed) -> dict:
    tests = {}
    if "bm25" in per:
        a, b = _paired(per["bm25"]["A"], per["bm25"]["B"], order)
        loss = boot_relative_loss(a, b, n_boot, seed)
        d = boot_diff(a, b, n_boot, derive_seed(seed, "H1"))
        tests["H1"] = {"text": "BM25: constructed words (A) vs the volunteers' spelling of the same words (B)",
                       "diff": d["diff"], "lo": d["lo"], "hi": d["hi"], "p": d["p"], "relative_loss": loss[0],
                       "loss_lo": loss[1], "loss_hi": loss[2], "n": len(a)}
        a, b = _paired(per["bm25"]["A"], per["bm25"]["C"], order)
        loss = boot_relative_loss(a, b, n_boot, seed)
        tests["H1_as_written"] = {"text": "BM25: constructed words (A) vs answers exactly as written (C), descriptive",
                                  "relative_loss": loss[0], "loss_lo": loss[1], "loss_hi": loss[2], "n": len(a)}
    for key, (x, y, txt) in {"H2": ("bm25-l3", "bm25", "bm25-l3 minus bm25 on the volunteers' words (B)"),
                             "H3": ("bm25-l4", "bm25-l3", "bm25-l4 minus bm25-l3 on the volunteers' words (B)")}.items():
        if x in per and y in per:
            a, b = _paired(per[x]["B"], per[y]["B"], order)
            d = boot_diff(a, b, n_boot, derive_seed(seed, key))
            tests[key] = {"text": txt, **d, "n": len(a)}
    ps = [tests[k]["p"] for k in ("H1", "H2", "H3") if k in tests]
    for k, (adj, rej) in zip([k for k in ("H1", "H2", "H3") if k in tests], holm(ps)):
        tests[k]["p_holm"], tests[k]["significant"] = adj, rej
    return tests


def to_markdown(res: dict) -> str:
    L = ["# Volunteer data: confirmatory analysis", "",
         f"{res['prompts']} prompts with at least {res['min_writers']} writers whose answers contain the 4 constructed words. "
         f"Queries: {res['queries_b']} (B, volunteer words), {res['queries_c']} (C, as written). "
         "nDCG@10, averaged over a prompt's writers first, 95% bootstrap intervals over prompts.", "",
         "| System | A constructed | B volunteer's spelling | C as written |", "|---|---|---|---|"]
    for s, e in res["systems"].items():
        f = lambda x: f"{x['ndcg']:.3f} ({x['lo']:.3f}–{x['hi']:.3f})"
        L.append(f"| {s} | {f(e['A'])} | {f(e['B'])} | {f(e['C'])} |")
    L += ["", "## Planned tests (Holm-corrected together)", "", "| Test | Estimate (95% CI) | p | Holm p | Result |", "|---|---|---|---|---|"]
    for k in ("H1", "H2", "H3"):
        t = res["tests"].get(k)
        if not t:
            continue
        extra = f"; relative loss {100 * t['relative_loss']:.1f}% ({100 * t['loss_lo']:.1f}–{100 * t['loss_hi']:.1f}%)" if k == "H1" else ""
        L.append(f"| {k}: {t['text']} | {t['diff']:+.3f} ({t['lo']:+.3f} to {t['hi']:+.3f}){extra} | {t['p']:.4f} | {t['p_holm']:.4f} | {'significant' if t['significant'] else 'not significant'} |")
    t = res["tests"].get("H1_as_written")
    if t:
        L += ["", f"Descriptive: answers exactly as written (C) lose {100 * t['relative_loss']:.1f}% "
              f"({100 * t['loss_lo']:.1f}–{100 * t['loss_hi']:.1f}%) of BM25's nDCG@10 relative to the constructed 4-word queries. "
              "C mostly contains whole sentences, so it is not a keyword-search condition."]
    L.append("")
    return "\n".join(L)
