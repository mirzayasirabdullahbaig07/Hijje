import pytest

from hijje.variation import LEXICON, RULES, VariationModel, derive_seed

TEXT = "mobile ka waqt theek nahi hai aur mujhe kaam karna hai"


def test_derive_seed_is_stable_across_runs_and_machines():
    # Python's hash() would give a new number every run; this must not.
    assert derive_seed("hijje", 13, 0.5) == 13712662521681240568


def test_every_rule_produces_its_documented_example():
    for rule in RULES:
        source, target = rule.example
        assert target in rule.apply(source), rule.name


def test_native_review_round1_decisions_hold():
    """Respellings rejected by a native reviewer must never be generated again."""
    model = VariationModel()

    def variants(word):
        return {v for v, _, _ in model.candidates(word)}

    # a final -i is written "i", not "y" ...
    for word in ["pani", "roti", "kitni", "jaldi", "achi", "nahi"]:
        assert word[:-1] + "y" not in variants(word), word
    # ... while a final -e may still be written "y" or "ay"
    assert {"bachy", "bachay"} <= variants("bache")
    # people write "w", not "v"
    for word in ["chawal", "sawal", "waqt", "woh", "wale"]:
        assert not any("v" in v for v in variants(word)), word
    # single words
    assert "pni" not in variants("pani")
    assert {"teek", "tik"}.isdisjoint(variants("theek"))
    assert {"theak", "thk"} <= variants("theek")
    assert "treeqa" not in variants("tareeqa")
    # rules removed as a result
    assert {"w_v", "aspirate_h"}.isdisjoint(model.rule_names())
    # the natural h-dropping cases are still covered by the word list
    assert "muje" in variants("mujhe") and "bi" in variants("bhi")


def test_rule_names_are_unique():
    names = [r.name for r in RULES]
    assert len(names) == len(set(names))


def test_same_seed_gives_same_text():
    model = VariationModel()
    assert model.perturb(TEXT, rate=0.7, seed=5) == model.perturb(TEXT, rate=0.7, seed=5)


def test_different_seeds_give_different_texts():
    model = VariationModel()
    outputs = {model.perturb(TEXT, rate=0.7, seed=s).text for s in range(20)}
    assert len(outputs) > 5


def test_golden_output_guards_reproducibility():
    # If this fails, published numbers are no longer reproducible with the
    # same seed. Change it only together with a version bump.
    model = VariationModel(protect={"mobile"})
    result = model.perturb(TEXT, rate=0.7, seed=2024)
    assert result.text == "mobile ka wqt theek nhi hai aor mujhe kam krna hai"
    assert [(e.original, e.variant, e.rule) for e in result.edits] == [
        ("waqt", "wqt", "lexicon"),
        ("nahi", "nhi", "lexicon"),
        ("aur", "aor", "lexicon"),
        ("kaam", "kam", "long_a"),
        ("karna", "krna", "lexicon"),
    ]


def test_protected_words_are_never_changed():
    model = VariationModel(protect={"Mobile", "waqt"})
    for s in range(30):
        tokens = model.perturb(TEXT, rate=1.0, seed=s).text.split()
        assert tokens[0] == "mobile" and tokens[2] == "waqt"


def test_edits_describe_exactly_what_changed():
    model = VariationModel()
    result = model.perturb(TEXT, rate=0.8, seed=3)
    original, changed = TEXT.split(), result.text.split()
    assert len(original) == len(changed)
    edited = {e.position: e for e in result.edits}
    for i, (a, b) in enumerate(zip(original, changed)):
        if i in edited:
            assert (edited[i].original, edited[i].variant) == (a, b) and a != b
        else:
            assert a == b


def test_rate_zero_changes_nothing_and_tiny_rate_changes_something():
    model = VariationModel()
    assert model.perturb(TEXT, rate=0.0, seed=1).text == TEXT
    assert model.perturb(TEXT, rate=1e-9, seed=1).edits  # ensure_change
    assert not model.perturb(TEXT, rate=1e-9, seed=1, ensure_change=False).edits


def test_rate_out_of_range_raises():
    with pytest.raises(ValueError):
        VariationModel().perturb(TEXT, rate=1.5)


def test_candidates_are_alphabetic_and_never_the_word_itself():
    model = VariationModel()
    for word in list(LEXICON) + ["baat", "poora", "achha", "jagah", "waqt", "karna", "dukan"]:
        for variant, rule, weight in model.candidates(word):
            assert variant != word and variant.isalpha() and weight > 0, (word, variant, rule)


def test_only_rules_restricts_the_edits():
    model = VariationModel()
    result = model.perturb("baat kaam saath naam", rate=1.0, seed=1, only_rules=["long_a"])
    assert result.text == "bat kam sath nam"
    assert {e.rule for e in result.edits} == {"long_a"}


def test_punctuation_and_untouched_words_survive():
    model = VariationModel()
    result = model.perturb("Kya, yeh theek hai?", rate=1.0, seed=7)
    tokens = result.text.split()
    assert tokens[0].endswith(",") and tokens[-1].endswith("?")
    assert len(tokens) == 4


def test_numbers_and_urdu_script_are_left_alone():
    model = VariationModel()
    assert model.perturb("t20 2026 کیا", rate=1.0, seed=1).text == "t20 2026 کیا"


def test_stacked_edits_are_recorded():
    model = VariationModel()
    result = model.perturb("mujhe", rate=1.0, seed=4, max_edits=2)
    for edit in result.edits:
        assert edit.variant != edit.original
        assert 1 <= len(edit.rule.split("+")) <= 2
