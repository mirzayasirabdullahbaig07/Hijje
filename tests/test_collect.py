import csv
import json
from pathlib import Path

import pytest

from hijje import collect
from hijje.cli import main
from hijje.data import load_dataset, validate

FIX = Path(__file__).resolve().parent / "fixtures"
SENTENCES = str(FIX / "sentences_fixture.tsv")     # six sentences: s00001 .. s00006
BROWSER_CSV = str(FIX / "browser_answers.csv")     # real output of the form, driven in headless Chromium


def write_responses(path, rows):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=collect.RESPONSE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({"status": "ok", "device": "phone", "province": "", "frequency": "", **row})


# -- prompts and form --------------------------------------------------------------

def test_prompt_ids_are_read_and_checked(tmp_path):
    f = tmp_path / "ids.txt"
    f.write_text("# comment\ns00001\n\ns00003\n", encoding="utf-8")
    assert collect.read_prompt_ids(f) == ["s00001", "s00003"]
    f.write_text("s00001\ns00001\n", encoding="utf-8")
    with pytest.raises(ValueError, match="twice"):
        collect.read_prompt_ids(f)
    f.write_text("s1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="s00042"):
        collect.read_prompt_ids(f)


def test_the_committed_prompt_list_is_valid_and_has_no_sentence_text():
    path = FIX.parent.parent / "data" / "real_queries" / "prompt_ids.txt"
    ids = collect.read_prompt_ids(path)
    assert len(ids) == 40
    assert not any(ord(ch) > 127 for ch in path.read_text(encoding="utf-8")), "CC BY-SA text must not be committed"


def test_the_form_carries_every_prompt_and_the_contact(tmp_path):
    out = tmp_path / "form.html"
    collect.make_form(SENTENCES, ["s00001", "s00005"], out, contact="faiqa@example.org")
    html = out.read_text(encoding="utf-8")
    assert "پانی بہت ٹھنڈا ہے" in html and "کتاب میز پر رکھیں" in html
    assert "faiqa@example.org" in html and "__PAYLOAD__" not in html


def test_a_sentence_cannot_break_out_of_the_form_script(tmp_path):
    f = tmp_path / "evil.tsv"
    f.write_text("ایک </script><script>alert(1)</script> جملہ\tek jumla\n", encoding="utf-8")
    out = tmp_path / "form.html"
    collect.make_form(str(f), ["s00001"], out)
    html = out.read_text(encoding="utf-8")
    assert html.count("</script>") == 2          # the two real ones: config block and code block
    assert "<script>alert" not in html


def test_a_prompt_outside_the_sentence_file_is_refused(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        collect.make_form(SENTENCES, ["s00099"], tmp_path / "f.html")


# -- responses ---------------------------------------------------------------------------

def test_the_file_written_by_the_real_form_is_read_correctly():
    rows, stats = collect.load_responses([BROWSER_CSV])
    assert stats["rows read"] == 40 and stats["rows kept"] == 39        # one sentence was skipped by the volunteer
    assert stats["dropped: skipped or empty"] == 1
    assert stats["writers"] == 1 and stats["prompts answered"] == 39
    assert any('"x"' in r["query"] and "," in r["query"] for r in rows)    # quotes and commas survive
    assert rows[0]["device"] == "phone" and rows[0]["province"] == "Punjab"


def test_bad_rows_are_dropped_and_each_reason_is_counted(tmp_path):
    f = tmp_path / "a.csv"
    write_responses(f, [
        {"writer": "w1", "prompt": "s00001", "query": "pani bohat thanda"},
        {"writer": "w1", "prompt": "s00002", "query": ""},
        {"writer": "w1", "prompt": "s00003", "query": "پانی ٹھنڈا"},
        {"writer": "w1", "prompt": "s00004", "query": "x" * 201},
        {"writer": "w1", "prompt": "bad", "query": "hello"},
        {"writer": "", "prompt": "s00005", "query": "hello"},
        {"writer": "w1", "prompt": "s00006", "status": "skip", "query": "ignored"},
    ])
    rows, stats = collect.load_responses([str(f)])
    assert [r["prompt"] for r in rows] == ["s00001"]
    assert stats["dropped: skipped or empty"] == 2
    assert stats["dropped: typed in Urdu script, not Roman"] == 1
    assert stats["dropped: longer than 200 characters"] == 1
    assert stats["dropped: bad writer or prompt code"] == 2


def test_a_second_answer_to_the_same_prompt_replaces_the_first(tmp_path):
    f = tmp_path / "a.csv"
    write_responses(f, [{"writer": "w1", "prompt": "s00001", "query": "first"},
                        {"writer": "w1", "prompt": "s00001", "query": "second"}])
    rows, _ = collect.load_responses([str(f)])
    assert [r["query"] for r in rows] == ["second"]


def test_a_file_without_the_required_columns_is_refused(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing column"):
        collect.load_responses([str(f)])


def test_writers_per_prompt_and_spelling_report(tmp_path):
    rows = [
        {"writer": "w1", "prompt": "s00001", "query": "pani thanda"},
        {"writer": "w2", "prompt": "s00001", "query": "paani thanda"},
        {"writer": "w3", "prompt": "s00001", "query": "pani thanda"},
        {"writer": "w1", "prompt": "s00002", "query": "kitab"},
    ]
    assert collect.writers_per_prompt(rows) == {"s00001": 3, "s00002": 1}
    rep = collect.spelling_report(rows)
    assert rep["queries"] == 4 and rep["distinct_queries"] == 3
    # pairs for s00001: (w1,w2) = 1/3, (w1,w3) = 1, (w2,w3) = 1/3
    assert rep["mean_word_overlap_between_writers"] == pytest.approx((1 / 3 + 1 + 1 / 3) / 3)


# -- collection, judging, evaluation ----------------------------------------------------

ROWS = [
    {"writer": "w1", "prompt": "s00003", "query": "bohat mushkil", "device": "", "province": "", "frequency": ""},
    {"writer": "w2", "prompt": "s00003", "query": "bohat mushkl", "device": "", "province": "", "frequency": ""},
    {"writer": "w1", "prompt": "s00005", "query": "kitab mez", "device": "", "province": "", "frequency": ""},
]


def test_build_real_makes_a_valid_collection(tmp_path):
    info = collect.build_real(ROWS, SENTENCES, tmp_path)
    ds = load_dataset(tmp_path)
    assert validate(ds) == []
    assert (info["queries"], info["writers"], info["prompts"]) == (3, 2, 2)
    assert len(ds.corpus) == 6
    assert ds.qrels["r0001"] == {"s00003": 2}
    owners = json.loads((tmp_path / "owners.json").read_text())
    assert owners["r0002"] == {"writer": "w2", "prompt": "s00003"}


def test_judgments_add_relevant_passages_but_never_change_the_source(tmp_path):
    judgments = {"s00003": {"s00004": 1, "s00001": 0, "s00003": 0}}     # a judge cannot demote the source
    collect.build_real(ROWS, SENTENCES, tmp_path, judgments)
    ds = load_dataset(tmp_path)
    assert ds.qrels["r0001"] == {"s00003": 2, "s00004": 1}
    assert ds.qrels["r0002"] == {"s00003": 2, "s00004": 1}             # shared by every writer of the prompt
    assert ds.qrels["r0003"] == {"s00005": 2}


def test_judge_sheet_pools_results_and_skips_the_source(tmp_path):
    data = tmp_path / "data"
    collect.build_real(ROWS, SENTENCES, data)
    ds = load_dataset(data)
    owners = json.loads((data / "owners.json").read_text())
    sheet = tmp_path / "judge.csv"
    n = collect.judge_sheet(ds, owners, SENTENCES, ["bm25"], sheet, depth=3)
    rows = list(csv.DictReader(sheet.open(encoding="utf-8-sig")))
    assert n == len(rows) > 0
    assert all(r["candidate"] != r["prompt"] for r in rows)
    assert all(r["grade"] == "" for r in rows)
    pairs = {(r["prompt"], r["candidate"]) for r in rows}
    assert ("s00003", "s00004") in pairs          # shares "mushkil" with the prompt's sentence


def test_filled_judge_sheet_is_read_and_a_bad_grade_is_refused(tmp_path):
    f = tmp_path / "j.csv"
    f.write_text("prompt,prompt_text,candidate,candidate_text,grade\ns00003,a,s00004,b,1\ns00003,a,s00001,c,\n", encoding="utf-8")
    assert collect.load_judgments(f) == {"s00003": {"s00004": 1}}
    f.write_text("prompt,prompt_text,candidate,candidate_text,grade\ns00003,a,s00004,b,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="grade must be"):
        collect.load_judgments(f)


def test_judgments_can_be_exported_without_any_sentence_text(tmp_path, capsys):
    sheet = tmp_path / "j.csv"
    sheet.write_text("prompt,prompt_text,candidate,candidate_text,grade\ns00003,جملہ,s00004,جملہ,1\ns00003,جملہ,s00001,جملہ,0\ns00005,جملہ,s00006,جملہ,\n", encoding="utf-8")
    out = tmp_path / "grades.csv"
    assert main(["judge-export", "--sheet", str(sheet), "--out", str(out)]) == 0
    assert out.read_text().splitlines() == ["prompt,candidate,grade", "s00003,s00001,0", "s00003,s00004,1"]
    assert collect.load_judgments(out) == {"s00003": {"s00001": 0, "s00004": 1}}   # the 3-column file loads too


def test_evaluate_real_scores_per_prompt_and_finds_the_unlucky_writer(tmp_path):
    collect.build_real(ROWS, SENTENCES, tmp_path)
    ds = load_dataset(tmp_path)
    owners = json.loads((tmp_path / "owners.json").read_text())
    res = collect.evaluate_real(ds, owners, ["bm25"], k=10, n_boot=50)
    r = res["retrievers"]["bm25"]
    assert (res["queries"], res["prompts"]) == (3, 2)
    # w1 finds s00003 first (both words match only it); w2's misspelt word matches nothing,
    # so s00003 ties with s00001 on "bohat" and ranks lower or equal.
    assert 0 < r["worst_writer_ndcg"] <= r["ndcg"] <= 1
    assert r["agreement"] is not None and 0 <= r["agreement"] <= 1


def test_a_spelling_that_matches_nothing_gives_zero_and_the_mean_is_hand_checkable(tmp_path):
    rows = [
        {"writer": "w1", "prompt": "s00005", "query": "kitab", "device": "", "province": "", "frequency": ""},
        {"writer": "w2", "prompt": "s00005", "query": "kitaab", "device": "", "province": "", "frequency": ""},
    ]
    collect.build_real(rows, SENTENCES, tmp_path)
    ds = load_dataset(tmp_path)
    owners = json.loads((tmp_path / "owners.json").read_text())
    r = collect.evaluate_real(ds, owners, ["bm25"], n_boot=50)["retrievers"]["bm25"]
    # "kitab" is in s00005 and s00006 and ranks the source first or second; "kitaab" matches nothing -> 0
    assert r["worst_writer_ndcg"] == 0.0
    assert r["ndcg"] > 0                           # w1 alone contributes
    r3 = collect.evaluate_real(ds, owners, ["bm25-l3"], n_boot=50)["retrievers"]["bm25-l3"]
    assert r3["worst_writer_ndcg"] > 0             # the vowel-dropping key joins kitab and kitaab


# -- command line, end to end -------------------------------------------------------------

def test_cli_runs_the_whole_kit_end_to_end(tmp_path, capsys):
    ids = tmp_path / "ids.txt"
    ids.write_text("s00001\ns00003\ns00005\n", encoding="utf-8")
    form = tmp_path / "form.html"
    assert main(["make-form", "--src", SENTENCES, "--prompts", str(ids), "--out", str(form), "--contact", "me"]) == 0
    answers = tmp_path / "a.csv"
    write_responses(answers, [
        {"writer": "w1", "prompt": "s00001", "query": "pani thanda"},
        {"writer": "w2", "prompt": "s00001", "query": "paani thanda"},
        {"writer": "w1", "prompt": "s00003", "query": "bohat mushkil"},
        {"writer": "w2", "prompt": "s00003", "query": "bohat mushkil"},
        {"writer": "w1", "prompt": "s00005", "query": "kitab mez"},
        {"writer": "w2", "prompt": "s00005", "query": "kitaab mez"},
    ])
    data = tmp_path / "data"
    assert main(["collect-build", "--responses", str(answers), "--src", SENTENCES, "--out", str(data)]) == 0
    assert "writers per prompt: min 2, max 2" in capsys.readouterr().out
    sheet = tmp_path / "judge.csv"
    assert main(["judge-sheet", "--data", str(data), "--src", SENTENCES, "--out", str(sheet), "--retrievers", "bm25,bm25-l4"]) == 0
    assert main(["real-eval", "--data", str(data), "--out", str(tmp_path / "res"), "--retrievers", "bm25,bm25-l4", "--n-boot", "50"]) == 0
    text = (tmp_path / "res" / "summary.md").read_text(encoding="utf-8")
    assert "| bm25 |" in text and "| bm25-l4 |" in text and "Worst writer" in text


def test_cli_refuses_clearly_when_there_is_nothing_to_use(tmp_path, capsys):
    empty = tmp_path / "e.csv"
    write_responses(empty, [{"writer": "w1", "prompt": "s00001", "query": ""}])
    assert main(["collect-build", "--responses", str(empty), "--src", SENTENCES, "--out", str(tmp_path / "d")]) == 1
    assert "no usable answers" in capsys.readouterr().err
    assert main(["real-eval", "--data", str(tmp_path)]) == 1
