from pathlib import Path

import pytest

from hijje import clean, confirm
from hijje.cli import main

FIX = Path(__file__).resolve().parent / "fixtures"
SENTENCES = str(FIX / "sentences_fixture.tsv")


def _answers(tmp_path):
    f = tmp_path / "a.csv"
    lines = ["writer,prompt,status,query"]
    # sentence 1 = "pani bohat thanda hai": three writers, one with different spellings
    for w, q in (("w1", "pani bohat thanda hai"), ("w2", "paani bohut thanda hai"), ("w3", "pani bohat thanday hai ji")):
        lines.append(f"{w},s00001,ok,{q}")
        for p, extra in (("s00002", "thanda pani piyen"), ("s00003", "sawal bohat mushkil tha"), ("s00004", "mushkil sawal hal karen")):
            lines.append(f"{w},{p},ok,{extra}")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(f)


def test_holm_correction():
    out = confirm.holm([0.01, 0.04, 0.03])
    assert [round(a, 3) for a, _ in out] == [0.03, 0.06, 0.06]
    assert [r for _, r in out] == [True, False, False]


def test_bootstrap_difference_and_relative_loss():
    a, b = [1.0, 1.0, 1.0, 1.0], [0.5, 0.5, 0.5, 0.5]
    d = confirm.boot_diff(a, b, n_boot=200)
    assert d["diff"] == 0.5 and d["lo"] == 0.5 and d["p"] == 0.0
    est, lo, hi = confirm.boot_relative_loss(a, b, n_boot=200)
    assert est == pytest.approx(0.5) and lo == hi == pytest.approx(0.5)


def test_conditions_use_the_volunteers_own_spelling(tmp_path):
    rows, _ = clean.clean_answers([_answers(tmp_path)], SENTENCES, min_answers=1)
    cond = confirm.build_conditions(rows, SENTENCES, min_writers=3)
    assert "s00001" in cond["primary"]
    spelled = {r["query"] for r in cond["b_rows"] if r["prompt"] == "s00001"}
    assert spelled == {"pani bohat thanda hai", "paani bohut thanda hai", "pani bohat thanday hai"}


def test_run_gives_a_clean_ceiling_and_the_tests(tmp_path):
    rows, _ = clean.clean_answers([_answers(tmp_path)], SENTENCES, min_answers=1)
    res = confirm.run(rows, SENTENCES, systems=("bm25", "bm25-l3", "bm25-l4"), min_writers=3, n_boot=100)
    assert res["systems"]["bm25"]["A"]["ndcg"] == 1.0
    assert set(res["tests"]) >= {"H1", "H2", "H3"}
    assert res["tests"]["H2"]["n"] == res["prompts"]


def test_cli_confirm_writes_summary(tmp_path):
    out = tmp_path / "o"
    assert main(["confirm", "--responses", _answers(tmp_path), "--src", SENTENCES, "--core", "",
                 "--systems", "bm25,bm25-l3,bm25-l4", "--min-answers", "1", "--min-writers", "3",
                 "--n-boot", "100", "--out", str(out)]) == 0
    assert "Planned tests" in (out / "summary.md").read_text(encoding="utf-8")
    assert (out / "results.json").exists()
