import json
from pathlib import Path

import pytest

from hijje.cli import main
from hijje.dakshina import build_collection, read_sentences
from hijje.data import load_dataset, validate

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "sentences_fixture.tsv"


def test_sentences_are_read_in_file_order():
    s = read_sentences(SAMPLE)
    assert len(s) == 6 and s[0] == "pani bohat thanda hai"


def test_a_collection_is_built_and_passes_validation(tmp_path):
    info = build_collection(SAMPLE, tmp_path, n_queries=10, query_len=2)
    ds = load_dataset(tmp_path)
    assert validate(ds) == []
    assert info["sentences"] == 6 == len(ds.corpus)
    assert info["queries"] == len(ds.queries) > 0


def test_every_query_points_back_to_the_sentence_it_came_from(tmp_path):
    build_collection(SAMPLE, tmp_path, n_queries=10, query_len=2)
    ds = load_dataset(tmp_path)
    for qid, text in ds.queries.items():
        best = max(ds.qrels[qid], key=ds.qrels[qid].get)
        assert ds.qrels[qid][best] == 2
        assert set(text.split()) <= set(ds.corpus[best].lower().replace(".", "").split())


def test_a_second_sentence_with_all_the_words_gets_grade_one(tmp_path):
    build_collection(SAMPLE, tmp_path, n_queries=10, query_len=2)
    ds = load_dataset(tmp_path)
    grades = [g for q in ds.qrels.values() for g in q.values()]
    assert 1 in grades and 2 in grades


def test_the_same_seed_builds_the_same_collection(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    build_collection(SAMPLE, a, n_queries=3, query_len=2, seed=5)
    build_collection(SAMPLE, b, n_queries=3, query_len=2, seed=5)
    for name in ("corpus.jsonl", "queries.jsonl", "qrels.tsv"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_a_different_seed_can_pick_different_queries(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    build_collection(SAMPLE, a, n_queries=2, query_len=2, seed=1)
    build_collection(SAMPLE, b, n_queries=2, query_len=2, seed=2)
    assert (a / "queries.jsonl").read_text() != (b / "queries.jsonl").read_text()


def test_a_missing_file_gives_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="romanized"):
        build_collection(tmp_path, tmp_path / "out")


def test_cli_builds_and_reports_the_licence(tmp_path, capsys):
    code = main(["build-dakshina", "--src", str(SAMPLE), "--out", str(tmp_path), "--n-queries", "3", "--query-len", "2"])
    assert code == 0
    assert "CC BY-SA" in capsys.readouterr().out
    assert json.loads((tmp_path / "build_info.json").read_text())["queries"] > 0


def test_cli_eval_runs_end_to_end_with_human_spellings(tmp_path, capsys):
    data = tmp_path / "data"
    build_collection(SAMPLE, data, n_queries=4, query_len=2)
    lex = Path(__file__).resolve().parent / "fixtures" / "lexicon_sample.tsv"
    code = main(["eval", "--data", str(data), "--variation", f"attested:{lex}", "--retrievers", "bm25,bm25-l3",
                 "--out", str(tmp_path / "res"), "--n-boot", "50", "--n-variants", "2"])
    assert code == 0
    result = json.loads((tmp_path / "res" / "results.json").read_text(encoding="utf-8"))
    assert result["meta"]["variation"] == "attested"
    assert "only with spellings that people wrote" in (tmp_path / "res" / "summary.md").read_text(encoding="utf-8")


# --- Reference run on the real Dakshina files --------------------------------
# These need the Dakshina Urdu files (CC BY-SA 4.0, about 5 MB for Urdu), which are not in
# this repository. Set HIJJE_DAKSHINA_DIR to the folder that contains 'lexicons' and
# 'romanized' to run them; otherwise they are skipped.

import os

DAKSHINA = os.environ.get("HIJJE_DAKSHINA_DIR")
needs_dakshina = pytest.mark.skipif(not DAKSHINA, reason="set HIJJE_DAKSHINA_DIR to run")
RESULTS = Path(__file__).resolve().parent.parent / "results"


@needs_dakshina
@pytest.mark.parametrize("variation", ["human", "rules", "human_plus_rules"])
def test_dakshina_reference_results_reproduce(tmp_path, variation):
    from hijje.cli import make_model
    from hijje.evaluate import EvalConfig, evaluate

    build_collection(DAKSHINA, tmp_path / "data", n_queries=1000)
    ds = load_dataset(tmp_path / "data")
    lexicon = str(Path(DAKSHINA) / "lexicons" / "ur.translit.sampled.train.tsv")
    spec = {"human": f"attested:{lexicon}", "rules": "rules", "human_plus_rules": f"attested+rules:{lexicon}"}[variation]
    reference = json.loads((RESULTS / f"dakshina_ur_{variation}" / "results.json").read_text(encoding="utf-8"))
    cfg = reference["meta"]["config"]
    config = EvalConfig(k=cfg["k"], rates=tuple(cfg["rates"]), n_variants=cfg["n_variants"],
                        seed=cfg["seed"], max_edits=cfg["max_edits"], n_boot=cfg["n_boot"])
    names = ["bm25", "bm25-l2", "bm25-l3"]
    result = evaluate(ds, names, config, model=make_model(spec, ds.protected), with_rule_impact=False)
    for name in names:
        for cond in reference["meta"]["conditions"]:
            for metric in ("ndcg", "recall", "mrr"):
                assert result["summary"][name][cond][metric] == pytest.approx(
                    reference["summary"][name][cond][metric], abs=1e-9), (name, cond, metric)


def test_committed_dakshina_summaries_are_present_and_name_their_method():
    for variation, phrase in {
        "human": "only with spellings that people wrote",
        "human_plus_rules": "hand-written rules were used",
    }.items():
        text = (RESULTS / f"dakshina_ur_{variation}" / "summary.md").read_text(encoding="utf-8")
        assert phrase in text


def test_readme_dakshina_table_matches_the_saved_run():
    """The five rows of the Dakshina table in the README must come from the committed results."""
    readme = (RESULTS.parent / "README.md").read_text(encoding="utf-8")
    result = json.loads((RESULTS / "dakshina_ur_human" / "results.json").read_text(encoding="utf-8"))
    for name in result["meta"]["retrievers"]:
        s = result["summary"][name]
        row = (f"| {name} | {s['clean']['ndcg']:.3f} | {s['respelled_50']['ndcg']:.3f} | "
               f"{s['respelled_50']['drop_pct']:.1f}% | {s['respelled_100']['ndcg']:.3f} | "
               f"{s['respelled_100']['drop_pct']:.1f}% |")
        assert row in readme, f"README is out of date for: {row}"


def test_readme_generator_comparison_matches_the_saved_runs():
    readme = (RESULTS.parent / "README.md").read_text(encoding="utf-8")
    for variation in ("human", "rules", "human_plus_rules"):
        result = json.loads((RESULTS / f"dakshina_ur_{variation}" / "results.json").read_text(encoding="utf-8"))
        cells = [f"{result['summary'][n]['respelled_100']['drop_pct']:.1f}%" for n in result["meta"]["retrievers"]]
        assert " | ".join(cells) in readme, (variation, cells)


def _md_rows(path):
    text = path.read_text(encoding="utf-8").split("## Robustness")[1].split("## Recall")[0]
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].startswith("bm25"):
            rows[cells[0]] = (cells[1], cells[5])    # clean, 100% respelled
    return rows


def test_readme_query_length_table_matches_the_saved_runs():
    readme = (RESULTS.parent / "README.md").read_text(encoding="utf-8")
    sources = {
        2: RESULTS / "dakshina_ur_sensitivity" / "len2_seed13_human.md",
        3: RESULTS / "dakshina_ur_sensitivity" / "len3_seed13_human.md",
        4: RESULTS / "dakshina_ur_levels_human" / "summary.md",
        6: RESULTS / "dakshina_ur_sensitivity" / "len6_seed13_human.md",
    }
    for words, path in sources.items():
        rows = _md_rows(path)
        cells = " | ".join(f"{rows[n][0]} / {rows[n][1]}" for n in ("bm25", "bm25-l2", "bm25-l3", "bm25-l4"))
        assert f"| {words} words | {cells} |" in readme, f"README is out of date for {words}-word queries"


def test_readme_normcheck_table_matches_the_saved_report():
    readme = (RESULTS.parent / "README.md").read_text(encoding="utf-8")
    report = (RESULTS / "normcheck" / "normcheck.md").read_text(encoding="utf-8")
    checked = 0
    for line in report.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0][:1] in "1234" and len(cells) == 7 and cells[0][1:2] == " ":
            level = cells[0]
            row = f"| {level} | {cells[3]} | {cells[6].replace(' pts', ' pts')} |"
            assert row in readme, f"README is out of date for: {row}"
            checked += 1
    assert checked == 4


@needs_dakshina
@pytest.mark.parametrize("variation", ["human", "rules"])
def test_level4_reference_results_reproduce(tmp_path, variation):
    from hijje.cli import make_model
    from hijje.evaluate import EvalConfig, evaluate

    build_collection(DAKSHINA, tmp_path / "data", n_queries=1000)
    ds = load_dataset(tmp_path / "data")
    lexicon = str(Path(DAKSHINA) / "lexicons" / "ur.translit.sampled.train.tsv")
    spec = f"attested:{lexicon}" if variation == "human" else "rules"
    reference = json.loads((RESULTS / f"dakshina_ur_levels_{variation}" / "results.json").read_text(encoding="utf-8"))
    cfg = reference["meta"]["config"]
    config = EvalConfig(k=cfg["k"], rates=tuple(cfg["rates"]), n_variants=cfg["n_variants"],
                        seed=cfg["seed"], max_edits=cfg["max_edits"], n_boot=cfg["n_boot"])
    result = evaluate(ds, ["bm25-l4"], config, model=make_model(spec, ds.protected), with_rule_impact=False)
    for cond in reference["meta"]["conditions"]:
        assert result["summary"]["bm25-l4"][cond]["ndcg"] == pytest.approx(
            reference["summary"]["bm25-l4"][cond]["ndcg"], abs=1e-9), cond


@needs_dakshina
def test_normcheck_report_reproduces():
    from hijje.attested import load_attested
    from hijje.normcheck import check, to_markdown

    lex = Path(DAKSHINA) / "lexicons"
    splits = {n: load_attested([str(lex / f"ur.translit.sampled.{n}.tsv")])[0] for n in ("train", "dev", "test")}
    assert to_markdown(check(splits)) == (RESULTS / "normcheck" / "normcheck.md").read_text(encoding="utf-8")
