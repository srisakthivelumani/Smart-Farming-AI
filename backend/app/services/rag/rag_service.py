"""
rag_service.py
--------------
Retrieval-Augmented Generation service for the Smart Farming AI project.

Orchestrates the full RAG pipeline:
    1. build_knowledge_base() — load PDFs/TXTs → chunk → embed → FAISS index
    2. retrieve_context()     — embed query → cosine search → ranked chunks
    3. ask_question()         — retrieve context → build prompt → Granite inference

Design rules:
  - GraniteService is injected; never instantiated here.
  - Credentials are never stored or logged.
  - Granite is NEVER called without retrieved context; if retrieval returns
    nothing Granite is still called but is explicitly told context is absent
    so it must state that the documents do not contain enough information.
  - Weather, market prices, and crop data are never fabricated.
"""

import logging
import os
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.exceptions import GraniteNotConfiguredError, GraniteUnavailableError
from app.services.granite_service import GraniteResponse, GraniteService
from app.services.rag.document_loader import load_document
from app.services.rag.text_chunker import chunk_documents
from app.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Paths are resolved relative to this file's location (backend/app/services/rag/)
# so the service works regardless of the working directory.
_THIS_DIR = Path(__file__).resolve().parent          # …/app/services/rag
_APP_DIR  = _THIS_DIR.parent.parent                  # …/app
_KB_DIR   = _APP_DIR / "data" / "knowledge_base"
_IDX_DIR  = _APP_DIR / "data" / "faiss_index"

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".txt"})


class RAGService:
    """End-to-end RAG pipeline backed by FAISS and IBM Granite.

    The service is stateful: :meth:`build_knowledge_base` (or
    :meth:`load_index`) must be called before :meth:`ask_question`.

    Args:
        granite_service: An initialised :class:`~app.services.granite_service.GraniteService`
            instance (typically injected via FastAPI's dependency system).
        settings:        Application settings; used for ``embedding_model``,
                         ``chunk_size``, ``chunk_overlap``, and ``rag_top_k``.
    """

    def __init__(self, granite_service: GraniteService, settings: Settings) -> None:
        self._granite = granite_service
        self._settings = settings
        self._store: VectorStore = VectorStore(
            model_name=settings.embedding_model
        )
        self._index_built: bool = False

    # ------------------------------------------------------------------ #
    #  Knowledge-base management                                           #
    # ------------------------------------------------------------------ #

    def build_knowledge_base(
        self,
        knowledge_base_dir: str | None = None,
        index_dir: str | None = None,
    ) -> dict[str, Any]:
        """Scan the knowledge-base directory, embed all documents, and save the index.

        Reads every ``.pdf`` and ``.txt`` file from ``knowledge_base_dir``,
        chunks them using :func:`~app.services.rag.text_chunker.chunk_documents`,
        builds a FAISS ``IndexFlatIP`` over normalised LaBSE embeddings, and
        persists the result to ``index_dir``.

        Args:
            knowledge_base_dir: Override the default knowledge-base path
                (``app/data/knowledge_base/``).  Useful for testing.
            index_dir: Override the default index output path
                (``app/data/faiss_index/``).

        Returns:
            A summary dict with keys:
            ``files_processed``, ``chunks_indexed``, ``index_dir``,
            ``skipped_files`` (list of filenames that could not be loaded).

        Raises:
            FileNotFoundError: If ``knowledge_base_dir`` does not exist.
            ValueError: If no supported files are found in the directory.
        """
        kb_path  = Path(knowledge_base_dir) if knowledge_base_dir else _KB_DIR
        idx_path = Path(index_dir)          if index_dir          else _IDX_DIR

        if not kb_path.exists():
            raise FileNotFoundError(
                f"Knowledge-base directory not found: '{kb_path}'. "
                "Create it and add .pdf or .txt files."
            )
        if not kb_path.is_dir():
            raise FileNotFoundError(
                f"Expected a directory, got a file: '{kb_path}'."
            )

        candidate_files = [
            f for f in kb_path.iterdir()
            if f.is_file() and f.suffix.lower() in _SUPPORTED_EXTENSIONS
        ]

        if not candidate_files:
            raise ValueError(
                f"No supported files (.pdf, .txt) found in '{kb_path}'."
            )

        logger.info(
            "build_knowledge_base: found %d file(s) in '%s'.",
            len(candidate_files), kb_path,
        )

        all_chunks: list[dict[str, Any]] = []
        skipped: list[str] = []

        for file_path in sorted(candidate_files):
            logger.info("Processing '%s' …", file_path.name)
            docs = load_document(str(file_path))
            if not docs:
                logger.warning("No content extracted from '%s' — skipping.", file_path.name)
                skipped.append(file_path.name)
                continue

            chunks = chunk_documents(
                docs,
                chunk_size=self._settings.chunk_size,
                overlap=self._settings.chunk_overlap,
            )
            if not chunks:
                logger.warning("No chunks produced from '%s' — skipping.", file_path.name)
                skipped.append(file_path.name)
                continue

            all_chunks.extend(chunks)
            logger.info(
                "  '%s' → %d doc record(s), %d chunk(s).",
                file_path.name, len(docs), len(chunks),
            )

        if not all_chunks:
            raise ValueError(
                "All files in the knowledge base were empty or unreadable. "
                "No vectors were indexed."
            )

        # Rebuild a fresh store so repeated calls do not accumulate stale vectors.
        self._store.reset()
        self._store.add_documents(all_chunks)
        self._store.save(str(idx_path))
        self._index_built = True

        summary = {
            "files_processed": len(candidate_files) - len(skipped),
            "chunks_indexed":  len(all_chunks),
            "index_dir":       str(idx_path),
            "skipped_files":   skipped,
        }
        logger.info("build_knowledge_base complete: %s", summary)
        return summary

    def load_index(self, index_dir: str | None = None) -> None:
        """Load a previously saved FAISS index from disk.

        Call this at application startup when the index has already been
        built so that :meth:`ask_question` is immediately available without
        re-embedding every document.

        Args:
            index_dir: Override the default index path
                (``app/data/faiss_index/``).

        Raises:
            FileNotFoundError: If the index directory or required files are
                missing.
            ValueError: If the stored index dimension does not match the
                current embedding model.
        """
        idx_path = Path(index_dir) if index_dir else _IDX_DIR
        self._store.load(str(idx_path))
        self._index_built = True
        logger.info("load_index: index loaded from '%s'.", idx_path)

    # ------------------------------------------------------------------ #
    #  Retrieval                                                           #
    # ------------------------------------------------------------------ #
    
    def retrieve_context(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:

        if not self._index_built:
            raise RuntimeError(
                "The FAISS index has not been built or loaded."
            )

        if not query or not query.strip():
            raise ValueError("query must be a non-empty string.")

        k = top_k if top_k is not None else self._settings.rag_top_k

        if not isinstance(k, int) or k <= 0:
            raise ValueError(f"top_k must be positive, got {k!r}.")

        # Retrieve a wider candidate set using hybrid search
        results = self._store.search(query, top_k=max(k, 20))

        min_score = self._settings.rag_min_similarity

        filtered = [
            result for result in results
            if result.get("score", 0.0) >= min_score
        ]

        # Remove duplicate results from the same source page
        unique_results = []
        seen = set()

        for result in filtered:
            key = (result.get("source"), result.get("page"))

            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        return unique_results[:k]

    

    # ------------------------------------------------------------------ #
    #  Question answering                                                  #
    # ------------------------------------------------------------------ #

    def ask_question(
        self,
        query: str,
        language: str = "English",
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """Answer an agricultural question using RAG + IBM Granite.

        Retrieves the top-k most relevant chunks from the FAISS index,
        assembles a structured prompt that includes source attribution, and
        calls :meth:`~app.services.granite_service.GraniteService.generate`.

        If retrieval returns no results Granite is still called but is
        explicitly told the documents do not contain enough information —
        it must communicate this to the user rather than fabricating an
        answer.

        Args:
            query:    The user's agricultural question.
            language: Desired response language (default ``"English"``).
                      The model will be instructed to reply in this language.
            top_k:    Override the number of context chunks to retrieve.

        Returns:
            A dict with keys:

            * ``answer``        – Granite's generated text
            * ``sources``       – list of ``{"source", "page", "file_type", "score"}``
                                  dicts for each retrieved chunk
            * ``context_used``  – ``True`` if at least one chunk was retrieved
            * ``model_id``      – Granite model identifier
            * ``input_tokens``  – IBM token usage (input)
            * ``output_tokens`` – IBM token usage (output)
            * ``latency_seconds`` – Granite inference latency

        Raises:
            RuntimeError: If the index has not been built or loaded.
            ValueError: If ``query`` is empty.
            GraniteNotConfiguredError: If IBM credentials are not set.
            GraniteUnavailableError:   If the IBM API call fails.
        """
        if not self._index_built:
            raise RuntimeError(
                "The FAISS index has not been built or loaded. "
                "Call build_knowledge_base() or load_index() first."
            )
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string.")

        # ── 1. Retrieve context chunks ──────────────────────────────────
        chunks = self.retrieve_context(query, top_k=top_k)
        context_used = bool(chunks)

        # ── 2. Build the prompt ─────────────────────────────────────────
        prompt = self._build_prompt(query, chunks, language)
        logger.debug("RAG prompt (first 300 chars): %.300s", prompt)

        # ── 3. Call Granite — propagate IBM errors unchanged ────────────
        response: GraniteResponse = self._granite.generate(
            prompt,
            max_new_tokens=self._settings.granite_max_new_tokens,
            temperature=self._settings.granite_temperature,
        )

        # ── 4. Assemble structured output ───────────────────────────────
        sources = [
            {
                "source":    c["source"],
                "page":      c["page"],
                "file_type": c["file_type"],
                "score":     round(c.get("score", 0.0), 4),
            }
            for c in chunks
        ]

        return {
            "answer":          response.generated_text,
            "sources":         sources,
            "context_used":    context_used,
            "model_id":        response.model_id,
            "input_tokens":    response.input_token_count,
            "output_tokens":   response.output_token_count,
            "latency_seconds": response.latency_seconds,
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_prompt(
        query: str,
        chunks: list[dict[str, Any]],
        language: str,
    ) -> str:
        """Assemble the RAG prompt sent to IBM Granite.

        The prompt enforces three rules explicitly stated to the model:
        (1) answer only from the provided context,
        (2) state clearly if the context is insufficient — never fabricate,
        (3) never invent weather, market prices, or crop data.

        Args:
            query:    The user's question.
            chunks:   Retrieved context chunks (may be empty).
            language: The language in which Granite should reply.

        Returns:
            A fully formatted prompt string ready for
            :meth:`~app.services.granite_service.GraniteService.generate`.
        """
        system_block = (
    "You are an agricultural assistant for the Smart Farming AI system.\n"
    "Use ONLY the information explicitly stated in the provided context.\n\n"
    "STRICT RULES:\n"
    "1. Answer only with facts directly supported by the context.\n"
    "2. Do not add assumptions, explanations, examples, or recommendations "
    "that are not explicitly supported by the context.\n"
    "3. Do not use your general knowledge to fill missing information.\n"
    "4. If the context does not contain enough information, respond with: "
    "'The available agricultural documents do not contain enough information "
    "to answer this question.'\n"
    "5. Never invent weather data, market prices, crop yields, pest statistics, "
    "or agricultural facts.\n"
    f"6. Respond in {language}.\n"
    "7. Keep the answer clear and concise.\n"
)

        if not chunks:
            context_block = (
                "--- CONTEXT ---\n"
                "[No relevant documents were found for this query.]\n"
                "--- END CONTEXT ---\n"
            )
        else:
            context_lines: list[str] = ["--- CONTEXT ---"]
            for i, chunk in enumerate(chunks, start=1):
                source_tag = (
                    f"[Source {i}: {chunk['source']}, "
                    f"page {chunk['page']}]"
                )
                context_lines.append(source_tag)
                context_lines.append(chunk["text"])
                context_lines.append("")   # blank separator
            context_lines.append("--- END CONTEXT ---")
            context_block = "\n".join(context_lines) + "\n"

        prompt = (
            f"{system_block}\n"
            f"{context_block}\n"
            f"Question: {query}\n\n"
            "Answer:"
        )
        return prompt
