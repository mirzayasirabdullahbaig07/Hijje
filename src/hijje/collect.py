"""Collecting real queries from volunteers, and testing retrievers on them.

The synthetic and constructed queries used so far answer "what if the spelling
changes?". The questions a paper must answer are "how do real people spell a
real query?" and "does search still find the passage?". This module is the
kit for that:

1. ``make_form``     a single HTML page. A volunteer reads a sentence in Urdu
                      script (so no Roman spelling is suggested) and types the
                      search query they would use, in their own Roman Urdu.
2. ``load_responses`` reads the CSV files the volunteers send back.
3. ``build_real``     turns them into a BEIR-layout test collection: all
                      Dakshina sentences are the passages, every volunteer's
                      query is a query, and the sentence it was written from
                      is the relevant passage.
4. ``judge_sheet`` /  pooled relevance judging: a query may be answered by
   ``load_judgments`` other sentences too, so the top results of every
                      retriever are listed for a person to grade.
5. ``evaluate_real``  scores retrievers on the real queries, per writer.

Privacy: the form asks for no name, e-mail or phone number. A random code
identifies a writer. It asks only the device type, the province and how often
the person writes Roman Urdu, all optional and chosen from fixed lists.
"""

from __future__ import annotations

import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional, Sequence

from .dakshina import SENTENCE_FILE, _find
from .data import Dataset, load_dataset
from .metrics import bootstrap_ci, jaccard, mean, mrr_at_k, ndcg_at_k, recall_at_k
from .retrievers import build_retriever
from .variation import derive_seed

RESPONSE_COLUMNS = ["writer", "prompt", "status", "query", "device", "province", "frequency"]
MAX_QUERY_CHARS = 200
_ARABIC_SCRIPT = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
_PROMPT_ID = re.compile(r"^s\d{5}$")


# -- prompts -----------------------------------------------------------------

def read_prompt_ids(path) -> list[str]:
    ids = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not _PROMPT_ID.match(line):
            raise ValueError(f"not a sentence number like s00042: {line!r}")
        ids.append(line)
    if len(set(ids)) != len(ids):
        raise ValueError("a sentence number is listed twice")
    if not ids:
        raise ValueError("no prompt sentence numbers found")
    return ids


def read_native_sentences(src) -> list[tuple[str, str]]:
    """(Urdu-script sentence, Roman sentence) pairs from a Dakshina ``rejoined`` file."""
    src = Path(src)
    path = src if src.is_file() else _find(src)
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1].strip():
                out.append((parts[0].strip(), parts[1].strip()))
    return out


def _index(sentence_id: str) -> int:
    return int(sentence_id[1:]) - 1


# -- the form ------------------------------------------------------------------

def make_form(src, prompt_ids: Sequence[str], out, contact: str = "", title: str = "Roman Urdu search study", endpoint: str = "") -> dict:
    """Write the volunteer form (one self-contained HTML file) to ``out``.

    With ``endpoint`` (an https address, e.g. a Google Apps Script web app, see
    ``docs/VOLUNTEER_GUIDE.md``) the form also sends the answers there when the
    volunteer finishes. The CSV download stays as a fallback.
    """
    from .form_template import FORM_HTML

    if endpoint and not endpoint.startswith("https://"):
        raise ValueError("endpoint must be an https:// address")
    sentences = read_native_sentences(src)
    prompts = []
    for sid in prompt_ids:
        i = _index(sid)
        if not 0 <= i < len(sentences):
            raise ValueError(f"{sid} is outside the sentence file ({len(sentences)} sentences)")
        prompts.append({"id": sid, "text": sentences[i][0]})
    payload = json.dumps({"prompts": prompts, "contact": contact, "title": title, "endpoint": endpoint}, ensure_ascii=False)
    # no "<" may reach the page: it could close the <script> element or open a comment
    payload = payload.replace("<", "\\u003c")
    html = FORM_HTML.replace("__PAYLOAD__", payload).replace("__TITLE__", title)
    Path(out).write_text(html, encoding="utf-8")
    return {"prompts": len(prompts), "out": str(out)}


# -- other ways to answer ------------------------------------------------------

SHEET_COLUMNS = ["writer", "prompt", "urdu", "query"]
_NUMBERED = re.compile(r"^\s*(\d{1,3})\s*[\)\.\-:،]?\s*(.*)$")


def _prompts_with_text(src, prompt_ids: Sequence[str]) -> list[tuple[str, str]]:
    sentences = read_native_sentences(src)
    out = []
    for sid in prompt_ids:
        i = _index(sid)
        if not 0 <= i < len(sentences):
            raise ValueError(f"{sid} is outside the sentence file ({len(sentences)} sentences)")
        out.append((sid, sentences[i][0]))
    return out


def make_sheet(src, prompt_ids: Sequence[str], out, writer: str) -> int:
    """A CSV a volunteer fills in with Excel or Google Sheets (one column to type in).

    ``writer`` is pre-filled, so every row of the sheet belongs to one person
    and nobody has to type a code.
    """
    if not re.match(r"^[A-Za-z0-9_-]{1,40}$", writer):
        raise ValueError("writer code: letters, digits, - and _ only")
    rows = _prompts_with_text(src, prompt_ids)
    with Path(out).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(SHEET_COLUMNS)
        for sid, text in rows:
            w.writerow([writer, sid, text, ""])
    return len(rows)


def make_text(src, prompt_ids: Sequence[str], out, intro: str = "") -> int:
    """The prompts as a numbered text, to paste into WhatsApp or e-mail."""
    rows = _prompts_with_text(src, prompt_ids)
    lines = [intro.strip(), ""] if intro.strip() else []
    lines += [f"{n}) {text}" for n, (_, text) in enumerate(rows, 1)]
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


def parse_reply(text: str, prompt_ids: Sequence[str], writer: str) -> tuple[list[dict], dict]:
    """Read a reply typed as ``3) kitni der lagegi`` lines (WhatsApp, e-mail, Notes).

    A line must start with the number of the prompt it answers. ``1)``, ``1.``,
    ``1-``, ``1:`` and a bare ``1`` all work, as do Urdu digits. Lines without a
    number, numbers outside the list and repeated numbers (the last one wins) are
    counted, never guessed at.
    """
    stats: dict = defaultdict(int)
    found: dict = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _NUMBERED.match(line)
        if not m:
            stats["lines without a number"] += 1
            continue
        n, query = int(m.group(1)), " ".join(m.group(2).split())
        if not 1 <= n <= len(prompt_ids):
            stats["number outside the list"] += 1
            continue
        if n in found:
            stats["number repeated (last kept)"] += 1
        found[n] = query
    rows = [
        {"writer": writer, "prompt": prompt_ids[n - 1], "status": "ok", "query": q,
         "device": "", "province": "", "frequency": ""}
        for n, q in sorted(found.items())
    ]
    stats["answers found"] = len(rows)
    return rows, dict(stats)


def write_responses(rows: Sequence[dict], out) -> None:
    with Path(out).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=RESPONSE_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def all_batches(folder) -> dict:
    """``{"a": [ids], "b": [ids], ...}`` from ``prompt_ids.txt`` (batch a) and ``prompt_ids_<x>.txt``."""
    out = {}
    for path in sorted(Path(folder).glob("prompt_ids*.txt")):
        stem = path.stem
        key = "a" if stem == "prompt_ids" else stem.rsplit("_", 1)[1]
        out[key] = read_prompt_ids(path)
    return dict(sorted(out.items()))


# -- responses -----------------------------------------------------------------

def load_responses(paths: Iterable[str]) -> tuple[list[dict], dict]:
    """Read volunteer CSV files. Returns (clean rows, counts of what was dropped).

    One row per (writer, prompt): if a writer answered a prompt twice, the last
    answer is kept. Every dropped row is counted by reason.
    """
    from .attested import expand_paths

    stats: dict = defaultdict(int)
    latest: dict = {}
    for path in expand_paths(paths):
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = {"writer", "prompt", "query"} - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{path}: missing column(s) {sorted(missing)}")
            for row in reader:
                stats["rows read"] += 1
                writer, prompt = (row.get("writer") or "").strip(), (row.get("prompt") or "").strip()
                query = " ".join((row.get("query") or "").split())
                if not writer or not _PROMPT_ID.match(prompt):
                    stats["dropped: bad writer or prompt code"] += 1
                    continue
                if (row.get("status") or "ok").strip() == "skip" or not query:
                    stats["dropped: skipped or empty"] += 1
                    continue
                if _ARABIC_SCRIPT.search(query):
                    stats["dropped: typed in Urdu script, not Roman"] += 1
                    continue
                if len(query) > MAX_QUERY_CHARS:
                    stats["dropped: longer than %d characters" % MAX_QUERY_CHARS] += 1
                    continue
                latest[(writer, prompt)] = {
                    "writer": writer, "prompt": prompt, "query": query,
                    "device": (row.get("device") or "").strip(),
                    "province": (row.get("province") or "").strip(),
                    "frequency": (row.get("frequency") or "").strip(),
                }
    rows = [latest[k] for k in sorted(latest)]
    stats["rows kept"] = len(rows)
    stats["writers"] = len({r["writer"] for r in rows})
    stats["prompts answered"] = len({r["prompt"] for r in rows})
    return rows, dict(stats)


def writers_per_prompt(rows: Sequence[dict]) -> dict:
    counts: dict = defaultdict(set)
    for r in rows:
        counts[r["prompt"]].add(r["writer"])
    return {p: len(w) for p, w in sorted(counts.items())}


def spelling_report(rows: Sequence[dict]) -> dict:
    """How much do different writers' queries for the same prompt differ in spelling?"""
    from .text import tokenize

    by_prompt: dict = defaultdict(list)
    for r in rows:
        by_prompt[r["prompt"]].append(tokenize(r["query"]))
    pair_overlap, distinct_queries, total_queries = [], 0, 0
    for toks in by_prompt.values():
        total_queries += len(toks)
        distinct_queries += len({tuple(t) for t in toks})
        for i in range(len(toks)):
            for j in range(i + 1, len(toks)):
                a, b = set(toks[i]), set(toks[j])
                if a | b:
                    pair_overlap.append(len(a & b) / len(a | b))
    return {
        "queries": total_queries,
        "distinct_queries": distinct_queries,
        "mean_word_overlap_between_writers": mean(pair_overlap) if pair_overlap else None,
    }


# -- the collection --------------------------------------------------------------

def build_real(rows: Sequence[dict], src, out, judgments: Optional[dict] = None) -> dict:
    """Write a BEIR-layout collection: all sentences as passages, volunteers' queries.

    judgments: optional {prompt_id: {sentence_id: grade}} from ``load_judgments``.
    The sentence a prompt was taken from is always grade 2.
    """
    sentences = read_native_sentences(src)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "corpus.jsonl").open("w", encoding="utf-8") as fh:
        for i, (_, roman) in enumerate(sentences):
            fh.write(json.dumps({"_id": f"s{i + 1:05d}", "title": "", "text": roman}, ensure_ascii=False) + "\n")
    queries, qrels, owner = [], [], {}
    for n, r in enumerate(rows, 1):
        qid = f"r{n:04d}"
        owner[qid] = {"writer": r["writer"], "prompt": r["prompt"]}
        queries.append({"_id": qid, "text": r["query"]})
        grades = {r["prompt"]: 2}
        for sid, g in (judgments or {}).get(r["prompt"], {}).items():
            if sid != r["prompt"]:
                grades[sid] = g
        for sid, g in grades.items():
            if g > 0:
                qrels.append((qid, sid, g))
    with (out / "queries.jsonl").open("w", encoding="utf-8") as fh:
        for q in queries:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")
    with (out / "qrels.tsv").open("w", encoding="utf-8") as fh:
        fh.write("query-id\tcorpus-id\tscore\n")
        for qid, sid, g in qrels:
            fh.write(f"{qid}\t{sid}\t{g}\n")
    (out / "owners.json").write_text(json.dumps(owner, indent=1) + "\n", encoding="utf-8")
    info = {
        "queries": len(queries),
        "writers": len({r["writer"] for r in rows}),
        "prompts": len({r["prompt"] for r in rows}),
        "judged_prompts": len(judgments or {}),
        "licence": "passages: CC BY-SA 4.0 (Dakshina, Roark et al. 2020); queries: written by volunteers",
    }
    (out / "build_info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


# -- pooled judging ----------------------------------------------------------------

JUDGE_COLUMNS = ["prompt", "prompt_text", "candidate", "candidate_text", "grade"]


def judge_sheet(ds: Dataset, owners: dict, src, retrievers: Sequence[str], out, depth: int = 3,
                max_per_prompt: Optional[int] = 10) -> int:
    """List every passage that any retriever ranks in its top ``depth`` for any query.

    Each row is one (prompt, passage) pair to grade, shared by all writers of the
    prompt: 2 = the passage gives the information the prompt sentence gives,
    1 = partly, 0 = no. The prompt's own sentence is not listed (it is always 2).
    """
    sentences = read_native_sentences(src)
    doc_ids = sorted(ds.corpus)
    texts = [ds.corpus[d] for d in doc_ids]
    qids = sorted(ds.queries)
    pooled: dict = defaultdict(lambda: defaultdict(int))
    for spec in retrievers:
        retriever = build_retriever(spec)
        retriever.index(doc_ids, texts)
        runs = retriever.search_batch([ds.queries[q] for q in qids], depth)
        for qid, run in zip(qids, runs):
            prompt = owners[qid]["prompt"]
            for d, _ in run:
                if d != prompt:
                    pooled[prompt][d] += 1
    n = 0
    with Path(out).open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=JUDGE_COLUMNS)
        writer.writeheader()
        for prompt in sorted(pooled):
            counts = pooled[prompt]
            keep = sorted(counts, key=lambda d: (-counts[d], d))
            if max_per_prompt is not None:
                keep = keep[:max_per_prompt]
            for cand in sorted(keep):
                writer.writerow({
                    "prompt": prompt, "prompt_text": sentences[_index(prompt)][0],
                    "candidate": cand, "candidate_text": sentences[_index(cand)][0], "grade": "",
                })
                n += 1
    return n


def export_judgments(judge_csv, out) -> int:
    """Write only the grades (prompt, candidate, grade) of a filled judge sheet.

    The judge sheet holds CC BY-SA sentence text; this three-column file holds only
    sentence numbers and grades, so it can live in the repository.
    """
    grades = load_judgments(judge_csv)
    n = 0
    with Path(out).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["prompt", "candidate", "grade"])
        for prompt in sorted(grades):
            for cand in sorted(grades[prompt]):
                writer.writerow([prompt, cand, grades[prompt][cand]])
                n += 1
    return n


def load_judgments(path) -> dict:
    """Read a filled judge sheet into {prompt: {sentence: grade}}. Blank grades are ignored."""
    out: dict = defaultdict(dict)
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            grade = (row.get("grade") or "").strip()
            if not grade:
                continue
            if grade not in {"0", "1", "2"}:
                raise ValueError(f"grade must be 0, 1 or 2, got {grade!r} for {row.get('prompt')}/{row.get('candidate')}")
            out[row["prompt"].strip()][row["candidate"].strip()] = int(grade)
    return dict(out)


# -- evaluation ---------------------------------------------------------------------

def evaluate_real(ds: Dataset, owners: dict, retrievers: Sequence[str], k: int = 10, seed: int = 13, n_boot: int = 2000) -> dict:
    """Score retrievers on real queries. Numbers are averaged per prompt first.

    worst_writer   the lowest nDCG among the writers of a prompt, averaged over
                   prompts: the writer with the unlucky spelling.
    agreement      mean overlap (Jaccard) of the top-k of two writers' queries
                   for the same prompt: do different spellings return the same results?
    """
    doc_ids = sorted(ds.corpus)
    texts = [ds.corpus[d] for d in doc_ids]
    qids = sorted(q for q in ds.queries if q in ds.qrels)
    result = {"queries": len(qids), "prompts": len({owners[q]["prompt"] for q in qids}), "k": k, "retrievers": {}}
    for spec in retrievers:
        retriever = build_retriever(spec)
        retriever.index(doc_ids, texts)
        runs = retriever.search_batch([ds.queries[q] for q in qids], k)
        ranked = {q: [d for d, _ in run] for q, run in zip(qids, runs)}
        per_prompt: dict = defaultdict(lambda: {"ndcg": [], "recall": [], "mrr": [], "ids": []})
        for q in qids:
            bucket = per_prompt[owners[q]["prompt"]]
            bucket["ndcg"].append(ndcg_at_k(ranked[q], ds.qrels[q], k))
            bucket["recall"].append(recall_at_k(ranked[q], ds.qrels[q], k))
            bucket["mrr"].append(mrr_at_k(ranked[q], ds.qrels[q], k))
            bucket["ids"].append(ranked[q])
        prompts = sorted(per_prompt)
        ndcg = [mean(per_prompt[p]["ndcg"]) for p in prompts]
        worst = [min(per_prompt[p]["ndcg"]) for p in prompts]
        agree = []
        for p in prompts:
            ids = per_prompt[p]["ids"]
            agree += [jaccard(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))]
        lo, hi = bootstrap_ci(ndcg, n_boot, seed=derive_seed(seed, "real-ci", spec))
        result["retrievers"][retriever.name] = {
            "ndcg": mean(ndcg), "ndcg_ci": [lo, hi],
            "recall": mean([mean(per_prompt[p]["recall"]) for p in prompts]),
            "mrr": mean([mean(per_prompt[p]["mrr"]) for p in prompts]),
            "worst_writer_ndcg": mean(worst),
            "agreement": mean(agree) if agree else None,
        }
    return result


def to_markdown(result: dict, spell: Optional[dict] = None, writers: Optional[dict] = None) -> str:
    k = result["k"]
    out = ["# Hijje on real queries", ""]
    out.append(f"{result['queries']} queries written by volunteers for {result['prompts']} prompts. "
               "Each number is averaged over prompts first, so a prompt with many writers does not count more.")
    if writers:
        counts = sorted(writers.values())
        out.append(f"Writers per prompt: minimum {counts[0]}, median {counts[len(counts) // 2]}, maximum {counts[-1]}.")
    if spell and spell.get("mean_word_overlap_between_writers") is not None:
        out.append(f"Different writers' queries for the same prompt share {100 * spell['mean_word_overlap_between_writers']:.0f}% of their words "
                   f"on average ({spell['distinct_queries']} distinct queries out of {spell['queries']}).")
    out += ["", f"| Retriever | nDCG@{k} | 95% CI | Recall@{k} | MRR | Worst writer | Agreement |", "|---|---|---|---|---|---|---|"]
    for name, r in result["retrievers"].items():
        agree = "–" if r["agreement"] is None else f"{r['agreement']:.3f}"
        out.append(f"| {name} | {r['ndcg']:.3f} | {r['ndcg_ci'][0]:.3f}–{r['ndcg_ci'][1]:.3f} | {r['recall']:.3f} | {r['mrr']:.3f} | {r['worst_writer_ndcg']:.3f} | {agree} |")
    out += ["", "*Worst writer*: lowest nDCG among the writers of a prompt, averaged over prompts. "
            "*Agreement*: overlap of the top results of two writers' queries for the same prompt.", ""]
    return "\n".join(out)
