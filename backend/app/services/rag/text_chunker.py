"""
text_chunker.py
---------------
Splits structured document records (produced by document_loader.py) into
overlapping word-based chunks suitable for embedding and vector search.

Each output chunk contains:
    - chunk_id  : globally unique identifier string
    - text      : chunk text content
    - source    : original filename
    - page      : 1-based page number from the source document
    - file_type : "pdf" or "txt"
"""

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def _split_into_chunks(words: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Slide a window over a word list and return a list of text chunks.

    Args:
        words:      Tokenised words from a single document record.
        chunk_size: Maximum number of words per chunk.
        overlap:    Number of words shared between consecutive chunks.

    Returns:
        A list of non-empty chunk strings.
    """
    chunks: list[str] = []
    step = chunk_size - overlap
    start = 0

    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        start += step

    return chunks


def chunk_documents(
    documents: list[dict[str, Any]],
    chunk_size: int = 300,
    overlap: int = 60,
) -> list[dict[str, Any]]:
    """Split document records into overlapping word-based chunks.

    Accepts the list of structured records returned by
    :func:`document_loader.load_document` and splits each record's ``text``
    field into chunks of approximately ``chunk_size`` words with ``overlap``
    words of context carried over between consecutive chunks.

    Args:
        documents:  List of document records.  Each record must contain at
                    least the keys ``text``, ``source``, ``page``, and
                    ``file_type``.
        chunk_size: Target number of words per chunk.  Must be a positive
                    integer greater than ``overlap``.  Defaults to ``500``.
        overlap:    Number of words repeated at the start of each successive
                    chunk to preserve context across chunk boundaries.  Must
                    be a non-negative integer strictly less than
                    ``chunk_size``.  Defaults to ``100``.

    Returns:
        A list of chunk records.  Each record contains:

        * ``chunk_id``  – UUID4 string, unique per chunk
        * ``text``      – chunk text content (non-empty, whitespace-stripped)
        * ``source``    – inherited from the source document record
        * ``page``      – inherited from the source document record
        * ``file_type`` – inherited from the source document record

        Returns an empty list when ``documents`` is empty or every record
        yields no usable text.

    Raises:
        ValueError: If ``chunk_size`` is not a positive integer, if
                    ``overlap`` is negative, or if ``overlap`` is greater
                    than or equal to ``chunk_size``.

    Example::

        from app.services.rag.document_loader import load_document
        from app.services.rag.text_chunker import chunk_documents

        docs = load_document("data/soil_report.pdf")
        chunks = chunk_documents(docs, chunk_size=500, overlap=100)
        for c in chunks:
            print(c["chunk_id"], c["source"], c["page"], c["text"][:60])
    """
    # --- parameter validation ------------------------------------------------
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError(
            f"chunk_size must be a positive integer, got {chunk_size!r}."
        )
    if not isinstance(overlap, int) or overlap < 0:
        raise ValueError(
            f"overlap must be a non-negative integer, got {overlap!r}."
        )
    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be strictly less than "
            f"chunk_size ({chunk_size})."
        )
    # -------------------------------------------------------------------------

    result: list[dict[str, Any]] = []

    for doc in documents:
        text: str = doc.get("text", "")
        source: str = doc.get("source", "")
        page: int = doc.get("page", 1)
        file_type: str = doc.get("file_type", "")

        if not text or not text.strip():
            logger.debug("Skipping document record with empty text (source='%s').", source)
            continue

        words = text.split()

        if not words:
            logger.debug("Skipping record with no words (source='%s').", source)
            continue

        chunks = _split_into_chunks(words, chunk_size, overlap)

        for chunk_text in chunks:
            if not chunk_text.strip():
                continue

            result.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "source": source,
                    "page": page,
                    "file_type": file_type,
                }
            )

    logger.info(
        "chunk_documents: produced %d chunks from %d document record(s).",
        len(result),
        len(documents),
    )

    return result
