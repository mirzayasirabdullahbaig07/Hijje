import pytest

from hijje.normalize import LEVELS, analyze, normalize_text, normalize_word
from hijje.text import tokenize
from hijje.variation import VariationModel

# Spellings of one word that must share a key from the given level upward.
SAME_FROM_L1 = [
    ("kaam", "kam"),
    ("achha", "acha"),
    ("theek", "thik"),
    ("poora", "pura"),
    ("yaaar", "yaar", "yar"),
]
SAME_FROM_L2 = [
    ("kya", "kia", "kiya"),
    ("mujhe", "mujhy", "mujhay", "muje"),
    ("nahi", "nahin", "nahee"),
    ("aur", "or"),
    ("kaise", "kese", "kesay", "kaisay"),
    ("yeh", "ye"),
    ("phir", "fir"),
    ("waqt", "wakt", "vaqt"),
    ("ke", "kay", "ky"),
    ("zyada", "ziada", "ziyada"),
    ("yahan", "yaha"),
    ("liye", "liay", "lie", "liyay"),
]
SAME_FROM_L3 = [
    ("karna", "krna"),
    ("bohat", "boht", "bht", "bahut"),
    ("kuch", "kch", "kuchh"),
    ("theek", "thik", "thk", "tik", "teek"),
    ("mujhe", "mjhe"),
    ("tum", "tm"),
    ("hum", "hm", "ham"),
]


def _keys(group, level):
    return {normalize_word(w, level) for w in group}


@pytest.mark.parametrize("group", SAME_FROM_L1)
def test_level1_merges_length_variants(group):
    assert len(_keys(group, 0)) == len(set(group))  # level 0 keeps them apart
    for level in (1, 2, 3):
        assert len(_keys(group, level)) == 1, (group, level)


@pytest.mark.parametrize("group", SAME_FROM_L2)
def test_level2_merges_phonetic_variants(group):
    for level in (2, 3):
        assert len(_keys(group, level)) == 1, (group, level)


@pytest.mark.parametrize("group", SAME_FROM_L3)
def test_level3_merges_vowel_dropped_variants(group):
    assert len(_keys(group, 3)) == 1, group


def test_vowel_dropping_is_not_solved_before_level3():
    # This is what separates level 3 from level 2; if it changes, the README is wrong.
    assert normalize_word("karna", 2) != normalize_word("krna", 2)


def test_different_words_stay_apart_at_level2():
    for a, b in [("chai", "chawal"), ("pani", "paisa"), ("roti", "raat"), ("mobile", "mazboot")]:
        assert normalize_word(a, 2) != normalize_word(b, 2)


def test_known_false_merge_is_documented_behaviour():
    # "kaam" (work) and "kam" (less) are different words that level 1 merges.
    # The test pins the cost of normalisation so nobody forgets it exists.
    assert normalize_word("kaam", 1) == normalize_word("kam", 1)


def test_level0_only_lowercases():
    assert normalize_word("Theek", 0) == "theek"


def test_non_roman_tokens_pass_through():
    for token in ["t20", "2026", "کیا", "5g"]:
        for level in LEVELS:
            assert normalize_word(token, level) == token


def test_invalid_level_raises():
    with pytest.raises(ValueError):
        normalize_word("kya", 4)


def test_analyze_and_normalize_text():
    assert analyze("Kya, kiya?", 2) == ["kia", "kia"]
    assert normalize_text("Mujhe NAHIN pata", 2) == "muji nahi pata"


def _vocabulary(seed):
    words = set()
    for text in list(seed.corpus.values()) + list(seed.queries.values()):
        words.update(t for t in tokenize(text) if t.isalpha())
    model = VariationModel()
    for w in list(words):
        words.update(v for v, _, _ in model.candidates(w))
    return sorted(words)


def test_idempotent_on_real_vocabulary_and_its_variants(seed):
    for word in _vocabulary(seed):
        for level in LEVELS:
            once = normalize_word(word, level)
            assert normalize_word(once, level) == once, (word, level, once)


def test_stronger_levels_never_split_what_weaker_levels_merged(seed):
    vocab = _vocabulary(seed)
    for lower, higher in [(1, 2), (2, 3)]:
        key_at_higher = {}
        for word in vocab:
            low_key = normalize_word(word, lower)
            high_key = normalize_word(word, higher)
            assert key_at_higher.setdefault(low_key, high_key) == high_key, (word, lower, higher)
