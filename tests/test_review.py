import csv
import json
from pathlib import Path

import pytest

from hijje.cli import main
from hijje.review import FIELDS, build_sheet, summarize
from hijje.variation import LEXICON_RULE, RULES

DOCS = Path(__file__).resolve().parent.parent / "docs"


def _variants_file(tmp_path):
    rows = [
        {"edits": [{"from": "kya", "to": "kia", "rule": "lexicon"}, {"from": "baat", "to": "bat", "rule": "long_a"}]},
        {"edits": [{"from": "kya", "to": "kia", "rule": "lexicon"}]},
        {"edits": []},
    ]
    path = tmp_path / "variants.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def test_sheet_has_one_row_per_distinct_respelling(tmp_path):
    out = tmp_path / "sheet.csv"
    assert build_sheet(_variants_file(tmp_path), out) == 2
    with out.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0]) == FIELDS
    assert [(r["original"], r["variant"], r["rule"], r["times_generated"]) for r in rows] == [
        ("kya", "kia", "lexicon", "2"),
        ("baat", "bat", "long_a", "1"),
    ]
    assert all(r["natural"] == "" for r in rows)


def test_summarize_counts_answers_per_rule(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text(
        "original,variant,rule,times_generated,natural,note\n"
        "kya,kia,lexicon,2,y,\n"
        "hai,h,lexicon,1,N,rare\n"
        "aur,r,lexicon,1,,\n"
        "baat,bat,long_a,1,Yes,\n",
        encoding="utf-8",
    )
    stats = summarize(sheet)
    assert stats["lexicon"] == {"reviewed": 2, "natural": 1, "unreviewed": 1, "share_natural": 0.5}
    assert stats["long_a"]["share_natural"] == 1.0


def test_summarize_rejects_unclear_answers(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("original,variant,rule,times_generated,natural,note\nkya,kia,lexicon,2,maybe,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be y or n"):
        summarize(sheet)


def test_cli_review_round_trip(tmp_path, capsys):
    out = tmp_path / "r" / "sheet.csv"
    assert main(["review-sheet", "--variants", str(_variants_file(tmp_path)), "--out", str(out)]) == 0
    assert main(["review-stats", "--sheet", str(out)]) == 0
    assert "| lexicon | 0 | 0 | – | 1 |" in capsys.readouterr().out


def test_rules_command_and_rule_documentation_stay_in_sync(capsys):
    assert main(["rules"]) == 0
    printed = capsys.readouterr().out
    documented = (DOCS / "VARIATION_RULES.md").read_text(encoding="utf-8")
    for rule in RULES:
        assert f"`{rule.name}`" in printed
        assert f"`{rule.name}`" in documented, f"{rule.name} is missing from docs/VARIATION_RULES.md"
    assert f"`{LEXICON_RULE}`" in documented
