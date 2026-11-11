from pathlib import Path

import pytest

from hijje.data import load_dataset

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


@pytest.fixture(scope="session")
def seed_dir() -> Path:
    return SEED_DIR


@pytest.fixture(scope="session")
def seed():
    return load_dataset(SEED_DIR)


@pytest.fixture()
def tiny_dir(tmp_path):
    """A four-document dataset small enough to reason about by hand."""
    (tmp_path / "corpus.jsonl").write_text(
        '{"_id": "d1", "text": "chai mein doodh daalne ka tareeqa"}\n'
        '{"_id": "d2", "text": "roti ka aata naram kaise banayein"}\n'
        '{"_id": "d3", "text": "mobile ki battery jaldi khatam hoti hai"}\n'
        '{"_id": "d4", "text": "imtihan ki tayyari ka theek tareeqa"}\n',
        encoding="utf-8",
    )
    (tmp_path / "queries.jsonl").write_text(
        '{"_id": "q1", "text": "chai mein doodh kaise daalein"}\n'
        '{"_id": "q2", "text": "roti naram kaise hoti hai"}\n'
        '{"_id": "q3", "text": "battery jaldi kyun khatam hoti hai"}\n',
        encoding="utf-8",
    )
    (tmp_path / "qrels.tsv").write_text(
        "query-id\tcorpus-id\tscore\nq1\td1\t1\nq2\td2\t1\nq3\td3\t1\n", encoding="utf-8"
    )
    (tmp_path / "protected_terms.txt").write_text("# loanwords\nmobile\nbattery\n", encoding="utf-8")
    return tmp_path
