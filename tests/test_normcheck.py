import pytest

from hijje.cli import main
from hijje.normcheck import check, share_with_shared_key, to_markdown, unified_pairs

TABLE = {
    "کتنی": {"kitni": 2, "katni": 1},        # one word, two spellings
    "کتاب": {"kitab": 3},                    # another word
    "ٹھیک": {"theek": 2, "thik": 1, "tik": 1},
}


def test_unified_pairs_counts_each_pair_of_spellings_once():
    share, pairs = unified_pairs(TABLE, 0)
    assert pairs == 1 + 0 + 3 and share == 0.0     # nothing unified without normalisation
    share2, _ = unified_pairs(TABLE, 1)
    assert share2 == pytest.approx(1 / 4 * 1)      # only theek and thik join at level 1 (ee becomes i): 1 of 4 pairs


def test_level4_unifies_the_short_vowel_pair():
    share, pairs = unified_pairs({"کتنی": {"kitni": 2, "katni": 1}}, 4)
    assert (share, pairs) == (1.0, 1)


def test_a_word_sharing_a_key_with_another_word_is_counted():
    vocab = {"کم": {"kam": 1}, "کام": {"kaam": 1}, "کتاب": {"kitab": 1}}
    assert share_with_shared_key(vocab, vocab, 0) == 0.0
    assert share_with_shared_key(vocab, vocab, 1) == pytest.approx(2 / 3)   # kam and kaam merge at level 1


def test_check_reports_extra_collisions_over_level_0_and_a_split_never_seen_in_the_others():
    result = check({"a": {"کم": {"kam": 1}}, "b": {"کام": {"kaam": 1}}}, levels=(0, 1))
    assert result["levels"]["0"]["a"]["extra_shared_keys"] == 0.0
    assert result["levels"]["1"]["a"]["extra_shared_keys"] == 1.0    # kam now collides with a word from split b


def test_markdown_lists_every_level():
    text = to_markdown(check({"all": TABLE}))
    for name in ("none", "length", "phonetic", "skeleton", "vowelclass"):
        assert name in text


def test_cli_normcheck_runs_and_refuses_a_bad_split(tmp_path, capsys):
    f = tmp_path / "lex.tsv"
    f.write_text("کتنی\tkitni\t2\nکتنی\tkatni\t1\n", encoding="utf-8")
    assert main(["normcheck", "--split", f"all={f}", "--out", str(tmp_path / "o")]) == 0
    assert (tmp_path / "o" / "normcheck.md").exists()
    assert main(["normcheck", "--split", "nofile"]) == 2
