import random
from pathlib import Path

import pytest

from hijje.attested import load_attested
from hijje.attested_model import ATTESTED_RULE, AttestedVariation
from hijje.cli import make_model
from hijje.variation import VariationModel, derive_seed

FIXTURES = Path(__file__).resolve().parent / "fixtures"
LEXICON = str(FIXTURES / "lexicon_sample.tsv")


@pytest.fixture()
def model():
    table, _ = load_attested([LEXICON])
    return AttestedVariation(table)


def test_only_spellings_that_people_wrote_are_ever_produced(model):
    for seed in range(200):
        out = model.perturb("pani", rate=1.0, seed=seed)
        assert out.text in {"paani", "panee"}      # never "pani" itself, never an invented form
        assert out.edits[0].rule == ATTESTED_RULE


def test_the_more_people_wrote_a_spelling_the_more_often_it_is_chosen():
    model = AttestedVariation({"پانی": {"pani": 1, "paani": 9, "panee": 1}})
    # starting from "pani", the alternatives are paani (9) and panee (1)
    counts = {"paani": 0, "panee": 0}
    for seed in range(2000):
        counts[model.perturb("pani", rate=1.0, seed=seed).text] += 1
    assert 0.85 < counts["paani"] / 2000 < 0.95


def test_a_word_the_table_does_not_know_is_left_alone(model):
    out = model.perturb("zindagi pani", rate=1.0, seed=1)
    assert out.text.split()[0] == "zindagi"
    assert [e.original for e in out.edits] == ["pani"]


def test_a_text_with_nothing_changeable_comes_back_unchanged(model):
    out = model.perturb("zindagi hai", rate=1.0, seed=1)
    assert out.text == "zindagi hai" and out.edits == ()


def test_the_same_seed_gives_the_same_result(model):
    a = model.perturb("sawal pani theek", rate=0.7, seed=derive_seed(13, "q1", 0))
    b = model.perturb("sawal pani theek", rate=0.7, seed=derive_seed(13, "q1", 0))
    assert a == b


def test_golden_output_is_stable():
    """Fixed table + fixed seed -> fixed text. Fails if the sampling ever changes."""
    model = AttestedVariation({"پانی": {"pani": 3, "paani": 2, "panee": 1}, "سوال": {"sawal": 3, "saval": 1}})
    got = [model.perturb("pani sawal", rate=1.0, seed=s).text for s in range(6)]
    # By hand: with rate 1.0 two draws decide which words change, the third picks the
    # spelling of "pani": paani (weight 2) if draw*3 < 2, else panee (weight 1).
    expected = []
    for seed in range(6):
        rng = random.Random(seed)
        draws = [rng.random() for _ in range(4)]
        expected.append(("paani" if draws[2] * 3 < 2 else "panee") + " saval")
    assert got == expected
    assert got == ["paani saval", "panee saval", "paani saval", "paani saval", "paani saval", "panee saval"]


def test_punctuation_and_case_around_a_word_are_kept(model):
    out = model.perturb("(Pani)!", rate=1.0, seed=3)
    assert out.text.startswith("(") and out.text.endswith(")!")


def test_protected_words_are_never_changed():
    table, _ = load_attested([LEXICON])
    model = AttestedVariation(table, protect=["pani"])
    assert model.perturb("pani", rate=1.0, seed=1).text == "pani"


def test_a_spelling_shared_by_two_urdu_words_goes_to_the_one_with_more_weight():
    table = {"کا": {"ka": 50, "kaa": 5}, "کاہ": {"ka": 2, "kah": 4}}
    model = AttestedVariation(table)
    assert {c[0] for c in model.candidates("ka")} == {"kaa"}


def test_coverage_is_the_share_of_words_that_can_change(model):
    assert model.coverage("pani sawal zindagi hai") == pytest.approx(0.5)
    assert model.coverage("") == 0.0


def test_rate_zero_changes_nothing_and_a_bad_rate_is_refused(model):
    assert model.perturb("pani", rate=0.0, seed=1).text == "pani"
    with pytest.raises(ValueError):
        model.perturb("pani", rate=1.5)


def test_fallback_rules_handle_words_the_table_lacks():
    table, _ = load_attested([LEXICON])
    model = AttestedVariation(table, fallback=VariationModel())
    out = model.perturb("tareeqa", rate=1.0, seed=2)     # not in the table, but the rules know it
    assert out.edits and out.edits[0].rule != ATTESTED_RULE
    assert ATTESTED_RULE in model.rule_names()


def test_fallback_is_not_used_when_the_table_knows_the_word():
    table, _ = load_attested([LEXICON])
    model = AttestedVariation(table, fallback=VariationModel())
    assert {r for _, r, _ in model.candidates("pani")} == {ATTESTED_RULE}


def test_only_rules_can_restrict_to_the_attested_source(model):
    assert model.candidates("pani", only_rules=["long_a"]) == []
    assert model.candidates("pani", only_rules=[ATTESTED_RULE])


def test_make_model_builds_each_kind():
    assert isinstance(make_model("rules"), VariationModel)
    assert isinstance(make_model(f"attested:{LEXICON}"), AttestedVariation)
    both = make_model(f"attested+rules:{LEXICON}")
    assert both.fallback is not None


@pytest.mark.parametrize("spec", ["attested", "attested:", "nonsense", "attested:/no/such/file.tsv"])
def test_make_model_refuses_a_bad_spec(spec):
    with pytest.raises(ValueError):
        make_model(spec)
