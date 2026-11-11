"""Dataset loading in the BEIR file layout.

    corpus.jsonl          {"_id": "d001", "title": "", "text": "..."}
    queries.jsonl         {"_id": "q001", "text": "..."}
    qrels.tsv             query-id <TAB> corpus-id <TAB> score
                          (qrels/test.tsv is also accepted)
    protected_terms.txt   optional, one word per line; never respelled

BEIR's layout is used so that any BEIR-format dataset works without changes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union


@dataclass
class Dataset:
    name: str
    corpus: dict            # doc_id -> text
    queries: dict           # query_id -> text
    qrels: dict             # query_id -> {doc_id: grade}
    protected: frozenset = field(default_factory=frozenset)

    def stats(self) -> dict:
        judged = sum(len(v) for v in self.qrels.values())
        return {
            "name": self.name,
            "documents": len(self.corpus),
            "queries": len(self.queries),
            "relevance_judgements": judged,
            "protected_terms": len(self.protected),
        }


def _read_jsonl(path: Path, what: str) -> dict:
    out = {}
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = str(row["_id"])
            if key in out:
                raise ValueError(f"{path}:{line_no}: duplicate {what} id {key!r}")
            title = (row.get("title") or "").strip()
            text = (row.get("text") or "").strip()
            out[key] = f"{title} {text}".strip() if title else text
    return out


def _read_qrels(path: Path) -> dict:
    qrels: dict = {}
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or not parts[0].strip():
                continue
            try:
                grade = int(parts[2])
            except ValueError:
                if line_no == 1:
                    continue  # header row
                raise ValueError(f"{path}:{line_no}: score must be an integer")
            qrels.setdefault(parts[0].strip(), {})[parts[1].strip()] = grade
    return qrels


def load_dataset(path: Union[str, Path]) -> Dataset:
    root = Path(path)
    if not root.is_dir():
        raise FileNotFoundError(f"dataset directory not found: {root}")
    qrels_path = root / "qrels.tsv"
    if not qrels_path.exists():
        qrels_path = root / "qrels" / "test.tsv"
    protected_path = root / "protected_terms.txt"
    protected = frozenset()
    if protected_path.exists():
        lines = protected_path.read_text(encoding="utf-8").splitlines()
        protected = frozenset(
            ln.strip().lower() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")
        )
    return Dataset(
        name=root.name,
        corpus=_read_jsonl(root / "corpus.jsonl", "document"),
        queries=_read_jsonl(root / "queries.jsonl", "query"),
        qrels=_read_qrels(qrels_path),
        protected=protected,
    )


def validate(ds: Dataset) -> list:
    """Return a list of problems; an empty list means the dataset is usable."""
    problems = []
    if not ds.corpus:
        problems.append("corpus is empty")
    if not ds.queries:
        problems.append("there are no queries")
    for doc_id, text in ds.corpus.items():
        if not text:
            problems.append(f"document {doc_id} has no text")
    for qid, text in ds.queries.items():
        if not text:
            problems.append(f"query {qid} has no text")
        if not any(g > 0 for g in ds.qrels.get(qid, {}).values()):
            problems.append(f"query {qid} has no relevant document")
    for qid, judged in ds.qrels.items():
        if qid not in ds.queries:
            problems.append(f"qrels mention unknown query {qid}")
        for doc_id in judged:
            if doc_id not in ds.corpus:
                problems.append(f"qrels for {qid} mention unknown document {doc_id}")
    return problems
