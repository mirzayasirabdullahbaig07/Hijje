"""Checking the variation rules against spellings that people actually wrote.

The rules in ``variation.py`` are one person's model of how Roman Urdu is
respelled. This module compares that model with human data: files in which the
same native-script word appears with one or more Latin-script spellings
written by people.

Input format, one pair per line, tab-separated:

    native-script word <TAB> Latin-script spelling [<TAB> count]

This is the format of the Dakshina romanization lexicons
(``ur/lexicons/ur.translit.sampled.*.tsv``) and of its token-aligned romanized
sentences (``ur/romanized/ur.romanized.rejoined.aligned.cased_nopunct.tsv``).

Three questions are answered:

1. How do people's spellings of one word differ? (``variation_patterns``)
2. For each rule, how many of the respellings it generates did a person also
   write? (``rule_check``)
3. What did people write for one particular word? (``lookup``)
"""

from __future__ import annotations

import difflib
import glob as _glob
import re
import string
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Iterable, Optional

from .variation import LEXICON_RULE, RULES, VariationModel

_LATIN_WORD = re.compile(r"^[a-z]+$")
_EDGE_PUNCT = string.punctuation + "“”‘’،۔؟"
NOTHING = "(nothing)"
WORD_END = " [word end]"


def expand_paths(patterns: Iterable[str]) -> list[str]:
    """Expand wildcards ourselves, because PowerShell does not do it."""
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(_glob.glob(str(pattern), recursive=True))
        paths.extend(matches if matches else [str(pattern)])
    return paths


def load_attested(paths: Iterable[str]) -> tuple[dict, dict]:
    """Read (native word, Latin spelling, count) files.

    Returns ``(table, stats)`` where ``table[native][spelling]`` is the summed
    count. Lines that cannot be used are counted in ``stats`` by reason, so
    that nothing is dropped silently.
    """
    table: dict = defaultdict(Counter)
    stats: Counter = Counter()
    for path in expand_paths(paths):
        with Path(path).open(encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
                    stats["skipped: malformed line"] += 1
                    continue
                native = parts[0].strip()
                if native == "</s>":
                    continue  # sentence separator in the aligned files
                roman = parts[1].strip().lower().strip(_EDGE_PUNCT)
                native = native.strip(_EDGE_PUNCT)
                if " " in native or " " in roman:
                    stats["skipped: more than one word on the line"] += 1
                    continue
                if not native or native.isascii():
                    stats["skipped: source word is not in native script"] += 1
                    continue
                if not _LATIN_WORD.match(roman):
                    stats["skipped: spelling has digits or symbols"] += 1
                    continue
                count = 1
                if len(parts) >= 3 and parts[2].strip().isdigit():
                    count = int(parts[2])
                table[native][roman] += count
                stats["pairs read"] += 1
    return dict(table), dict(stats)


def diff_patterns(a: str, b: str) -> list[str]:
    """Label each place where two spellings of the same word differ.

    Examples: ("pani", "paani") -> ["a ~ aa"]; ("theek", "thik") -> ["i ~ ee"];
    ("sawal", "saval") -> ["v ~ w"]; ("karna", "krna") -> ["a ~ (nothing)"];
    ("pani", "pany") -> ["i ~ y [word end]"].
    """
    labels = []
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        x, y = a[i1:i2], b[j1:j2]
        if x and y:
            label = " ~ ".join(sorted((x, y), key=lambda s: (len(s), s)))
        else:
            piece = x or y
            longer, pos = (a, i1) if x else (b, j1)
            before = longer[pos - 1] if pos > 0 else ""
            after = longer[pos + len(piece)] if pos + len(piece) < len(longer) else ""
            if len(piece) == 1 and piece in (before, after):
                label = f"{piece} ~ {piece}{piece}"      # a doubled letter
            else:
                label = f"{piece} ~ {NOTHING}"
        at_end = i2 == len(a) and j2 == len(b)
        labels.append(label + (WORD_END if at_end else ""))
    return labels


def summary(table: dict) -> dict:
    words = len(table)
    multi = sum(1 for spellings in table.values() if len(spellings) > 1)
    total = sum(len(spellings) for spellings in table.values())
    return {
        "native_words": words,
        "words_with_several_spellings": multi,
        "distinct_spellings": total,
        "spellings_per_word": (total / words) if words else 0.0,
    }


def variation_patterns(table: dict) -> list[dict]:
    """How spellings of the same word differ, most widespread pattern first.

    A pattern is counted once per native word, however many of that word's
    spelling pairs show it.
    """
    words_with: dict = defaultdict(set)
    example: dict = {}
    clean_example: set = set()   # patterns whose example pair differs in that one way only
    for native in sorted(table):
        forms = sorted(table[native])
        for x, y in combinations(forms, 2):
            labels = diff_patterns(x, y)
            for label in labels:
                words_with[label].add(native)
                if label not in example or (len(labels) == 1 and label not in clean_example):
                    example[label] = (x, y)
                    if len(labels) == 1:
                        clean_example.add(label)
    ranked = sorted(words_with, key=lambda label: (-len(words_with[label]), label))
    return [
        {"pattern": label, "words": len(words_with[label]), "example": list(example[label])}
        for label in ranked
    ]


def _candidates_by_rule(model: VariationModel, word: str) -> dict:
    """Respellings of one word, kept separate for every rule that produces them."""
    out = {}
    listed = {v for v in model.lexicon.get(word, ()) if v != word}
    if listed:
        out[LEXICON_RULE] = listed
    for rule in model.rules:
        produced = {v for v in rule.apply(word) if v and v.isalpha() and v != word}
        if produced:
            out[rule.name] = produced
    return out


def rule_check(table: dict, model: Optional[VariationModel] = None) -> dict:
    """Compare what the rules generate with what people wrote.

    Only words with at least two attested spellings are used. For every
    attested spelling, every rule is applied; a generated respelling counts as
    "attested" if a person also wrote it for the same word.

    The share is a lower bound on how realistic a rule is: a respelling that
    nobody in a small group of annotators happened to write is not thereby
    wrong. Comparing rules with each other is safer than reading one share
    alone.
    """
    model = model or VariationModel()
    per_rule = {
        name: {"generated": 0, "attested": 0, "attested_example": None, "unattested_example": None}
        for name in model.rule_names()
    }
    pairs = explained = 0
    for native in sorted(table):
        forms = sorted(table[native])
        if len(forms) < 2:
            continue
        written = set(forms)
        produced = {form: _candidates_by_rule(model, form) for form in forms}
        for form in forms:
            for rule, variants in produced[form].items():
                entry = per_rule[rule]
                for variant in sorted(variants):
                    entry["generated"] += 1
                    if variant in written:
                        entry["attested"] += 1
                        if entry["attested_example"] is None:
                            entry["attested_example"] = [form, variant]
                    elif entry["unattested_example"] is None:
                        entry["unattested_example"] = [form, variant]
        reach = {form: set().union(*produced[form].values()) if produced[form] else set() for form in forms}
        for x, y in combinations(forms, 2):
            pairs += 1
            if y in reach[x] or x in reach[y]:
                explained += 1
    for entry in per_rule.values():
        entry["share"] = entry["attested"] / entry["generated"] if entry["generated"] else None
    return {
        "per_rule": per_rule,
        "attested_pairs": pairs,
        "pairs_explained_by_one_edit": explained,
        "coverage": explained / pairs if pairs else None,
    }


def lookup(table: dict, roman_words: Iterable[str], max_words: int = 5) -> dict:
    """For each Latin spelling: the native words written that way and all their spellings."""
    index: dict = defaultdict(list)
    for native, spellings in table.items():
        for roman in spellings:
            index[roman].append(native)
    out = {}
    for word in roman_words:
        key = word.lower()
        natives = sorted(index.get(key, []), key=lambda n: (-sum(table[n].values()), n))[:max_words]
        out[key] = [
            {"native": n, "spellings": sorted(table[n].items(), key=lambda kv: (-kv[1], kv[0]))}
            for n in natives
        ]
    return out


def analyze(paths: Iterable[str], show: Iterable[str] = (), model: Optional[VariationModel] = None) -> dict:
    files = expand_paths(paths)
    table, stats = load_attested(files)
    return {
        "files": files,
        "read": stats,
        "summary": summary(table),
        "patterns": variation_patterns(table),
        "rules": rule_check(table, model),
        "lookup": lookup(table, show),
    }


# ----------------------------------------------------------------- reporting

def _row(cells) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def to_markdown(result: dict, top: int = 40) -> str:
    s = result["summary"]
    lines = ["# Rules checked against human-written spellings", ""]
    lines.append("Files: " + ", ".join(Path(f).name for f in result["files"]))
    lines.append("")
    for reason, n in sorted(result["read"].items()):
        lines.append(f"- {reason}: {n}")
    lines += [
        "",
        f"{s['native_words']} native-script words, {s['distinct_spellings']} distinct spellings "
        f"({s['spellings_per_word']:.2f} per word); {s['words_with_several_spellings']} words were "
        "spelled in more than one way.",
        "",
        "## How people's spellings of one word differ",
        "",
        "Each pattern is counted once per word. `a ~ aa` means one spelling has `a` where another "
        f"has `aa`; `{NOTHING}` means the letter is simply absent in one spelling.",
        "",
        _row(["Pattern", "Words", "Example"]),
        _row(["---", "---", "---"]),
    ]
    for p in result["patterns"][:top]:
        lines.append(_row([f"`{p['pattern']}`", p["words"], f"{p['example'][0]} / {p['example'][1]}"]))
    remaining = len(result["patterns"]) - top
    if remaining > 0:
        lines += ["", f"{remaining} rarer patterns are in the JSON file."]

    r = result["rules"]
    examples = {rule.name: rule.example for rule in RULES}
    lines += [
        "",
        "## Do the rules generate what people write?",
        "",
        "For every word with several human spellings, each rule was applied to each spelling. "
        "*Also written by a person* counts the generated respellings that a person wrote for the "
        "same word. The share is a lower bound: few people spelled each word, so a missing "
        "spelling is not proof that it is wrong. Compare the rules with each other.",
        "",
        _row(["Rule", "Rule's own example", "Generated", "Also written by a person", "Share", "Generated but not seen"]),
        _row(["---"] * 6),
    ]
    for name, e in r["per_rule"].items():
        ex = examples.get(name)
        share = "–" if e["share"] is None else f"{100 * e['share']:.1f}%"
        miss = "–" if not e["unattested_example"] else f"{e['unattested_example'][0]} → {e['unattested_example'][1]}"
        lines.append(_row([f"`{name}`", f"{ex[0]} → {ex[1]}" if ex else "word list", e["generated"], e["attested"], share, miss]))
    if r["coverage"] is not None:
        lines += [
            "",
            f"Of {r['attested_pairs']} pairs of human spellings of the same word, "
            f"{r['pairs_explained_by_one_edit']} ({100 * r['coverage']:.1f}%) differ by exactly one rule "
            "edit. The rest differ in ways the rules do not model, or by more than one edit.",
        ]

    if result["lookup"]:
        lines += ["", "## What people wrote for particular words", ""]
        for word, entries in result["lookup"].items():
            if not entries:
                lines.append(f"- **{word}**: not found in these files")
                continue
            for entry in entries:
                spellings = ", ".join(f"{sp} ({n})" for sp, n in entry["spellings"])
                lines.append(f"- **{word}** = {entry['native']}: {spellings}")
    return "\n".join(lines) + "\n"
