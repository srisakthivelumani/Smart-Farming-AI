"""
vector_store.py
---------------
FAISS-backed vector store for the Smart Farming AI RAG pipeline.

Uses sentence-transformers for dense embeddings and a FAISS IndexFlatIP
(inner-product) index over L2-normalised vectors to achieve cosine
similarity search entirely on CPU.

Typical usage::

    from app.services.rag.vector_store import VectorStore

    store = VectorStore()
    store.add_documents(chunks)          # chunks from text_chunker
    results = store.search("soil pH", top_k=5)

    store.save("app/data/faiss_index")
    store.load("app/data/faiss_index")
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_METADATA_FILENAME = "metadata.json"
_INDEX_FILENAME = "index.faiss"


class VectorStore:
    """CPU-based cosine-similarity vector store backed by FAISS and LaBSE.

    Embeddings are L2-normalised before being added to a ``IndexFlatIP``
    index so that inner-product search is equivalent to cosine similarity.
    The embedding dimension is determined at construction time by encoding a
    single probe sentence — it is never hardcoded.

    Attributes:
        model_name: HuggingFace model identifier used for embeddings.
    """

    def __init__(self, model_name: str = "sentence-transformers/LaBSE") -> None:
        """Initialise the vector store and load the embedding model."""
        self.model_name: str = model_name
        logger.info("Loading embedding model '%s' ...", model_name)
        self._model: SentenceTransformer = SentenceTransformer(model_name)

        probe: np.ndarray = self._model.encode(
            ["probe"], convert_to_numpy=True
        )
        self._dim: int = int(probe.shape[1])
        logger.info("Embedding dimension detected: %d", self._dim)

        self._index: faiss.IndexFlatIP = faiss.IndexFlatIP(self._dim)
        self._metadata: list[dict[str, Any]] = []

    def reset(self) -> None:
        """Clear indexed vectors while keeping the embedding model loaded."""
        self._index = faiss.IndexFlatIP(self._dim)
        self._metadata.clear()
        logger.info("Vector store reset; embedding model retained.")

   

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add_documents(self, chunks: list[dict[str, Any]]) -> None:
        """Encode chunks and add them to the FAISS index.

        Each chunk must contain at minimum a ``"text"`` key.  The keys
        ``chunk_id``, ``source``, ``page``, and ``file_type`` are preserved
        as metadata and returned verbatim by :meth:`search`.

        Args:
            chunks: List of chunk dicts as produced by
                :func:`~app.services.rag.text_chunker.chunk_documents`.

        Raises:
            ValueError: If ``chunks`` is empty.
        """
        if not chunks:
            raise ValueError("chunks must not be empty.")

        texts = [c.get("text", "") for c in chunks]
        non_empty_indices = [i for i, t in enumerate(texts) if t.strip()]

        if not non_empty_indices:
            logger.warning("add_documents: all chunks have empty text — nothing added.")
            return

        valid_texts = [texts[i] for i in non_empty_indices]
        valid_chunks = [chunks[i] for i in non_empty_indices]

        logger.info("Encoding %d chunk(s) …", len(valid_texts))
        embeddings: np.ndarray = self._model.encode(
            valid_texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype(np.float32)

        faiss.normalize_L2(embeddings)
        self._index.add(embeddings)
        self._metadata.extend(valid_chunks)

        logger.info(
            "add_documents: added %d vector(s). Index total: %d.",
            len(valid_chunks),
            self._index.ntotal,
        )

    
    
    # Known crop names used for query-crop-aware ranking.
    # Add new crops here as the knowledge base grows — no other code changes needed.
    _KNOWN_CROPS: frozenset[str] = frozenset({
        "tomato", "tomatoes",
        "rice", "paddy",
        "wheat",
        "maize", "corn",
        "banana", "bananas",
        "plum", "plums",
        "mango", "mangoes",
        "onion", "onions",
        "potato", "potatoes",
        "chilli", "chillies", "chili",
        "groundnut", "groundnuts",
        "sugarcane",
        "cotton",
        "soybean", "soya",
        "coconut",
        "brinjal", "eggplant",
        "cabbage",
        "cauliflower",
        "okra", "ladyfinger",
        "bitter gourd", "bittergourd",
        "pumpkin",
        "watermelon",
        "grapes", "grape",
        # Legumes and other vegetables found in the knowledge base
        "pea", "peas",
        "bean", "beans",
        "lentil", "lentils",
        "pepper", "capsicum",
        "guava",
        "muskmelon",
        "gherkin",
        "tapioca",
        "vanilla",
        "marigold",
        "jasmine",
    })

    def search(self, query: str, top_k: int = 20) -> list[dict[str, Any]]:
        """Retrieve chunks using hybrid semantic + crop-aware keyword ranking.

        Scoring pipeline
        ----------------
        1. FAISS inner-product search over L2-normalised embeddings gives a
           *semantic_score* in [-1, 1] (cosine similarity).

        2. A full linear scan of all chunk texts gives a *keyword_score* in
           [0, 1] composed of:
           a. **Base coverage** — fraction of non-stop query terms that appear
              in the chunk.
           b. **Specific-term bonus** (+0.05 each, capped) — for terms like
              "varieties", "planting", "sowing" that carry agronomic signal
              (deliberately excludes generic words like "crop", "season").
           c. **Primary crop-name bonus** (+0.35) — applied when the chunk
              contains the query crop name as a *primary subject*: the crop
              name appears ≥2 times, OR appears together with at least one
              agronomic signal term (varieties / planting / sowing / season /
              cultivar / transplanting / harvest / yield).  This distinguishes
              "Tomato … planted during May-June" (primary) from an incidental
              list entry ("crop growing districts … tomato").
           d. **Crop-name mismatch penalty** (×0.50) — when the chunk contains
              a *different* well-known crop but does NOT contain the query crop
              at all.

        3. Final score blending:
           - Chunks found by FAISS (semantic_score > 0): 0.55 × sem + 0.45 × kw
           - Keyword-only chunks (semantic_score == 0, not in FAISS top-k):
             0.35 × sem + 0.65 × kw  (keywords dominate since FAISS missed them)
        """
        import re

        if not query or not query.strip():
            raise ValueError("query must be a non-empty string.")

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k!r}.")

        if self._index.ntotal == 0:
            return []

        # 1. Semantic retrieval: collect a wider candidate set.
        effective_k = min(max(top_k * 10, 100), self._index.ntotal)

        query_embedding = self._model.encode(
            [query], convert_to_numpy=True
        ).astype(np.float32)

        faiss.normalize_L2(query_embedding)
        scores, indices = self._index.search(query_embedding, effective_k)

        combined: dict[int, dict[str, Any]] = {}

        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue

            combined[int(idx)] = {
                **self._metadata[int(idx)],
                "semantic_score": float(score),
                "keyword_score": 0.0,
            }

        # 2. Keyword retrieval across ALL chunks.
        stop_words = {
            "what", "which", "where", "when", "why", "how",
            "the", "is", "are", "was", "were", "in", "on",
            "of", "for", "to", "and", "or", "a", "an",
            "according", "document", "documents", "my",
            "important", "discussed", "mentioned",
            "their", "about", "from", "with",
        }

        query_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        query_terms -= stop_words

        # Identify crop names explicitly mentioned in the query.
        query_crops = query_terms & self._KNOWN_CROPS
        # Other-crop names — crops NOT in the query, used for mismatch detection.
        other_crops = self._KNOWN_CROPS - query_crops

        # Specific agronomic signal terms (non-generic).
        # Used both for the specific-term bonus and for the primary-crop test.
        specific_terms = {
            "varieties", "variety", "cultivar", "cultivars",
            "planting", "sowing", "transplanting",
            "germination", "seedling", "nursery",
            "fertilizer", "fertiliser", "pesticide", "irrigation",
            "harvest", "harvesting", "yield",
            "season", "seasons",
        }

        # Build a set of crop-specific OCR repair patterns from the query crops.
        # OCR from scanned PDFs sometimes hyphenates or splits crop names across
        # columns, e.g. "Tomat o" (space) or "Tomat-\no" (hyphen+newline).
        # We repair these only for the exact query-crop substrings to avoid
        # corrupting unrelated words (e.g. "tomato in" must not become "tomatoin").
        ocr_repairs: list[tuple[re.Pattern, str]] = []
        for crop in query_crops:
            # Match the crop name split after at least 4 characters, with an
            # optional hyphen/space followed by the remainder — but ONLY when the
            # remainder is followed by a word boundary (space or punctuation),
            # not another letter, to avoid merging "tomato into" → "tomatointo".
            if len(crop) >= 5:
                for split_at in range(4, len(crop)):
                    prefix = re.escape(crop[:split_at])
                    suffix = re.escape(crop[split_at:])
                    pat = re.compile(
                        r"\b" + prefix + r"\s*[-\s]?\s*" + suffix + r"\b",
                        re.IGNORECASE,
                    )
                    ocr_repairs.append((pat, crop))

        if query_terms:
            for idx, chunk in enumerate(self._metadata):
                raw_text = chunk.get("text", "").lower()
                # Apply targeted OCR repairs for query-crop names only.
                text = raw_text
                for pat, replacement in ocr_repairs:
                    text = pat.sub(replacement, text)
                words = set(re.findall(r"[a-zA-Z0-9]+", text))

                matched_terms = query_terms.intersection(words)

                if not matched_terms:
                    continue

                # Base coverage score (0.0–1.0).
                coverage = len(matched_terms) / len(query_terms)

                # Small bonus per specific agronomic term that matched.
                specific_matches = len(matched_terms.intersection(specific_terms))
                keyword_score = min(1.0, coverage + 0.05 * specific_matches)

                # ── Crop-name awareness ──────────────────────────────────
                if query_crops:
                    # Count occurrences after OCR normalisation.
                    crop_occurrences = sum(
                        len(re.findall(r"\b" + re.escape(crop) + r"\b", text))
                        for crop in query_crops
                    )
                    chunk_has_query_crop = crop_occurrences >= 1
                    chunk_has_other_crop = bool(words & other_crops)

                    # "Primary subject" test: query crop dominates the chunk.
                    # Requires ≥2 occurrences, OR exactly 1 occurrence alongside
                    # an agronomic signal term — BUT only when the chunk does NOT
                    # also contain a different known crop (which would indicate the
                    # query-crop mention is incidental in a multi-crop context).
                    crop_with_signal = (
                        crop_occurrences >= 1
                        and bool(words & specific_terms)
                        and not chunk_has_other_crop          # no competing crop
                    )
                    chunk_is_primary_crop = (
                        crop_occurrences >= 2                  # repeated mentions
                        or crop_with_signal                    # sole crop + signal
                    )

                    if chunk_is_primary_crop:
                        # Strong boost: chunk is primarily about the queried crop.
                        # +0.45 ensures that a primary-crop chunk with decent coverage
                        # always reaches keyword_score = 1.0 (min(1.0, x+0.45)).
                        keyword_score = min(1.0, keyword_score + 0.45)
                    elif chunk_has_query_crop and chunk_has_other_crop:
                        # Incidental mention in a multi-crop chunk: no net change
                        # (weak positive would still be outweighed by off-topic content).
                        pass
                    elif chunk_has_query_crop:
                        # Weak boost: crop name appears once without a competing crop.
                        keyword_score = min(1.0, keyword_score + 0.10)
                    elif chunk_has_other_crop:
                        # Penalty: chunk is about a different known crop entirely.
                        keyword_score *= 0.50
                # ────────────────────────────────────────────────────────

                if idx in combined:
                    combined[idx]["keyword_score"] = keyword_score
                else:
                    combined[idx] = {
                        **chunk,
                        "semantic_score": 0.0,
                        "keyword_score": keyword_score,
                    }

        # 3. Calculate combined score.
        # A single blended formula: 0.55 semantic + 0.45 keyword.
        # For keyword-only chunks (semantic_score == 0.0, not in FAISS top-k),
        # a small flat lift of +0.10 is added so they remain competitive when
        # the keyword evidence is strong — but not so large that noisy keyword
        # matches can overwhelm semantically-scored results.
        results = []

        for result in combined.values():
            semantic_score = result["semantic_score"]
            keyword_score = result["keyword_score"]

            base = 0.55 * semantic_score + 0.45 * keyword_score

            if semantic_score == 0.0 and keyword_score >= 0.80:
                # Keyword-only path with strong keyword signal: add a small lift.
                base += 0.10

            result["score"] = base
            results.append(result)

        # 4. Sort by hybrid score.
        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]


    def save(self, index_dir: str) -> None:
        """Persist the FAISS index and chunk metadata to disk.

        Creates ``index_dir`` if it does not exist.  Writes two files:

        * ``index.faiss``   – the serialised FAISS index
        * ``metadata.json`` – JSON array of chunk metadata dicts

        Args:
            index_dir: Directory path where the index files will be written.

        Raises:
            OSError: If the directory cannot be created or files cannot be
                written.
        """
        dir_path = Path(index_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        index_path = dir_path / _INDEX_FILENAME
        metadata_path = dir_path / _METADATA_FILENAME

        faiss.write_index(self._index, str(index_path))
        metadata_path.write_text(
            json.dumps(self._metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info(
            "save: wrote %d vector(s) to '%s'.", self._index.ntotal, index_dir
        )

    def load(self, index_dir: str) -> None:
        """Load a previously saved FAISS index and metadata from disk.

        Replaces the current in-memory index and metadata entirely.

        Args:
            index_dir: Directory containing ``index.faiss`` and
                ``metadata.json`` as written by :meth:`save`.

        Raises:
            FileNotFoundError: If ``index_dir``, ``index.faiss``, or
                ``metadata.json`` do not exist.
            ValueError: If the loaded index dimension does not match the
                model's embedding dimension.
            json.JSONDecodeError: If ``metadata.json`` is malformed.
        """
        dir_path = Path(index_dir)

        if not dir_path.exists():
            raise FileNotFoundError(
                f"Index directory not found: '{index_dir}'"
            )

        index_path = dir_path / _INDEX_FILENAME
        metadata_path = dir_path / _METADATA_FILENAME

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index file not found: '{index_path}'"
            )
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: '{metadata_path}'"
            )

        loaded_index: faiss.IndexFlatIP = faiss.read_index(str(index_path))

        if loaded_index.d != self._dim:
            raise ValueError(
                f"Loaded index dimension ({loaded_index.d}) does not match "
                f"model dimension ({self._dim})."
            )

        self._index = loaded_index
        self._metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        logger.info(
            "load: loaded %d vector(s) from '%s'.", self._index.ntotal, index_dir
        )
