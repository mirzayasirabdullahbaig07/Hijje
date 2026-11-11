"""Command line interface.

    hijje variants "mujhe nahi pata"        show respellings of a text
    hijje normalize "kya kia kiya"          show the key at every level
    hijje rules --lexicon                   list every rule and word-list entry
    hijje validate --data data/seed         check a dataset for problems
    hijje collisions --data data/seed       which different words get merged
    hijje eval --data data/seed --out results/seed
    hijje review-sheet --variants results/seed/variants.jsonl --out review/seed.csv
    hijje review-stats --sheet review/seed.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from .data import load_dataset, validate
from .evaluate import EvalConfig, evaluate
from .normalize import LEVEL_NAMES, LEVELS, normalize_text, normalize_word
from .report import to_markdown
from .review import build_sheet, summarize
from .text import tokenize
from .variation import LEXICON, LEXICON_WEIGHT, RULES, VariationModel, derive_seed

DEFAULT_RETRIEVERS = "bm25,bm25-l1,bm25-l2,bm25-l3,char,fusion"


def _protect(path) -> frozenset:
    if not path:
        return frozenset()
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return frozenset(ln.strip().lower() for ln in lines if ln.strip() and not ln.startswith("#"))


def cmd_variants(args) -> int:
    model = VariationModel(protect=_protect(args.protect_file))
    print(f"original : {args.text}")
    for i in range(args.n):
        p = model.perturb(args.text, rate=args.rate, seed=derive_seed(args.seed, i), max_edits=args.max_edits)
        edits = ", ".join(f"{e.original}→{e.variant} ({e.rule})" for e in p.edits) or "no change"
        print(f"variant {i + 1}: {p.text}\n           {edits}")
    return 0


def cmd_normalize(args) -> int:
    levels = [args.level] if args.level is not None else list(LEVELS)
    for level in levels:
        print(f"level {level} ({LEVEL_NAMES[level]:8}): {normalize_text(args.text, level)}")
    return 0


def cmd_rules(args) -> int:
    """Print the rule table in Markdown (docs/VARIATION_RULES.md is built from this)."""
    print("| Rule | What it models | Example | Weight |")
    print("|---|---|---|---|")
    for rule in RULES:
        print(f"| `{rule.name}` | {rule.description} | {rule.example[0]} → {rule.example[1]} | {rule.weight} |")
    print(f"\nWord list (`lexicon`): {len(LEXICON)} frequent words with "
          f"{sum(len(v) for v in LEXICON.values())} alternate spellings, weight {LEXICON_WEIGHT}.")
    if args.lexicon:
        print()
        for word, alternates in LEXICON.items():
            print(f"- {word}: {', '.join(alternates)}")
    return 0


def cmd_review_sheet(args) -> int:
    n = build_sheet(args.variants, args.out)
    print(f"{n} distinct respellings written to {args.out}")
    print("Fill the 'natural' column with y or n, then run: hijje review-stats --sheet " + str(args.out))
    return 0


def cmd_review_stats(args) -> int:
    stats = summarize(args.sheet)
    print("| Rule | Reviewed | Judged natural | Share | Not yet reviewed |")
    print("|---|---|---|---|---|")
    for rule in sorted(stats):
        s = stats[rule]
        share = "–" if s["share_natural"] is None else f"{100 * s['share_natural']:.0f}%"
        print(f"| {rule} | {s['reviewed']} | {s['natural']} | {share} | {s['unreviewed']} |")
    return 0


def cmd_validate(args) -> int:
    ds = load_dataset(args.data)
    for key, value in ds.stats().items():
        print(f"{key}: {value}")
    problems = validate(ds)
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nno problems found")
    return 0


def cmd_collisions(args) -> int:
    ds = load_dataset(args.data)
    vocab = set()
    for text in list(ds.corpus.values()) + list(ds.queries.values()):
        vocab.update(t for t in tokenize(text) if t.isascii() and t.isalpha())
    print(f"{len(vocab)} distinct words in {ds.name}\n")
    for level in LEVELS[1:]:
        groups = defaultdict(set)
        for word in vocab:
            groups[normalize_word(word, level)].add(word)
        merged = sorted((g for g in groups.values() if len(g) > 1), key=lambda g: (-len(g), sorted(g)))
        words_merged = sum(len(g) for g in merged)
        print(
            f"level {level} ({LEVEL_NAMES[level]}): {len(groups)} keys, "
            f"{len(merged)} merged groups covering {words_merged} words"
        )
        for group in merged[: args.top]:
            print("   " + " = ".join(sorted(group)))
        print()
    print("Read each line and ask: are these the same word? Every 'no' is a false merge.")
    return 0


def cmd_eval(args) -> int:
    ds = load_dataset(args.data)
    problems = validate(ds)
    if problems:
        print(f"dataset has {len(problems)} problem(s); run `hijje validate` first", file=sys.stderr)
        return 1
    config = EvalConfig(
        k=args.k,
        rates=tuple(float(r) for r in args.rates.split(",")),
        n_variants=args.n_variants,
        seed=args.seed,
        max_edits=args.max_edits,
        n_boot=args.n_boot,
    )
    specs = [s.strip() for s in args.retrievers.split(",") if s.strip()]
    try:
        result = evaluate(ds, specs, config, with_rule_impact=not args.no_rule_impact)
    except (ImportError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    variants = result.pop("variants")
    (out / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "variants.jsonl").open("w", encoding="utf-8") as fh:
        for row in variants:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = to_markdown(result)
    (out / "summary.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"written: {out / 'summary.md'}, {out / 'results.json'}, {out / 'variants.jsonl'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hijje", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("variants", help="show respellings of a text")
    p.add_argument("text")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--rate", type=float, default=0.6)
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--max-edits", type=int, default=1)
    p.add_argument("--protect-file", help="file with words that must not be changed")
    p.set_defaults(func=cmd_variants)

    p = sub.add_parser("normalize", help="show normalisation keys")
    p.add_argument("text")
    p.add_argument("--level", type=int, choices=LEVELS)
    p.set_defaults(func=cmd_normalize)

    p = sub.add_parser("rules", help="print the spelling-variation rules as a Markdown table")
    p.add_argument("--lexicon", action="store_true", help="also print the word list")
    p.set_defaults(func=cmd_rules)

    p = sub.add_parser("review-sheet", help="make a spreadsheet of respellings for native-speaker review")
    p.add_argument("--variants", required=True, help="variants.jsonl written by `hijje eval`")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_review_sheet)

    p = sub.add_parser("review-stats", help="summarise a filled-in review sheet per rule")
    p.add_argument("--sheet", required=True)
    p.set_defaults(func=cmd_review_stats)

    p = sub.add_parser("validate", help="check a dataset")
    p.add_argument("--data", required=True)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("collisions", help="list words merged by each normalisation level")
    p.add_argument("--data", required=True)
    p.add_argument("--top", type=int, default=15)
    p.set_defaults(func=cmd_collisions)

    p = sub.add_parser("eval", help="run the robustness experiment")
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--retrievers", default=DEFAULT_RETRIEVERS, help=f"comma-separated (default: {DEFAULT_RETRIEVERS})")
    p.add_argument("--rates", default="0.5,1.0")
    p.add_argument("--n-variants", type=int, default=5)
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--max-edits", type=int, default=1)
    p.add_argument("--n-boot", type=int, default=2000)
    p.add_argument("--no-rule-impact", action="store_true", help="skip the per-rule analysis")
    p.set_defaults(func=cmd_eval)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
