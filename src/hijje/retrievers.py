"""Retrievers under test.

Every retriever has the same two methods, so the evaluation code does not
need to know which one it is running:

    index(doc_ids, texts)        build the index once
    search(query, k)             -> [(doc_id, score), ...] best first

Ties are always broken the same way, so two runs give identical rankings.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from functools import partial
from typing import Callable, Optional, Sequence

import numpy as np

from .normalize import analyze
from .text import tokenize

Ranking = list  # list[tuple[str, float]]


class BaseRetriever:
    name: str = "retriever"

    def index(self, doc_ids: Sequence[str], texts: Sequence[str]) -> None:
        raise NotImplementedError

    def search(self, query: str, k: int = 10) -> Ranking:
        raise NotImplementedError

    def search_batch(self, queries: Sequence[str], k: int = 10) -> list[Ranking]:
        return [self.search(q, k) for q in queries]


class BM25(BaseRetriever):
    """Okapi BM25 with the non-negative (Lucene-style) IDF.

    Written out in plain Python on purpose: it is ~40 lines, has no hidden
    preprocessing, and takes any analyzer, which is how the normalised
    variants (bm25-l1 to bm25-l4) are built. For corpora with millions
    of passages, swap in a compiled implementation behind the same interface.
    """

    def __init__(
        self,
        analyzer: Callable[[str], list] = tokenize,
        k1: float = 1.2,
        b: float = 0.75,
        name: str = "bm25",
    ) -> None:
        self.analyzer, self.k1, self.b, self.name = analyzer, k1, b, name

    def index(self, doc_ids, texts) -> None:
        self.doc_ids = list(doc_ids)
        self.postings: dict = defaultdict(list)
        self.doc_len = []
        for i, text in enumerate(texts):
            tokens = self.analyzer(text)
            self.doc_len.append(len(tokens))
            for term, tf in Counter(tokens).items():
                self.postings[term].append((i, tf))
        n = len(self.doc_ids)
        self.avgdl = (sum(self.doc_len) / n) if n else 0.0
        self.idf = {
            term: math.log(1.0 + (n - len(plist) + 0.5) / (len(plist) + 0.5))
            for term, plist in self.postings.items()
        }

    def search(self, query, k=10) -> Ranking:
        scores: dict = defaultdict(float)
        for term in self.analyzer(query):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, tf in self.postings[term]:
                norm = 1.0 - self.b + self.b * self.doc_len[i] / (self.avgdl or 1.0)
                scores[i] += idf * tf * (self.k1 + 1.0) / (tf + self.k1 * norm)
        ranked = sorted(scores.items(), key=lambda item: (-item[1], self.doc_ids[item[0]]))
        return [(self.doc_ids[i], score) for i, score in ranked[:k]]


class CharNgramTfidf(BaseRetriever):
    """TF-IDF over character n-grams inside word boundaries.

    A respelled word still shares most of its character n-grams with the
    original, so this retriever tolerates spelling changes without knowing
    anything about Urdu. It is the language-agnostic baseline that the
    phonetic rules have to beat to justify their existence.
    """

    def __init__(self, ngram_range=(2, 4), name: str = "char") -> None:
        self.ngram_range, self.name = ngram_range, name

    def index(self, doc_ids, texts) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.doc_ids = list(doc_ids)
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=self.ngram_range, lowercase=True, sublinear_tf=True
        )
        self.matrix = self.vectorizer.fit_transform(list(texts))

    def search(self, query, k=10) -> Ranking:
        qv = self.vectorizer.transform([query])
        scores = (self.matrix @ qv.T).toarray().ravel()
        order = np.argsort(-scores, kind="stable")[:k]
        return [(self.doc_ids[i], float(scores[i])) for i in order if scores[i] > 0]


class RRF(BaseRetriever):
    """Reciprocal Rank Fusion of several retrievers.

    score(d) = sum over retrievers of 1 / (k_rrf + rank of d).
    It uses ranks only, so retrievers with incomparable score scales (BM25
    scores, cosine similarities) can be combined without calibration.
    """

    def __init__(self, retrievers, k_rrf: int = 60, depth: int = 100, name: str = "fusion") -> None:
        self.retrievers, self.k_rrf, self.depth, self.name = list(retrievers), k_rrf, depth, name

    def index(self, doc_ids, texts) -> None:
        for r in self.retrievers:
            r.index(doc_ids, texts)

    def _fuse(self, rankings, k) -> Ranking:
        scores: dict = defaultdict(float)
        for ranking in rankings:
            for rank, (doc_id, _) in enumerate(ranking, start=1):
                scores[doc_id] += 1.0 / (self.k_rrf + rank)
        return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]

    def search(self, query, k=10) -> Ranking:
        return self._fuse([r.search(query, self.depth) for r in self.retrievers], k)

    def search_batch(self, queries, k=10) -> list[Ranking]:
        per_retriever = [r.search_batch(queries, self.depth) for r in self.retrievers]
        return [self._fuse([runs[i] for runs in per_retriever], k) for i in range(len(queries))]


class DenseRetriever(BaseRetriever):
    """Exact cosine-similarity search over sentence embeddings.

    `encode` is any function texts -> 2-D array. Passing the encoder in keeps
    this class testable without downloading a model, and lets any embedding
    library be used.
    """

    def __init__(self, encode, name: str = "dense", query_prefix: str = "", doc_prefix: str = "") -> None:
        self.encode, self.name = encode, name
        self.query_prefix, self.doc_prefix = query_prefix, doc_prefix

    @staticmethod
    def _unit(x) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        norms = np.linalg.norm(x, axis=1, keepdims=True)
        return x / np.where(norms == 0, 1.0, norms)

    def index(self, doc_ids, texts) -> None:
        self.doc_ids = list(doc_ids)
        self.doc_emb = self._unit(self.encode([self.doc_prefix + t for t in texts]))

    def search_batch(self, queries, k=10) -> list[Ranking]:
        q = self._unit(self.encode([self.query_prefix + t for t in queries]))
        scores = q @ self.doc_emb.T
        out = []
        for row in scores:
            order = np.argsort(-row, kind="stable")[:k]
            out.append([(self.doc_ids[i], float(row[i])) for i in order])
        return out

    def search(self, query, k=10) -> Ranking:
        return self.search_batch([query], k)[0]

    @classmethod
    def from_sentence_transformers(
        cls, model_name: str, device: Optional[str] = None, batch_size: int = 64
    ) -> "DenseRetriever":
        """Load a sentence-transformers model (needs `pip install "hijje[dense]"`).

        E5 models were trained with "query: " and "passage: " prefixes and lose
        accuracy without them, so the prefixes are added for that family. The
        "instruct" E5 variants use a different prompt format and are not
        handled here.
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise ImportError(
                'Dense retrievers need sentence-transformers: pip install "hijje[dense]"'
            ) from exc
        model = SentenceTransformer(model_name, device=device)

        def encode(texts):
            return model.encode(
                list(texts), batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False
            )

        lowered = model_name.lower()
        is_e5 = "e5" in lowered and "instruct" not in lowered
        prefixes = ("query: ", "passage: ") if is_e5 else ("", "")
        return cls(encode, name=f"dense:{model_name}", query_prefix=prefixes[0], doc_prefix=prefixes[1])


def build_retriever(spec: str) -> BaseRetriever:
    """Create a retriever from a short name.

    bm25                 exact-token BM25
    bm25-l1 .. -l4       BM25 over normalised tokens (see normalize.py)
    char                 character n-gram TF-IDF
    fusion               RRF of bm25 + bm25-l2 + char
    rrf:a+b+c            RRF of any listed retrievers
    dense:<model>        a sentence-transformers model from the Hugging Face hub
    """
    s = spec.strip()
    if s == "bm25":
        return BM25()
    m = re.fullmatch(r"bm25-l([1234])", s)
    if m:
        return BM25(analyzer=partial(analyze, level=int(m.group(1))), name=s)
    if s == "char":
        return CharNgramTfidf()
    if s == "fusion":
        return RRF([build_retriever(p) for p in ("bm25", "bm25-l2", "char")], name="fusion")
    if s.startswith("rrf:"):
        parts = [p for p in s[4:].split("+") if p]
        if len(parts) < 2:
            raise ValueError("rrf: needs at least two retrievers, e.g. rrf:bm25+char")
        return RRF([build_retriever(p) for p in parts], name=s)
    if s.startswith("dense:"):
        return DenseRetriever.from_sentence_transformers(s[len("dense:"):])
    raise ValueError(f"unknown retriever spec: {spec!r}")
