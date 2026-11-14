"""Measuring the phonetic normalisers directly on spellings people wrote.

``attested.py`` asks how well the *respelling rules* match human spellings.
This module asks the same question of the *normalisers* (levels 0-4), without
any search engine in the way. For every level it measures two things:

unified pairs
    Take every pair of different spellings that people wrote for the same Urdu
    word. What share of those pairs gets the same key? Higher is better: the
    normaliser brings the spellings together.

extra shared keys
    What share of the Urdu words has a key that some other Urdu word also has,
    beyond what already happens with no normalisation at all (level 0)? Lower
    is better. This is an *upper bound* on false merges: two spellings of one
    Urdu word in different Urdu-script forms would count here although merging
    them is correct.

The two numbers pull against each other, and the table shows where each level
sits between them. Use the split files that Dakshina provides (train / dev /
test contain different words) so that a normaliser tuned on one is judged on
words it never saw.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping

from .normalize import LEVEL_NAMES, LEVELS, normalize_word

Table = Mapping[str, Mapping[str, int]]


def unified_pairs(table: Table, level: int) -> tuple[float, int]:
    """(share of same-word spelling pairs that share a key, number of pairs)."""
    pairs = unified = 0
    for spellings in table.values():
        keys = [normalize_word(s, level) for s in sorted(spellings)]
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                pairs += 1
                unified += keys[i] == keys[j]
    return (unified / pairs if pairs else 0.0), pairs


def share_with_shared_key(words: Table, vocabulary: Table, level: int) -> float:
    """Share of ``words`` that have a key which another word of ``vocabulary`` also has."""
    owners: dict[str, set] = defaultdict(set)
    for native, spellings in vocabulary.items():
        for s in spellings:
            owners[normalize_word(s, level)].add(native)
    shared = {native for group in owners.values() if len(group) > 1 for native in group}
    return sum(1 for native in words if native in shared) / len(words) if words else 0.0


def check(splits: Mapping[str, Table], levels=LEVELS) -> dict:
    """Score every level on every split; collisions are measured against all words."""
    vocabulary: dict = {}
    for table in splits.values():
        vocabulary.update(table)
    base = {name: share_with_shared_key(t, vocabulary, 0) for name, t in splits.items()}
    result: dict = {"words": {n: len(t) for n, t in splits.items()}, "levels": {}}
    for level in levels:
        row = {}
        for name, table in splits.items():
            unified, n_pairs = unified_pairs(table, level)
            row[name] = {
                "unified_pairs": unified,
                "pairs": n_pairs,
                "extra_shared_keys": share_with_shared_key(table, vocabulary, level) - base[name],
            }
        result["levels"][str(level)] = row
    return result


def to_markdown(result: dict, title: str = "Normalisers checked on human spellings") -> str:
    names = list(result["words"])
    out = [f"# {title}", ""]
    out.append("Words per split: " + ", ".join(f"{n} {w}" for n, w in result["words"].items()) + ".")
    out += [
        "",
        "*Unified pairs*: share of the different spellings of one Urdu word that get one key (higher is better).",
        "*Extra shared keys*: share of words whose key another word also has, beyond level 0 "
        "(lower is better; an upper bound on false merges).",
        "",
    ]
    header = ["Level"] + [f"{n}: unified" for n in names] + [f"{n}: extra shared" for n in names]
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * len(header))
    for level, row in result["levels"].items():
        cells = [f"{level} {LEVEL_NAMES[int(level)]}"]
        cells += [f"{100 * row[n]['unified_pairs']:.1f}%" for n in names]
        cells += [f"{100 * row[n]['extra_shared_keys']:+.1f} pts" for n in names]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"
