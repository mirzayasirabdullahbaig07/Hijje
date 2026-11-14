"""Building a retrieval test collection from the Dakshina Urdu sentences.

Source: the Dakshina dataset (Roark et al., 2020), Urdu part, licence
CC BY-SA 4.0. The file used is ``ur/romanized/ur.romanized.rejoined.tsv``:
one line per sentence, native-script sentence <TAB> the same sentence written
in Roman letters by a person.

What the collection is
----------------------
- Passages: every Roman-script sentence (about 9,800). They are real text
  written by people, in each writer's own spelling. They are never changed.
- Queries: for a sample of sentences, the few most distinctive words of the
  sentence, in the writer's own spelling. This is a keyword-style query.
- Relevance: the sentence the query came from (grade 2). Any other sentence
  that contains all of the query's words also counts (grade 1), so a retriever
  is not punished for finding a true duplicate.

What it is not
--------------
The queries are *constructed* from the passages, not written by users with an
information need. A word-matching retriever therefore starts with a large
advantage on clean queries. The value of the collection is the test it allows
afterwards: respell the query words the way other people spell them and see
what is lost. See ``docs/DATASETS.md`` for the full list of limits.

The built files are derived from CC BY-SA 4.0 text. They are therefore not
committed to this repository (which is MIT); build them locally.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Optional

from .text import tokenize
from .variation import derive_seed

SENTENCE_FILE = "ur.romanized.rejoined.tsv"
MIN_WORD_LEN = 3
MAX_DF_SHARE = 0.02       # words in more than 2% of sentences are too common


def read_sentences(path) -> list[str]:
    """Roman-script sentences from a Dakshina ``rejoined`` file, in file order."""
    sentences = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1].strip():
                sentences.append(parts[1].strip())
    return sentences


def _query_words(tokens: list[str], df: Counter, n_docs: int, length: int) -> Optional[list[str]]:
    """The `length` most distinctive usable words, kept in sentence order."""
    max_df = max(2, int(MAX_DF_SHARE * n_docs))
    seen, usable = set(), []
    for pos, tok in enumerate(tokens):
        if tok in seen or len(tok) < MIN_WORD_LEN or not (tok.isascii() and tok.isalpha()):
            continue
        if not 2 <= df[tok] <= max_df:
            continue
        seen.add(tok)
        usable.append((-math.log(n_docs / df[tok]), pos, tok))
    if len(usable) < length:
        return None
    best = sorted(usable)[:length]
    return [tok for _, _, tok in sorted(best, key=lambda t: t[1])]


def build_collection(
    src,
    out,
    n_queries: int = 1000,
    query_len: int = 4,
    seed: int = 13,
) -> dict:
    """Write ``corpus.jsonl``, ``queries.jsonl`` and ``qrels.tsv`` to ``out``.

    ``src`` is the Dakshina Urdu folder (the one that contains ``romanized/``),
    or the ``ur.romanized.rejoined.tsv`` file itself.
    """
    src = Path(src)
    path = src if src.is_file() else _find(src)
    sentences = read_sentences(path)
    if not sentences:
        raise ValueError(f"no sentences found in {path}")

    token_lists = [tokenize(s) for s in sentences]
    token_sets = [set(t) for t in token_lists]
    df: Counter = Counter()
    for ts in token_sets:
        df.update(ts)
    n_docs = len(sentences)

    # Order sentences by a seeded hash so the sample never depends on file order
    # or on Python's random module.
    order = sorted(range(n_docs), key=lambda i: derive_seed(seed, "sentence", i))
    queries, qrels = [], []
    for i in order:
        if len(queries) >= n_queries:
            break
        words = _query_words(token_lists[i], df, n_docs, query_len)
        if words is None:
            continue
        qid = f"q{len(queries) + 1:05d}"
        queries.append({"_id": qid, "text": " ".join(words)})
        wanted = set(words)
        qrels.append((qid, f"s{i + 1:05d}", 2))
        for j in range(n_docs):
            if j != i and wanted <= token_sets[j]:
                qrels.append((qid, f"s{j + 1:05d}", 1))

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "corpus.jsonl").open("w", encoding="utf-8") as fh:
        for i, s in enumerate(sentences):
            fh.write(json.dumps({"_id": f"s{i + 1:05d}", "title": "", "text": s}, ensure_ascii=False) + "\n")
    with (out / "queries.jsonl").open("w", encoding="utf-8") as fh:
        for q in queries:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")
    with (out / "qrels.tsv").open("w", encoding="utf-8") as fh:
        fh.write("query-id\tcorpus-id\tscore\n")
        for qid, did, score in qrels:
            fh.write(f"{qid}\t{did}\t{score}\n")

    info = {
        "source_file": path.name,
        "sentences": n_docs,
        "queries": len(queries),
        "query_len": query_len,
        "seed": seed,
        "extra_relevant": sum(1 for _, _, s in qrels if s == 1),
        "licence": "CC BY-SA 4.0 (Dakshina, Roark et al. 2020)",
    }
    (out / "build_info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


def _find(folder: Path) -> Path:
    hits = sorted(folder.rglob(SENTENCE_FILE))
    if not hits:
        raise FileNotFoundError(
            f"{SENTENCE_FILE} not found under {folder}. Point --src at the Dakshina "
            "Urdu folder (the one that contains 'romanized')."
        )
    return hits[0]
