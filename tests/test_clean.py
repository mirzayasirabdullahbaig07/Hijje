from pathlib import Path

import pytest

from hijje import clean
from hijje.cli import main

FIX = Path(__file__).resolve().parent / "fixtures"
SENTENCES = str(FIX / "sentences_fixture.tsv")


def test_alignment_tolerates_different_spellings_and_keeps_word_order():
    q = ["pani", "bohut", "thanda", "hay"]
    p = ["pani", "bohat", "thanda", "hai"]
    assert clean.align(q, p) == [(0, 0), (1, 1), (2, 2)]          # "hay"/"hai" is below the 0.7 similarity
    assert clean.align(["thanda", "pani"], ["pani", "thanda"]) in ([(0, 1)], [(1, 0)])   # never crossing


@pytest.mark.parametrize("query,style", [
    ("pani bohut thanda hai", "transliteration"),
    ("thanda pani", "keywords"),
    ("yes", "unrelated"),
    ("kia haal hai", "unrelated"),
    ("pani bohat thanda hai aur yeh bohat lambi baat hai jo bahut der tak chalti rahi", "other"),
])
def test_answer_types(query, style):
    assert clean.classify(query, "pani bohat thanda hai")["style"] == style


def test_yes_does_not_match_a_short_word():
    assert clean.classify("yes", "ye bohat achi baat hai")["style"] == "unrelated"


def test_clean_answers_applies_the_plan_then_the_type_check(tmp_path):
    f = tmp_path / "a.csv"
    lines = ["writer,prompt,status,query,device"]
    lines += ["w1,s00001,ok,pani bohat thanda hai,phone", "w1,s00002,ok,thanda pani piyen,phone",
              "w1,s00003,ok,yes,phone", "w1,s00004,skip,,phone", "w1,s00005,ok,kitab mez par rakhen,phone"]
    lines += ["w2,s00001,ok,pani thanda,phone"]                     # only one answer: writer dropped
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rows, stats = clean.clean_answers([str(f)], SENTENCES, min_answers=3)
    assert [r["prompt"] for r in rows] == ["s00001", "s00002", "s00005"]
    assert stats["dropped: skipped or empty"] == 1
    assert stats["dropped: unrelated to the sentence"] == 1
    assert stats["dropped: writers with fewer than 3 usable answers"] == 1
    kept, _ = clean.clean_answers([str(f)], SENTENCES, min_answers=3, keep_unrelated=True)
    assert len(kept) == 4


def test_the_volunteers_spelling_of_the_constructed_words():
    assert clean.volunteer_spelling_of(["bohat", "thanda"], "pani bohut thanday hai", "pani bohat thanda hai") == ["bohut", "thanday"]
    assert clean.volunteer_spelling_of(["bohat", "kitab"], "pani bohut thanday hai", "pani bohat thanda hai") is None      # word not in passage
    assert clean.volunteer_spelling_of(["bohat", "thanda"], "pani hai", "pani bohat thanda hai") is None                    # word not written


def test_cli_writes_cleaned_csv_and_report(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("writer,prompt,status,query\n" + "\n".join(f"w1,s0000{i},ok,{q}" for i, q in
                 enumerate(["pani bohat thanda hai", "thanda pani piyen", "sawal bohat mushkil tha", "x"], 1)) + "\n", encoding="utf-8")
    out, rep = tmp_path / "c" / "clean.csv", tmp_path / "c" / "r.md"
    assert main(["clean-answers", "--responses", str(f), "--src", SENTENCES, "--out", str(out), "--report", str(rep), "--min-answers", "3"]) == 0
    assert "style" in out.read_text(encoding="utf-8-sig").splitlines()[0]
    assert "transliteration" in rep.read_text(encoding="utf-8")


def test_the_researchers_own_test_answers_can_be_excluded(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("writer,prompt,status,query\nme,s00001,ok,pani bohat thanda hai\nyou,s00001,ok,pani bohut thanda hai\n", encoding="utf-8")
    rows, stats = clean.clean_answers([str(f)], SENTENCES, min_answers=1, exclude_writers=["me"])
    assert [r["writer"] for r in rows] == ["you"] and stats["dropped: the researcher's own test answers"] == 1
