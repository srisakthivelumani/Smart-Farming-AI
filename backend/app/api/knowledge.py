"""
Knowledge Base API — file upload and document listing.

Routes:
    POST /api/kb/upload      — upload a single PDF or TXT file
    GET  /api/kb/documents   — list all supported files in the knowledge base
"""

import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.core.dependencies import RAGServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

# Resolve the knowledge-base directory relative to THIS file so the path is
# correct regardless of the process working directory.
# __file__ → …/backend/app/api/knowledge.py
# parents:  [0] api/  [1] app/  [2] backend/
_KB_DIR: Path = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".txt"})
# Only allow filenames that contain word characters, hyphens, dots, and spaces.
_SAFE_FILENAME_RE = re.compile(r"^[\w\s\-\.]+$")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _sanitise_filename(raw_name: str) -> str:
    """Return a filesystem-safe version of *raw_name*.

    Strips leading/trailing whitespace, replaces interior whitespace runs
    with underscores, and removes every character that is not alphanumeric,
    a hyphen, a dot, or an underscore.  The result always retains the
    original extension (lower-cased).

    Args:
        raw_name: The ``filename`` field from the uploaded ``UploadFile``.

    Returns:
        A sanitised filename string without any path separators.
    """
    name = Path(raw_name).name        # strip any path component
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()

    # Collapse whitespace → underscore, strip unsafe chars
    stem = re.sub(r"\s+", "_", stem.strip())
    stem = re.sub(r"[^\w\-]", "", stem)

    if not stem:
        stem = "upload"

    return f"{stem}{suffix}"


def _unique_path(directory: Path, filename: str) -> Path:
    """Return a path inside *directory* that does not already exist.

    If ``filename`` is already taken, appends a short UUID4 hex segment
    before the extension, e.g. ``report_3f2a.pdf``.

    Args:
        directory: Target directory (must already exist).
        filename:  Desired filename (already sanitised).

    Returns:
        A :class:`~pathlib.Path` whose name is guaranteed not to collide
        with any existing file in *directory*.
    """
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    short_uid = uuid.uuid4().hex[:8]
    return directory / f"{stem}_{short_uid}{suffix}"


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/upload",
    summary="Upload a PDF or TXT file to the knowledge base",
    description=(
        "Accepts a single `.pdf` or `.txt` file, sanitises the filename to "
        "prevent path traversal, generates a unique name on collision, and "
        "saves the file to `app/data/knowledge_base/`."
    ),
    status_code=201,
)
async def upload_document(
    rag_service: RAGServiceDep,
    file: UploadFile = File(..., description="A .pdf or .txt file to upload"),
) -> JSONResponse:
    """Save an uploaded file to the knowledge-base directory.

    Args:
        file: The multipart file upload.

    Returns:
        HTTP 201 with ``filename``, ``file_type``, and ``status`` fields.

    Raises:
        HTTPException 400: Unsupported file extension or missing filename.
        HTTPException 500: File could not be written to disk.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}'. "
                "Only .pdf and .txt files are accepted."
            ),
        )

    safe_name = _sanitise_filename(file.filename)

    # Ensure the knowledge-base directory exists before writing.
    _KB_DIR.mkdir(parents=True, exist_ok=True)

    dest = _unique_path(_KB_DIR, safe_name)

    try:
        contents = await file.read()
        dest.write_bytes(contents)
    except OSError as exc:
        logger.error("Failed to save uploaded file '%s': %s", dest.name, exc)
        raise HTTPException(
            status_code=500,
            detail="File could not be saved. Please try again.",
        ) from exc
    finally:
        await file.close()

    logger.info(
        "upload_document: saved '%s' (%d bytes) to '%s'.",
        dest.name, len(contents), _KB_DIR,
    )

    try:
        index_summary = rag_service.build_knowledge_base()
        logger.info("Knowledge base rebuilt: %s", index_summary)
    except Exception as exc:
        logger.exception("Failed to rebuild knowledge base after upload.")
        raise HTTPException(
            status_code=500,
            detail=(
                "File was saved, but knowledge-base indexing failed. "
                "Please check the backend logs."
            ),
        ) from exc

    return JSONResponse(
        status_code=201,
        content={
            "filename":  dest.name,
            "file_type": suffix.lstrip("."),
            "status":    "uploaded",
        },
    )


@router.get(
    "/documents",
    summary="List documents in the knowledge base",
    description=(
        "Returns metadata for every `.pdf` and `.txt` file currently stored "
        "in `app/data/knowledge_base/`. Returns an empty list when the "
        "directory exists but contains no supported files."
    ),
)
async def list_documents() -> JSONResponse:
    """List all supported documents in the knowledge-base directory.

    Returns:
        HTTP 200 with a ``documents`` list.  Each entry contains
        ``filename``, ``file_type``, and ``size_bytes``.
        Returns an empty ``documents`` list when no files are present.
    """
    if not _KB_DIR.exists():
        logger.info("list_documents: knowledge-base directory does not exist yet.")
        return JSONResponse(status_code=200, content={"documents": []})

    files = sorted(
        f for f in _KB_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in _SUPPORTED_EXTENSIONS
    )

    documents = [
        {
            "filename":   f.name,
            "file_type":  f.suffix.lower().lstrip("."),
            "size_bytes": f.stat().st_size,
        }
        for f in files
    ]

    logger.info("list_documents: returning %d document(s).", len(documents))
    return JSONResponse(status_code=200, content={"documents": documents})
