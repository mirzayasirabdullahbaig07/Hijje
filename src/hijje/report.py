"""Turn an evaluation result into a Markdown report a person can read."""

from __future__ import annotations


def _f(x, signed: bool = False) -> str:
    if x is None:
        return "–"
    return f"{x:+.3f}" if signed else f"{x:.3f}"


def _table(header: list, rows: list) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _label(cond: str) -> str:
    return "Clean" if cond == "clean" else cond.replace("respelled_", "") + "% respelled"


def to_markdown(result: dict) -> str:
    meta, summary = result["meta"], result["summary"]
    cfg, ds = meta["config"], meta["dataset"]
    k = cfg["k"]
    conditions = meta["conditions"]
    noisy = conditions[1:]
    hardest = noisy[-1] if noisy else None

    out = [f"# Hijje evaluation: {ds['name']}", ""]
    out.append(
        f"{ds['documents']} documents, {meta['queries_evaluated']} queries, "
        f"{cfg['n_variants']} respelled variants per query per rate, seed {cfg['seed']}, "
        f"hijje {meta['hijje_version']}."
    )
    out += ["", f"## Robustness (nDCG@{k})", ""]
    header = ["Retriever", "Clean", "95% CI"]
    for cond in noisy:
        header += [_label(cond), "Drop"]
    if hardest:
        header += ["Worst variant", "Stability"]
    rows = []
    for name in meta["retrievers"]:
        s = summary[name]
        row = [name, _f(s["clean"]["ndcg"]), f"{_f(s['clean']['ndcg_ci'][0])}–{_f(s['clean']['ndcg_ci'][1])}"]
        for cond in noisy:
            row += [_f(s[cond]["ndcg"]), f"{s[cond]['drop_pct']:.1f}%"]
        if hardest:
            row += [_f(s[hardest]["worst_ndcg"]), _f(s[hardest]["stability"])]
        rows.append(row)
    out.append(_table(header, rows))
    if hardest:
        out += [
            "",
            f"*Drop* is the relative loss against the same retriever's clean score. "
            f"*Worst variant* is the mean over queries of the lowest score among that query's "
            f"variants at {_label(hardest).lower()}. *Stability* is the mean overlap (Jaccard) between "
            f"the clean top-{k} and each variant's top-{k}.",
        ]

    out += ["", f"## Recall@{k}", ""]
    out.append(
        _table(
            ["Retriever"] + [_label(c) for c in conditions],
            [[n] + [_f(summary[n][c]["recall"]) for c in conditions] for n in meta["retrievers"]],
        )
    )

    if result.get("comparisons"):
        out += ["", f"## Difference from `{meta['baseline']}` (nDCG@{k}, paired bootstrap 95% CI)", ""]
        rows = []
        for name, by_cond in result["comparisons"].items():
            row = [name]
            for cond in conditions:
                c = by_cond[cond]
                row.append(f"{_f(c['diff'], True)} [{_f(c['ci'][0], True)}, {_f(c['ci'][1], True)}]")
            rows.append(row)
        out.append(_table(["Retriever"] + [_label(c) for c in conditions], rows))
        out += ["", "An interval that does not contain 0 means the difference is unlikely to be query-sampling noise."]

    impact = result.get("rule_impact")
    if impact:
        out += ["", "## Which kind of respelling hurts", ""]
        out.append(
            f"Change in nDCG@{k} when a single rule is applied to every word it can change, "
            "measured only on the queries that rule changes."
        )
        out.append("")
        rows = []
        for rule, entry in impact.items():
            ex = entry["example"]
            example = f"{ex[0]} → {ex[1]}" if ex[0] else "word list"
            rows.append(
                [rule, example, entry["queries_changed"]]
                + [_f(entry["ndcg_change"][n], True) for n in meta["retrievers"]]
            )
        out.append(_table(["Rule", "Example", "Queries changed"] + meta["retrievers"], rows))
    return "\n".join(out) + "\n"
