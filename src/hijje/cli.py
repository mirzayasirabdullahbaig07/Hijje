"""Command line interface.

    hijje variants "mujhe nahi pata"        show respellings of a text
    hijje normalize "kya kia kiya"          show the key at every level
    hijje rules --lexicon                   list every rule and word-list entry
    hijje validate --data data/seed         check a dataset for problems
    hijje collisions --data data/seed       which different words get merged
    hijje eval --data data/seed --out results/seed
    hijje review-sheet --variants results/seed/variants.jsonl --out review/seed.csv
    hijje review-stats --sheet review/seed.csv
    hijje attested --pairs lexicon.tsv --out results/attested --show pani theek
    hijje make-form --src <ur folder> --prompts data/real_queries/prompt_ids.txt --out form.html
    hijje collect-build --responses "answers/*.csv" --src <ur folder> --out data/real_built
    hijje judge-sheet --data data/real_built --src <ur folder> --out judge.csv
    hijje judge-export --sheet judge.csv --out data/real_queries/judgments.csv
    hijje real-eval --data data/real_built --out results/real
    hijje normcheck --split train=<f> --split test=<f> --out results/normcheck
    hijje build-dakshina --src <dakshina ur folder> --out data/dakshina_ur
    hijje eval --data data/dakshina_ur --variation "attested:<lexicon files>" --out results/dakshina_ur
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from .attested import analyze, expand_paths, load_attested
from .attested_model import AttestedVariation
from .dakshina import build_collection
from . import collect
from .attested import to_markdown as attested_markdown
from .data import load_dataset, validate
from .evaluate import EvalConfig, evaluate
from .normcheck import check as normcheck_run
from .normcheck import to_markdown as normcheck_markdown
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


def make_model(spec: str, protect=frozenset()):
    """Build a respelling model from a command-line spec.

    rules                      the hand-written rules (default)
    attested:FILE[,FILE...]    only spellings people wrote, from these files
    attested+rules:FILE[,...]  the same, with the rules for words the files lack
    """
    if spec == "rules":
        return VariationModel(protect=protect)
    kind, _, files = spec.partition(":")
    if kind not in ("attested", "attested+rules") or not files:
        raise ValueError(
            f"unknown --variation {spec!r}: use rules, attested:FILE or attested+rules:FILE"
        )
    paths = expand_paths([f for f in files.split(",") if f])
    missing = [f for f in paths if not Path(f).is_file()]
    if missing:
        raise ValueError("file not found: " + ", ".join(missing))
    table, _ = load_attested(paths)
    if not table:
        raise ValueError("no usable (native word, Latin spelling) pairs in: " + ", ".join(paths))
    fallback = VariationModel(protect=protect) if kind == "attested+rules" else None
    return AttestedVariation(table, protect=protect, fallback=fallback)


def cmd_variants(args) -> int:
    try:
        model = make_model(args.variation, _protect(args.protect_file))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
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


def cmd_attested(args) -> int:
    files = expand_paths(args.pairs)
    missing = [f for f in files if not Path(f).is_file()]
    if missing:
        print("error: file not found: " + ", ".join(missing), file=sys.stderr)
        return 1
    result = analyze(files, show=args.show)
    if not result["summary"]["native_words"]:
        print("error: no usable (native word, Latin spelling) pairs in: " + ", ".join(files), file=sys.stderr)
        for reason, n in sorted(result["read"].items()):
            print(f"  {reason}: {n}", file=sys.stderr)
        return 1
    report = attested_markdown(result, top=args.top)
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "attested.md").write_text(report, encoding="utf-8")
        (out / "attested.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report)
    if args.out:
        print(f"written: {Path(args.out) / 'attested.md'}, {Path(args.out) / 'attested.json'}")
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
        model = make_model(args.variation, ds.protected)
        result = evaluate(ds, specs, config, model=model, with_rule_impact=not args.no_rule_impact,
                          variation=args.variation.split(":")[0])
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


def cmd_normcheck(args) -> int:
    splits = {}
    for item in args.split:
        name, sep, files = item.partition("=")
        if not sep or not files:
            print(f"error: --split needs NAME=FILE[,FILE...], got {item!r}", file=sys.stderr)
            return 2
        paths = expand_paths([f for f in files.split(",") if f])
        missing = [f for f in paths if not Path(f).is_file()]
        if missing:
            print("error: file not found: " + ", ".join(missing), file=sys.stderr)
            return 1
        table, _ = load_attested(paths)
        if not table:
            print(f"error: no usable pairs in {files}", file=sys.stderr)
            return 1
        splits[name] = table
    report = normcheck_markdown(normcheck_run(splits))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "normcheck.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


def cmd_make_form(args) -> int:
    try:
        ids = collect.read_prompt_ids(args.prompts)
        info = collect.make_form(args.src, ids, args.out, contact=args.contact, title=args.title)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"form with {info['prompts']} prompts written to {info['out']}")
    print("It contains CC BY-SA 4.0 sentences (Dakshina). Share it with volunteers, but do not commit it to the MIT repository.")
    return 0


def cmd_collect_build(args) -> int:
    try:
        rows, stats = collect.load_responses(args.responses)
        judgments = collect.load_judgments(args.judgments) if args.judgments else None
        if not rows:
            print("error: no usable answers found", file=sys.stderr)
            for reason, n in sorted(stats.items()):
                print(f"  {reason}: {n}", file=sys.stderr)
            return 1
        info = collect.build_real(rows, args.src, args.out, judgments)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for reason, n in sorted(stats.items()):
        print(f"{reason}: {n}")
    per = collect.writers_per_prompt(rows)
    print(f"writers per prompt: min {min(per.values())}, max {max(per.values())}")
    spell = collect.spelling_report(rows)
    if spell["mean_word_overlap_between_writers"] is not None:
        print(f"queries from different writers for one prompt share {100 * spell['mean_word_overlap_between_writers']:.0f}% of their words")
    print(json.dumps(info, indent=2))
    return 0


def _load_real(path):
    ds = load_dataset(path)
    owners_file = Path(path) / "owners.json"
    if not owners_file.is_file():
        raise ValueError(f"{owners_file} not found: build the collection with `hijje collect-build`")
    return ds, json.loads(owners_file.read_text(encoding="utf-8"))


def cmd_judge_sheet(args) -> int:
    try:
        ds, owners = _load_real(args.data)
        specs = [s.strip() for s in args.retrievers.split(",") if s.strip()]
        n = collect.judge_sheet(ds, owners, args.src, specs, args.out, args.depth)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"{n} (prompt, passage) pairs written to {args.out}")
    print("Fill the 'grade' column: 2 = gives the same information, 1 = partly, 0 = no. Then rebuild with --judgments.")
    return 0


def cmd_judge_export(args) -> int:
    try:
        n = collect.export_judgments(args.sheet, args.out)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"{n} grades written to {args.out} (sentence numbers and grades only)")
    return 0


def cmd_real_eval(args) -> int:
    try:
        ds, owners = _load_real(args.data)
        specs = [s.strip() for s in args.retrievers.split(",") if s.strip()]
        result = collect.evaluate_real(ds, owners, specs, k=args.k, seed=args.seed, n_boot=args.n_boot)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    rows = [{"prompt": o["prompt"], "writer": o["writer"], "query": ds.queries[q]} for q, o in owners.items() if q in ds.queries]
    report = collect.to_markdown(result, collect.spelling_report(rows), collect.writers_per_prompt(rows))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.md").write_text(report, encoding="utf-8")
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(report)
    return 0


def cmd_build_dakshina(args) -> int:
    try:
        info = build_collection(args.src, args.out, args.n_queries, args.query_len, args.seed)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(info, indent=2))
    print(f"written to {args.out}. These files are CC BY-SA 4.0: do not commit them to the MIT repository.")
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
    p.add_argument("--variation", default="rules", help="rules (default), attested:FILE or attested+rules:FILE")
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

    p = sub.add_parser("attested", help="check the rules against spellings written by people")
    p.add_argument("--pairs", nargs="+", required=True,
                   help="TSV files: native word, Latin spelling, optional count (Dakshina format)")
    p.add_argument("--out", help="folder for attested.md and attested.json")
    p.add_argument("--top", type=int, default=40, help="how many variation patterns to print")
    p.add_argument("--show", nargs="*", default=[], help="Latin spellings to look up, e.g. pani theek")
    p.set_defaults(func=cmd_attested)

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
    p.add_argument("--variation", default="rules", help="rules (default), attested:FILE or attested+rules:FILE")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("normcheck", help="score the normalisers on spellings people wrote")
    p.add_argument("--split", action="append", required=True, metavar="NAME=FILE[,FILE]",
                   help="a set of words to report on; repeat for dev, test, ... Collisions are measured against all splits together")
    p.add_argument("--out")
    p.set_defaults(func=cmd_normcheck)

    p = sub.add_parser("make-form", help="write the volunteer form (one HTML file)")
    p.add_argument("--src", required=True, help="Dakshina Urdu folder or the rejoined .tsv file")
    p.add_argument("--prompts", default="data/real_queries/prompt_ids.txt")
    p.add_argument("--out", required=True)
    p.add_argument("--contact", default="", help="shown to volunteers: where to send the file")
    p.add_argument("--title", default="Roman Urdu search study")
    p.set_defaults(func=cmd_make_form)

    p = sub.add_parser("collect-build", help="build a test collection from volunteers' answer files")
    p.add_argument("--responses", nargs="+", required=True, help="CSV files from volunteers (wildcards allowed)")
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--judgments", help="filled judge sheet from `hijje judge-sheet`")
    p.set_defaults(func=cmd_collect_build)

    p = sub.add_parser("judge-sheet", help="list pooled passages for a person to grade")
    p.add_argument("--data", required=True)
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--retrievers", default="bm25,bm25-l4,char")
    p.add_argument("--depth", type=int, default=3)
    p.set_defaults(func=cmd_judge_sheet)

    p = sub.add_parser("judge-export", help="keep only the grades of a filled judge sheet (safe to commit)")
    p.add_argument("--sheet", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_judge_export)

    p = sub.add_parser("real-eval", help="score retrievers on volunteers' real queries")
    p.add_argument("--data", required=True)
    p.add_argument("--out")
    p.add_argument("--retrievers", default="bm25,bm25-l2,bm25-l3,bm25-l4,char,fusion")
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--n-boot", type=int, default=2000)
    p.set_defaults(func=cmd_real_eval)

    p = sub.add_parser("build-dakshina", help="build a test collection from the Dakshina Urdu sentences")
    p.add_argument("--src", required=True, help="Dakshina Urdu folder (contains 'romanized') or the rejoined .tsv file")
    p.add_argument("--out", required=True)
    p.add_argument("--n-queries", type=int, default=1000)
    p.add_argument("--query-len", type=int, default=4)
    p.add_argument("--seed", type=int, default=13)
    p.set_defaults(func=cmd_build_dakshina)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
