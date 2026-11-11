import numpy as np
import pytest

from hijje.retrievers import BM25, RRF, CharNgramTfidf, DenseRetriever, build_retriever

IDS = ["d1", "d2", "d3"]
DOCS = ["chai mein doodh", "roti aur daal", "chai chai patti"]


def ids(ranking):
    return [doc_id for doc_id, _ in ranking]


def test_bm25_prefers_higher_term_frequency_and_skips_non_matches():
    r = BM25()
    r.index(IDS, DOCS)
    assert ids(r.search("chai")) == ["d3", "d1"]


def test_bm25_unknown_term_returns_nothing():
    r = BM25()
    r.index(IDS, DOCS)
    assert r.search("biryani") == []


def test_bm25_idf_is_never_negative():
    r = BM25()
    r.index(["a", "b"], ["pani pani", "pani"])
    assert all(v >= 0 for v in r.idf.values())
    assert all(score >= 0 for _, score in r.search("pani"))


def test_bm25_ties_are_broken_by_document_id():
    r = BM25()
    r.index(["z", "a", "m"], ["chai", "chai", "chai"])
    assert ids(r.search("chai")) == ["a", "m", "z"]


def test_bm25_respects_k():
    r = BM25()
    r.index(IDS, DOCS)
    assert len(r.search("chai", k=1)) == 1


def test_exact_bm25_misses_a_respelling_that_normalised_bm25_finds():
    docs = ["yeh tareeqa theek hai", "kaam karna mushkil hai"]
    exact, normalised = build_retriever("bm25"), build_retriever("bm25-l1")
    exact.index(["d1", "d2"], docs)
    normalised.index(["d1", "d2"], docs)
    assert exact.search("thik") == []
    assert ids(normalised.search("thik")) == ["d1"]


def test_level3_finds_vowel_dropped_spelling():
    r = build_retriever("bm25-l3")
    r.index(["d1", "d2"], ["kaam karna mushkil hai", "chai mein doodh"])
    assert ids(r.search("krna"))[0] == "d1"


def test_char_ngrams_tolerate_a_respelling():
    r = CharNgramTfidf()
    r.index(["d1", "d2"], ["yeh tareeqa theek hai", "kaam karna mushkil"])
    assert ids(r.search("thik"))[0] == "d1"


def test_rrf_puts_agreed_top_document_first():
    r = RRF([BM25(), CharNgramTfidf()])
    r.index(IDS, DOCS)
    result = r.search("chai patti")
    assert ids(result)[0] == "d3"
    assert set(ids(result)) >= {"d1", "d3"}
    assert result == r.search_batch(["chai patti"])[0]


def _letter_counts(texts):
    out = np.zeros((len(texts), 26), dtype=np.float32)
    for i, text in enumerate(texts):
        for ch in text.lower():
            if "a" <= ch <= "z":
                out[i, ord(ch) - 97] += 1
    return out


def test_dense_retriever_ranks_the_identical_text_first():
    r = DenseRetriever(_letter_counts)
    r.index(IDS, DOCS)
    assert ids(r.search("roti aur daal", k=2))[0] == "d2"
    batch = r.search_batch(["chai mein doodh", "roti aur daal"], k=1)
    assert [ids(x) for x in batch] == [["d1"], ["d2"]]


def test_dense_retriever_applies_prefixes_and_handles_zero_vectors():
    seen = []

    def encode(texts):
        seen.extend(texts)
        return _letter_counts(texts)

    r = DenseRetriever(encode, query_prefix="query: ", doc_prefix="passage: ")
    r.index(["d1", "d2"], ["chai", "123"])  # "123" has no letters: zero vector
    r.search("chai")
    assert seen == ["passage: chai", "passage: 123", "query: chai"]
    assert not np.isnan(r.doc_emb).any()


def test_build_retriever_names_and_errors():
    for spec in ["bm25", "bm25-l1", "bm25-l2", "bm25-l3", "char", "fusion", "rrf:bm25+char"]:
        assert build_retriever(spec).name == spec
    with pytest.raises(ValueError):
        build_retriever("bm42")
    with pytest.raises(ValueError):
        build_retriever("rrf:bm25")
