"""Cleaning volunteer answers, and telling what kind of answer each one is.

Why this exists
---------------
The form asked people to type "the search you would use" for an Urdu sentence.
Many people instead typed the whole sentence in Roman Urdu. Both are valuable
but they are different things:

transliteration  most of the sentence was written out (a person's own spelling
                 of the whole sentence)
keywords         a short search made of words of the sentence
other            long or mixed answers that are neither
unrelated        no word of the answer resembles any word of the sentence
                 ("yes", "hah", "nothing", an unrelated question)

An answer is compared with the sentence it was written for, word by word, with
a *fuzzy* match, because the whole point of the study is that the same word is
spelled in many ways. A monotone alignment (words keep their order) is used.

Thresholds are fixed here and are listed in ``docs/DEVIATIONS.md``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Optional, Sequence

from .collect import load_responses, read_native_sentences
from .dakshina import MAX_DF_SHARE, _query_words
from .text import tokenize

MATCH_SIM = 0.7         # two words count as "the same word" at this string similarity
TRANSLIT_MIN = 0.6      # share of the sentence's words written out, and share of the answer that is sentence words
KEYWORD_MAX_WORDS = 8
KEYWORD_MIN_PRECISION = 0.5


@lru_cache(maxsize=None)
def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def align(query: Sequence[str], passage: Sequence[str]) -> list[tuple[int, int]]:
    """Monotone fuzzy alignment: pairs (query index, passage index) of the same word."""
    n, m = len(query), len(passage)
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            s = _sim(query[i], passage[j])
            take = s + best[i + 1][j + 1] if s >= MATCH_SIM else -1.0
            best[i][j] = max(take, best[i + 1][j], best[i][j + 1])
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        s = _sim(query[i], passage[j])
        if s >= MATCH_SIM and abs(best[i][j] - (s + best[i + 1][j + 1])) < 1e-9:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif best[i][j] == best[i + 1][j]:
            i += 1
        else:
            j += 1
    return pairs


def classify(query: str, passage: str) -> dict:
    q, p = tokenize(query), tokenize(passage)
    pairs = align(q, p)
    matched = len(pairs)
    long_matches = sum(1 for qi, pj in pairs if len(q[qi]) >= 4 and len(p[pj]) >= 4)   # "yes" must not match "ye"
    coverage = matched / len(p) if p else 0.0
    precision = matched / len(q) if q else 0.0
    if long_matches == 0:
        style = "unrelated"
    elif coverage >= TRANSLIT_MIN and precision >= TRANSLIT_MIN:
        style = "transliteration"
    elif len(q) <= KEYWORD_MAX_WORDS and precision >= KEYWORD_MIN_PRECISION and coverage < TRANSLIT_MIN:
        style = "keywords"
    else:
        style = "other"
    return {"style": style, "coverage": round(coverage, 3), "precision": round(precision, 3)}


def clean_answers(paths, src, min_answers: int = 4, keep_unrelated: bool = False,
                  exclude_writers: Sequence[str] = ()) -> tuple[list[dict], dict]:
    """Rules of the analysis plan (``load_responses``), then the answer-type check.

    ``exclude_writers``: codes of the researcher's own test answers (exclusion 1 of the plan).
    """
    rows, stats = load_responses(paths, min_answers=min_answers)
    banned = {w.strip() for w in exclude_writers if w.strip()}
    if banned:
        stats["dropped: the researcher's own test answers"] = sum(1 for r in rows if r["writer"] in banned)
        rows = [r for r in rows if r["writer"] not in banned]
    sentences = read_native_sentences(src)
    kept = []
    styles: Counter = Counter()
    for r in rows:
        roman = sentences[int(r["prompt"][1:]) - 1][1]
        r = {**r, **classify(r["query"], roman)}
        styles[r["style"]] += 1
        if r["style"] == "unrelated" and not keep_unrelated:
            continue
        kept.append(r)
    stats = dict(stats)
    stats["answer types before the unrelated filter"] = dict(styles)
    if not keep_unrelated:
        stats["dropped: unrelated to the sentence"] = styles["unrelated"]
    stats["rows kept after cleaning"] = len(kept)
    stats["writers after cleaning"] = len({r["writer"] for r in kept})
    stats["prompts after cleaning"] = len({r["prompt"] for r in kept})
    return kept, stats


def constructed_words(sentences_roman: Sequence[str], query_len: int = 4) -> dict:
    """{prompt id: the distinctive words the constructed query would use}.

    Exactly the rule of ``dakshina.build_collection`` (df between 2 and 2% of sentences).
    """
    token_lists = [tokenize(s) for s in sentences_roman]
    df: Counter = Counter()
    for t in token_lists:
        df.update(set(t))
    n_docs = len(sentences_roman)
    out = {}
    for i, toks in enumerate(token_lists):
        words = _query_words(toks, df, n_docs, query_len)
        if words:
            out[f"s{i + 1:05d}"] = words
    return out


def volunteer_spelling_of(words: Sequence[str], query: str, passage: str) -> Optional[list[str]]:
    """The volunteer's own spelling of the given passage words, or None if one is missing."""
    q, p = tokenize(query), tokenize(passage)
    where = {pj: qi for qi, pj in align(q, p)}
    out = []
    for w in words:
        if w not in p:
            return None
        pj = p.index(w)
        if pj not in where:
            return None
        out.append(q[where[pj]])
    return out


def report_markdown(stats: dict) -> str:
    lines = ["# Cleaning report", "", "| Step | Rows |", "|---|---|"]
    for k, v in stats.items():
        if isinstance(v, dict):
            continue
        lines.append(f"| {k} | {v} |")
    types = stats.get("answer types before the unrelated filter")
    if types:
        total = sum(types.values())
        lines += ["", "Answer types (after the plan's rules):", "", "| Type | Answers | Share |", "|---|---|---|"]
        for k in ("transliteration", "keywords", "other", "unrelated"):
            lines.append(f"| {k} | {types.get(k, 0)} | {100 * types.get(k, 0) / total:.0f}% |")
    lines.append("")
    return "\n".join(lines)
