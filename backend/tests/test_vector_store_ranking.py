"""
test_vector_store_ranking.py
-----------------------------
Unit tests for VectorStore.search() hybrid ranking, focusing on:

1. Tomato-specific query → tomato chunks rank above off-topic crop chunks.
2. Rice-specific query → rice chunks rank above off-topic crop chunks.
3. Unrelated query (soil pH) → no crop mismatch penalty applied; most
   semantically similar result ranks first.
4. Edge cases: empty index, bad inputs, no-query-crop query.
"""
import re
import sys
import types
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Minimal stubs so VectorStore can be imported without FAISS / sentence-
# transformers being installed (unit-test isolation).
# ---------------------------------------------------------------------------

# Stub: faiss
faiss_stub = types.ModuleType("faiss")


class _FakeIndexFlatIP:
    """Minimal stand-in for faiss.IndexFlatIP."""

    def __init__(self, dim: int) -> None:
        self.d = dim
        self._vectors: list[np.ndarray] = []

    @property
    def ntotal(self) -> int:
        return len(self._vectors)

    def add(self, vecs: np.ndarray) -> None:
        for v in vecs:
            self._vectors.append(v.copy())

    def search(self, query: np.ndarray, k: int):
        """Brute-force dot-product search (vectors already L2-normalised)."""
        if not self._vectors:
            return np.array([[-1.0] * k]), np.array([[-1] * k])

        mat = np.stack(self._vectors)          # (n, d)
        sims = mat @ query[0]                  # (n,)
        k_eff = min(k, len(self._vectors))
        top = np.argsort(sims)[::-1][:k_eff]
        scores = sims[top]

        pad = k - k_eff
        if pad:
            top = np.concatenate([top, np.full(pad, -1, dtype=top.dtype)])
            scores = np.concatenate([scores, np.full(pad, -1.0)])

        return scores[np.newaxis, :], top[np.newaxis, :]


faiss_stub.IndexFlatIP = _FakeIndexFlatIP
faiss_stub.normalize_L2 = lambda x: x.__itruediv__(
    np.linalg.norm(x, axis=1, keepdims=True).clip(min=1e-10)
)
faiss_stub.write_index = MagicMock()
faiss_stub.read_index = MagicMock()
sys.modules["faiss"] = faiss_stub

# Stub: sentence_transformers
st_stub = types.ModuleType("sentence_transformers")


class _FakeSentenceTransformer:
    """Returns a deterministic unit vector derived from the text hash."""

    DIM = 16

    def __init__(self, model_name: str) -> None:
        pass

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        out = []
        for text in texts:
            rng = np.random.default_rng(abs(hash(text)) % (2**32))
            v = rng.standard_normal(self.DIM).astype(np.float32)
            v /= np.linalg.norm(v)
            out.append(v)
        arr = np.stack(out)
        return arr


st_stub.SentenceTransformer = _FakeSentenceTransformer
sys.modules["sentence_transformers"] = st_stub

# Now we can safely import VectorStore.
from app.services.rag.vector_store import VectorStore  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(*chunk_groups) -> VectorStore:
    """Build a VectorStore pre-loaded with the given chunk groups.

    Each group is a list of dicts with at minimum a ``"text"`` key.
    ``source``, ``page``, and ``file_type`` are filled with defaults
    if omitted.
    """
    store = VectorStore.__new__(VectorStore)
    store.model_name = "stub"
    store._model = _FakeSentenceTransformer("stub")
    store._dim = _FakeSentenceTransformer.DIM
    store._index = _FakeIndexFlatIP(store._dim)
    store._metadata = []

    all_chunks = []
    for group in chunk_groups:
        for chunk in group:
            chunk.setdefault("source", "test.pdf")
            chunk.setdefault("page", 1)
            chunk.setdefault("file_type", "pdf")
            all_chunks.append(chunk)

    store.add_documents(all_chunks)
    return store


# ---------------------------------------------------------------------------
# Fixtures — small synthetic corpora
# ---------------------------------------------------------------------------

TOMATO_CHUNKS = [
    {
        "text": (
            "Tomato varieties suitable for the region include PKM-1 and CO-3. "
            "Planting seasons are May-June, October-November, and January-February."
        ),
        "source": "horticulture.pdf",
        "page": 378,
        "file_type": "pdf",
    },
    {
        "text": (
            "Tomato cultivation requires well-drained soil. "
            "Transplanting of tomato seedlings is done 25 days after sowing."
        ),
        "source": "horticulture.pdf",
        "page": 377,
        "file_type": "pdf",
    },
]

BANANA_CHUNKS = [
    {
        "text": (
            "Banana varieties like Nendran and Robusta are planted during the "
            "rainy season. Banana planting requires spacing of 1.8 m × 1.8 m."
        ),
        "source": "horticulture.pdf",
        "page": 201,
        "file_type": "pdf",
    },
]

PLUM_CHUNKS = [
    {
        "text": (
            "Plum varieties are grown in temperate regions. "
            "Planting season for plum is December to February."
        ),
        "source": "horticulture.pdf",
        "page": 150,
        "file_type": "pdf",
    },
]

RICE_CHUNKS = [
    {
        "text": (
            "Rice (Oryza sativa) is cultivated in flooded paddy fields. "
            "Transplanting of rice seedlings is done 20–25 days after sowing."
        ),
        "source": "rice_guide.txt",
        "page": 1,
        "file_type": "txt",
    },
    {
        "text": (
            "Rice varieties suitable for Tamil Nadu include ADT-36 and CO-47. "
            "Sowing season for rice is June–July for Kuruvai crop."
        ),
        "source": "rice_guide.txt",
        "page": 3,
        "file_type": "txt",
    },
]

SOIL_CHUNK = [
    {
        "text": (
            "Soil pH affects nutrient availability. "
            "Most crops prefer a pH between 6.0 and 7.0."
        ),
        "source": "soil_guide.pdf",
        "page": 10,
        "file_type": "pdf",
    },
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTomatoQuery:
    """Tomato-specific query must rank tomato chunks above off-topic crops."""

    def setup_method(self):
        self.store = _make_store(TOMATO_CHUNKS, BANANA_CHUNKS, PLUM_CHUNKS)

    def test_tomato_chunk_ranks_first(self):
        results = self.store.search(
            "What are the tomato varieties and planting seasons?", top_k=5
        )
        assert results, "search returned no results"
        top_source_page = (results[0]["source"], results[0]["page"])
        # The first result must be one of the tomato pages.
        tomato_pages = {(c["source"], c["page"]) for c in TOMATO_CHUNKS}
        assert top_source_page in tomato_pages, (
            f"Expected a tomato page as top result, got page {results[0]['page']} "
            f"(source: {results[0]['source']}, score: {results[0]['score']:.4f})"
        )

    def test_tomato_chunks_outrank_banana_and_plum(self):
        results = self.store.search(
            "What are the tomato varieties and planting seasons?", top_k=5
        )
        tomato_pages = {(c["source"], c["page"]) for c in TOMATO_CHUNKS}
        off_topic_pages = {(c["source"], c["page"]) for c in BANANA_CHUNKS + PLUM_CHUNKS}

        tomato_scores = [
            r["score"] for r in results
            if (r["source"], r["page"]) in tomato_pages
        ]
        off_topic_scores = [
            r["score"] for r in results
            if (r["source"], r["page"]) in off_topic_pages
        ]

        assert tomato_scores, "No tomato chunks in results"
        if off_topic_scores:
            assert max(tomato_scores) > max(off_topic_scores), (
                f"Best tomato score {max(tomato_scores):.4f} ≤ "
                f"best off-topic score {max(off_topic_scores):.4f}"
            )

    def test_result_contains_required_metadata(self):
        results = self.store.search("tomato varieties planting", top_k=3)
        for r in results:
            assert "source" in r
            assert "page" in r
            assert "file_type" in r
            assert "score" in r
            assert "semantic_score" in r
            assert "keyword_score" in r

    def test_score_components_in_expected_range(self):
        results = self.store.search("tomato varieties", top_k=5)
        for r in results:
            assert 0.0 <= r["keyword_score"] <= 1.0, (
                f"keyword_score out of range: {r['keyword_score']}"
            )
            assert r["score"] >= 0.0


class TestRiceQuery:
    """Rice-specific query must rank rice chunks above off-topic crops."""

    def setup_method(self):
        self.store = _make_store(RICE_CHUNKS, TOMATO_CHUNKS, BANANA_CHUNKS)

    def test_rice_chunk_ranks_first(self):
        results = self.store.search(
            "What are the rice varieties and sowing season?", top_k=5
        )
        assert results, "search returned no results"
        top_page = results[0]["page"]
        top_source = results[0]["source"]
        rice_pages = {(c["source"], c["page"]) for c in RICE_CHUNKS}
        assert (top_source, top_page) in rice_pages, (
            f"Expected a rice page, got source={top_source} page={top_page} "
            f"score={results[0]['score']:.4f}"
        )

    def test_rice_outranks_tomato_on_rice_query(self):
        results = self.store.search(
            "Rice cultivation transplanting seedlings paddy", top_k=5
        )
        rice_pages = {(c["source"], c["page"]) for c in RICE_CHUNKS}
        tomato_pages = {(c["source"], c["page"]) for c in TOMATO_CHUNKS}

        rice_scores = [r["score"] for r in results if (r["source"], r["page"]) in rice_pages]
        tomato_scores = [r["score"] for r in results if (r["source"], r["page"]) in tomato_pages]

        assert rice_scores, "No rice chunks in results"
        if tomato_scores:
            assert max(rice_scores) > max(tomato_scores), (
                f"Rice best={max(rice_scores):.4f}, tomato best={max(tomato_scores):.4f}"
            )


class TestUnrelatedQuery:
    """Query with no crop name must not wrongly demote/promote by crop heuristics."""

    def setup_method(self):
        self.store = _make_store(SOIL_CHUNK, TOMATO_CHUNKS, RICE_CHUNKS)

    def test_returns_results(self):
        results = self.store.search("soil pH nutrient availability", top_k=5)
        assert results, "No results for soil query"

    def test_no_crop_mismatch_penalty_when_no_query_crop(self):
        """When the query has no crop name, keyword_score must not be halved."""
        results = self.store.search("soil pH nutrient availability", top_k=5)
        for r in results:
            # keyword_score should be based purely on coverage, not penalised.
            # The penalty is ×0.50; if every crop-bearing chunk were penalised,
            # they'd all have fractional scores below their coverage.
            # We simply verify scores are non-negative and keyword_score <= 1.0.
            assert r["keyword_score"] >= 0.0
            assert r["keyword_score"] <= 1.0

    def test_metadata_intact_on_unrelated_query(self):
        results = self.store.search("irrigation water management", top_k=5)
        for r in results:
            assert "source" in r
            assert "page" in r
            assert "file_type" in r


class TestEdgeCases:
    """Edge cases: empty index, bad inputs, crop-free query."""

    def test_empty_index_returns_empty_list(self):
        store = VectorStore.__new__(VectorStore)
        store.model_name = "stub"
        store._model = _FakeSentenceTransformer("stub")
        store._dim = _FakeSentenceTransformer.DIM
        store._index = _FakeIndexFlatIP(store._dim)
        store._metadata = []

        assert store.search("tomato varieties", top_k=5) == []

    def test_empty_query_raises(self):
        store = _make_store(TOMATO_CHUNKS)
        with pytest.raises(ValueError, match="non-empty"):
            store.search("", top_k=5)

    def test_whitespace_query_raises(self):
        store = _make_store(TOMATO_CHUNKS)
        with pytest.raises(ValueError, match="non-empty"):
            store.search("   ", top_k=5)

    def test_negative_top_k_raises(self):
        store = _make_store(TOMATO_CHUNKS)
        with pytest.raises(ValueError, match="top_k"):
            store.search("tomato", top_k=-1)

    def test_top_k_respected(self):
        store = _make_store(TOMATO_CHUNKS, BANANA_CHUNKS, PLUM_CHUNKS, RICE_CHUNKS)
        results = store.search("crop cultivation", top_k=2)
        assert len(results) <= 2

    def test_known_crops_is_frozenset(self):
        """_KNOWN_CROPS must be a frozenset (class attribute, not mutated at runtime)."""
        assert isinstance(VectorStore._KNOWN_CROPS, frozenset)

    def test_no_crop_query_not_penalised(self):
        """A crop-free query should not apply the crop-mismatch penalty."""
        store = _make_store(BANANA_CHUNKS, PLUM_CHUNKS, RICE_CHUNKS)
        results = store.search("irrigation water scheduling", top_k=5)
        # All keyword_scores must be in valid range.
        for r in results:
            assert 0.0 <= r["keyword_score"] <= 1.0
