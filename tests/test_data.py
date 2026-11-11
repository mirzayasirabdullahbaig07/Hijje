import pytest

from hijje.data import load_dataset, validate
from hijje.variation import VariationModel


def test_seed_dataset_is_valid(seed):
    assert validate(seed) == []
    assert seed.stats() == {
        "name": "seed",
        "documents": 48,
        "queries": 48,
        "relevance_judgements": 51,
        "protected_terms": 72,
    }


def test_seed_queries_are_lowercase_single_line(seed):
    # Variants are produced in lowercase; clean queries must be lowercase too,
    # otherwise letter case would be a hidden second difference.
    for qid, text in seed.queries.items():
        assert text == text.lower() and "\n" not in text, qid


def test_every_seed_query_can_be_respelled(seed):
    model = VariationModel(protect=seed.protected)
    for qid, text in seed.queries.items():
        assert model.perturb(text, rate=1.0, seed=1).edits, qid


def test_protected_terms_are_loaded_without_comments(seed):
    assert "mobile" in seed.protected
    assert not any(term.startswith("#") or term != term.lower() for term in seed.protected)


def test_loader_reads_tiny_dataset(tiny_dir):
    ds = load_dataset(tiny_dir)
    assert len(ds.corpus) == 4 and len(ds.queries) == 3
    assert ds.qrels["q1"] == {"d1": 1}
    assert ds.protected == frozenset({"mobile", "battery"})
    assert validate(ds) == []


def test_loader_accepts_beir_layout_and_titles(tmp_path):
    (tmp_path / "qrels").mkdir()
    (tmp_path / "corpus.jsonl").write_text('{"_id": 1, "title": "Chai", "text": "doodh patti"}\n', encoding="utf-8")
    (tmp_path / "queries.jsonl").write_text('{"_id": "q1", "text": "chai"}\n', encoding="utf-8")
    (tmp_path / "qrels" / "test.tsv").write_text("query-id\tcorpus-id\tscore\nq1\t1\t1\n", encoding="utf-8")
    ds = load_dataset(tmp_path)
    assert ds.corpus == {"1": "Chai doodh patti"}
    assert ds.qrels == {"q1": {"1": 1}}
    assert validate(ds) == []


def test_duplicate_ids_are_rejected(tmp_path):
    (tmp_path / "corpus.jsonl").write_text('{"_id": "d1", "text": "a"}\n{"_id": "d1", "text": "b"}\n', encoding="utf-8")
    (tmp_path / "queries.jsonl").write_text('{"_id": "q1", "text": "a"}\n', encoding="utf-8")
    (tmp_path / "qrels.tsv").write_text("q1\td1\t1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_dataset(tmp_path)


def test_validate_reports_broken_references(tmp_path):
    (tmp_path / "corpus.jsonl").write_text('{"_id": "d1", "text": "chai"}\n', encoding="utf-8")
    (tmp_path / "queries.jsonl").write_text(
        '{"_id": "q1", "text": "chai"}\n{"_id": "q2", "text": "roti"}\n', encoding="utf-8"
    )
    (tmp_path / "qrels.tsv").write_text("q1\td9\t1\nq7\td1\t1\n", encoding="utf-8")
    problems = validate(load_dataset(tmp_path))
    assert any("unknown document d9" in p for p in problems)
    assert any("unknown query q7" in p for p in problems)
    assert any("query q2 has no relevant document" in p for p in problems)


def test_missing_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "nope")
