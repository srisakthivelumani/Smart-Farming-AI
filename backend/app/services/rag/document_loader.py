"""
document_loader.py
------------------
Loads .pdf and .txt files into structured document records for the RAG pipeline.

Each record contains:
    - text      : extracted text content
    - source    : original filename (not the full path)
    - page      : 1-based page number (always 1 for TXT files)
    - file_type : "pdf" or "txt"
"""

import logging
import os
from pathlib import Path

import pymupdf  # PyMuPDF (modern API)

logger = logging.getLogger(__name__)


def _load_pdf(file_path: Path) -> list[dict]:
    """Extract text from a PDF file page by page using PyMuPDF.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        A list of document records, one per non-empty page.
        Each record has keys: ``text``, ``source``, ``page``, ``file_type``.

    Raises:
        Nothing — errors are caught and logged; an empty list is returned on failure.
    """
    records: list[dict] = []
    source = file_path.name

    try:
        doc = pymupdf.open(str(file_path))
    except Exception as exc:
        logger.error("Could not open PDF '%s': %s", file_path, exc)
        return records

    try:
        for page_index in range(len(doc)):
            try:
                page = doc.load_page(page_index)
                text = page.get_text().strip()
            except Exception as exc:
                logger.warning(
                    "Could not read page %d of '%s': %s",
                    page_index + 1,
                    file_path,
                    exc,
                )
                continue

            if not text:
                logger.debug("Skipping empty page %d in '%s'.", page_index + 1, file_path)
                continue

            records.append(
                {
                    "text": text,
                    "source": source,
                    "page": page_index + 1,
                    "file_type": "pdf",
                }
            )
    finally:
        doc.close()

    if not records:
        logger.warning("No extractable text found in PDF '%s'.", file_path)

    return records


def _load_txt(file_path: Path) -> list[dict]:
    """Read a plain-text UTF-8 file and return a single document record.

    Args:
        file_path: Absolute or relative path to the TXT file.

    Returns:
        A list with one document record, or an empty list if the file is empty
        or cannot be read.
        The record has keys: ``text``, ``source``, ``page``, ``file_type``.
    """
    source = file_path.name

    try:
        text = file_path.read_text(encoding="utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        logger.error("Could not decode '%s' as UTF-8: %s", file_path, exc)
        return []
    except OSError as exc:
        logger.error("Could not read file '%s': %s", file_path, exc)
        return []

    if not text:
        logger.warning("File '%s' is empty — skipping.", file_path)
        return []

    return [
        {
            "text": text,
            "source": source,
            "page": 1,
            "file_type": "txt",
        }
    ]


def load_document(file_path: str) -> list[dict]:
    """Load a supported document file and return structured text records.

    Supported formats: ``.pdf`` (via PyMuPDF) and ``.txt`` (UTF-8).

    Each returned record is a ``dict`` with the following keys:

    * ``text``      – extracted text content (non-empty, stripped)
    * ``source``    – filename (e.g. ``"crop_guide.pdf"``)
    * ``page``      – 1-based page number (always ``1`` for TXT files)
    * ``file_type`` – ``"pdf"`` or ``"txt"``

    Args:
        file_path: Path to the document file as a string.

    Returns:
        A (possibly empty) list of document record dicts.
        Returns an empty list when the file is missing, unsupported, empty,
        or unreadable — the reason is logged at ERROR or WARNING level.

    Example::

        records = load_document("data/soil_report.pdf")
        for r in records:
            print(r["source"], r["page"], r["text"][:80])
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("File not found: '%s'", file_path)
        return []

    if not path.is_file():
        logger.error("Path is not a file: '%s'", file_path)
        return []

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _load_pdf(path)
    elif suffix == ".txt":
        return _load_txt(path)
    else:
        logger.error(
            "Unsupported file type '%s' for '%s'. Supported types: .pdf, .txt",
            suffix,
            file_path,
        )
        return []
