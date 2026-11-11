import json

import pytest

from hijje.cli import main
from hijje.data import load_dataset
from hijje.evaluate import EvalConfig, condition_name, evaluate
from hijje.report import to_markdown

FAST = EvalConfig(rates=(0.5, 1.0), n_variants=3, n_boot=200, seed=7)


def test_result_structure_and_ranges(tiny_dir):
    ds = load_dataset(tiny_dir)
    result = evaluate(ds, ["bm25", "bm25-l2", "char"], FAST)
    assert result["meta"]["retrievers"] == ["bm25", "bm25-l2", "char"]
    assert result["meta"]["conditions"] == ["clean", "respelled_50", "respelled_100"]
    assert len(result["variants"]) == 3 * 2 * 3  # queries x rates x variants
    for name in result["meta"]["retrievers"]:
        clean = result["summary"][name]["clean"]
        assert 0.0 <= clean["ndcg"] <= 1.0
        assert clean["ndcg_ci"][0] <= clean["ndcg"] <= clean["ndcg_ci"][1]
        hard = result["summary"][name]["respelled_100"]
        assert hard["worst_ndcg"] <= hard["ndcg"] + 1e-12
        assert 0.0 <= hard["stability"] <= 1.0
        expected_drop = 100 * (clean["ndcg"] - hard["ndcg"]) / clean["ndcg"]
        assert hard["drop_pct"] == pytest.approx(expected_drop)
    assert set(result["comparisons"]) == {"bm25-l2", "char"}
    assert set(result["rule_impact"]) >= {"lexicon", "long_a", "vowel_drop"}
    json.dumps(result)  # must be serialisable


def test_evaluation_is_reproducible(tiny_dir):
    ds = load_dataset(tiny_dir)
    first = evaluate(ds, ["bm25", "fusion"], FAST)
    second = evaluate(ds, ["bm25", "fusion"], FAST)
    assert first == second


def test_a_different_seed_changes_the_variants(tiny_dir):
    ds = load_dataset(tiny_dir)
    a = evaluate(ds, ["bm25"], FAST, with_rule_impact=False)["variants"]
    b = evaluate(ds, ["bm25"], EvalConfig(rates=(0.5, 1.0), n_variants=3, n_boot=200, seed=8),
                 with_rule_impact=False)["variants"]
    assert [v["variant"] for v in a] != [v["variant"] for v in b]


def test_all_retrievers_see_identical_variants(tiny_dir):
    ds = load_dataset(tiny_dir)
    a = evaluate(ds, ["bm25"], FAST, with_rule_impact=False)["variants"]
    b = evaluate(ds, ["char", "bm25-l3"], FAST, with_rule_impact=False)["variants"]
    assert a == b


def test_protected_terms_are_respected_in_variants(tiny_dir):
    ds = load_dataset(tiny_dir)
    result = evaluate(ds, ["bm25"], FAST, with_rule_impact=False)
    for row in result["variants"]:
        if "battery" in row["original"].split():
            assert "battery" in row["variant"].split()
        assert all(e["from"] not in ds.protected for e in row["edits"])


def test_duplicate_or_missing_retrievers_raise(tiny_dir):
    ds = load_dataset(tiny_dir)
    with pytest.raises(ValueError):
        evaluate(ds, ["bm25", "bm25"], FAST)
    with pytest.raises(ValueError):
        evaluate(ds, [], FAST)


def test_condition_name():
    assert condition_name(0.5) == "respelled_50" and condition_name(1.0) == "respelled_100"


def test_seed_set_is_solvable_when_spelling_matches(seed):
    # Sanity check of the data, not a research result: if exact-match BM25
    # cannot solve the clean queries, the relevance labels are suspect.
    result = evaluate(seed, ["bm25"], EvalConfig(n_variants=1, n_boot=100), with_rule_impact=False)
    assert result["summary"]["bm25"]["clean"]["recall"] >= 0.95


def _reference(seed_dir):
    return seed_dir.parent.parent / "results" / "seed"


def test_reference_results_reproduce(seed, seed_dir):
    """The committed seed results must come out of the code as it is now.

    Only the pure-Python retrievers are compared exactly; the character
    n-gram retriever depends on the installed scikit-learn version.
    """
    reference = json.loads((_reference(seed_dir) / "results.json").read_text(encoding="utf-8"))
    cfg = reference["meta"]["config"]
    config = EvalConfig(k=cfg["k"], rates=tuple(cfg["rates"]), n_variants=cfg["n_variants"],
                        seed=cfg["seed"], max_edits=cfg["max_edits"], n_boot=cfg["n_boot"])
    names = ["bm25", "bm25-l1", "bm25-l2", "bm25-l3"]
    result = evaluate(seed, names, config, with_rule_impact=False)
    for name in names:
        for cond in reference["meta"]["conditions"]:
            for metric in ("ndcg", "recall", "mrr"):
                got = result["summary"][name][cond][metric]
                want = reference["summary"][name][cond][metric]
                assert got == pytest.approx(want, abs=1e-9), (name, cond, metric)


def test_readme_quotes_the_committed_results(seed_dir):
    """Every row of the robustness table in the README must match the saved run."""
    readme = (seed_dir.parent.parent / "README.md").read_text(encoding="utf-8")
    summary = (_reference(seed_dir) / "summary.md").read_text(encoding="utf-8")
    table = summary.split("## Robustness")[1].split("## Recall")[0]
    rows = [line for line in table.splitlines() if line.startswith("| ") and "Retriever" not in line]
    assert len(rows) == 6
    for row in rows:
        assert row in readme, f"README is out of date for: {row}"


def test_report_contains_every_retriever_and_rule(tiny_dir):
    ds = load_dataset(tiny_dir)
    result = evaluate(ds, ["bm25", "char"], FAST)
    text = to_markdown(result)
    assert "| bm25 |" in text and "| char |" in text
    assert "Which kind of respelling hurts" in text and "vowel_drop" in text
    assert "Difference from `bm25`" in text


def test_cli_eval_writes_all_outputs(seed_dir, tmp_path, capsys):
    out = tmp_path / "run"
    code = main(["eval", "--data", str(seed_dir), "--out", str(out), "--retrievers", "bm25,bm25-l2",
                 "--n-variants", "2", "--n-boot", "100"])
    assert code == 0
    assert (out / "summary.md").read_text(encoding="utf-8").startswith("# Hijje evaluation: seed")
    saved = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert saved["meta"]["queries_evaluated"] == 48
    assert len((out / "variants.jsonl").read_text(encoding="utf-8").splitlines()) == 48 * 2 * 2
    assert "Robustness" in capsys.readouterr().out


def test_cli_small_commands(seed_dir, capsys):
    assert main(["validate", "--data", str(seed_dir)]) == 0
    assert "no problems found" in capsys.readouterr().out
    assert main(["normalize", "kya kia kiya", "--level", "2"]) == 0
    assert "kia kia kia" in capsys.readouterr().out
    assert main(["variants", "mujhe nahi pata", "--n", "2"]) == 0
    assert "variant 2" in capsys.readouterr().out
    assert main(["collisions", "--data", str(seed_dir), "--top", "3"]) == 0
    assert "merged groups" in capsys.readouterr().out


def test_cli_reports_bad_retriever_names_without_a_traceback(seed_dir, tmp_path, capsys):
    assert main(["eval", "--data", str(seed_dir), "--out", str(tmp_path / "o"), "--retrievers", "bm42"]) == 2
    assert "unknown retriever spec" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_cli_refuses_a_broken_dataset(tmp_path, capsys):
    (tmp_path / "corpus.jsonl").write_text('{"_id": "d1", "text": "chai"}\n', encoding="utf-8")
    (tmp_path / "queries.jsonl").write_text('{"_id": "q1", "text": "chai"}\n', encoding="utf-8")
    (tmp_path / "qrels.tsv").write_text("q1\td9\t1\n", encoding="utf-8")
    assert main(["eval", "--data", str(tmp_path), "--out", str(tmp_path / "o")]) == 1
    assert main(["validate", "--data", str(tmp_path)]) == 1
