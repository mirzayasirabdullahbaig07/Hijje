"""Native-speaker review of generated respellings.

The variation rules are a model. The only way to know whether a rule writes
things people really write is to ask people. `build_sheet` turns a run's
variants into a spreadsheet with one row per distinct respelling;
`summarize` reads the filled-in sheet and reports, per rule, the share of its
respellings that reviewers judged natural. That share is the rule's measured
precision, and it belongs in the paper.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Union

FIELDS = ["original", "variant", "rule", "times_generated", "natural", "note"]
_YES = {"y", "yes", "1", "true"}
_NO = {"n", "no", "0", "false"}


def build_sheet(variants_path: Union[str, Path], out_path: Union[str, Path]) -> int:
    """Write the review sheet; return the number of rows."""
    counts: Counter = Counter()
    with Path(variants_path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                for edit in json.loads(line)["edits"]:
                    counts[(edit["rule"], edit["from"], edit["to"])] += 1
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(FIELDS)
        for (rule, original, variant), n in sorted(counts.items()):
            writer.writerow([original, variant, rule, n, "", ""])
    return len(counts)


def summarize(sheet_path: Union[str, Path]) -> dict:
    """Per rule: rows reviewed, rows judged natural, rows still blank."""
    stats: dict = {}
    with Path(sheet_path).open(encoding="utf-8", newline="") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            entry = stats.setdefault(row["rule"], {"reviewed": 0, "natural": 0, "unreviewed": 0})
            answer = (row.get("natural") or "").strip().lower()
            if not answer:
                entry["unreviewed"] += 1
            elif answer in _YES:
                entry["reviewed"] += 1
                entry["natural"] += 1
            elif answer in _NO:
                entry["reviewed"] += 1
            else:
                raise ValueError(
                    f"{sheet_path}:{line_no}: 'natural' must be y or n, got {row['natural']!r}"
                )
    for entry in stats.values():
        entry["share_natural"] = entry["natural"] / entry["reviewed"] if entry["reviewed"] else None
    return stats
