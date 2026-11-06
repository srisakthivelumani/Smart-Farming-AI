"""
Integration test script - Smart Farming AI
-------------------------------------------
Tests:
  1. FAISS index load (LaBSE embeddings)
  2. Retrieval for 4 questions (top-5 results per question)
  3. IBM Granite connectivity and inference

Run from project root with the backend venv:
  .\\backend\\.venv\\Scripts\\python.exe .\\backend\\run_integration_tests.py

Does NOT modify any files. Does NOT expose credentials.
"""

import sys
import textwrap
import time
from pathlib import Path

# Force UTF-8 output so the log file is readable regardless of console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow imports from app/ when run from any working directory
_BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND_DIR))

SEP  = "=" * 72
SEP2 = "-" * 72


def heading(text):
    print(f"\n{SEP}")
    print(f"  {text}")
    print(SEP)


def subheading(text):
    print(f"\n{SEP2}")
    print(f"  {text}")
    print(SEP2)


# Settings (reads .env, never prints credentials)
from app.core.config import get_settings
settings = get_settings()


# ==============================================================================
# PART 1 - FAISS Index Load & Retrieval Tests
# ==============================================================================

heading("PART 1 - FAISS Index Load & Retrieval Tests")

from app.services.rag.vector_store import VectorStore

_IDX_DIR = _BACKEND_DIR / "app" / "data" / "faiss_index"
_KB_DIR  = _BACKEND_DIR / "app" / "data" / "knowledge_base"

print("\n[Index directory]")
for f in sorted(_IDX_DIR.iterdir()):
    size_kb = f.stat().st_size // 1024
    print(f"  {f.name:<25}  {size_kb:>7} KB")

print("\n[Knowledge base files]")
for f in sorted(_KB_DIR.iterdir()):
    size_kb = f.stat().st_size // 1024
    print(f"  {f.name:<50}  {size_kb:>7} KB")

print(f"\n[Loading VectorStore]  model={settings.embedding_model}")
t0 = time.perf_counter()
store = VectorStore(model_name=settings.embedding_model)
store.load(str(_IDX_DIR))
load_elapsed = time.perf_counter() - t0
print(f"  Index loaded in {load_elapsed:.2f}s  |  vectors={store._index.ntotal}")

QUESTIONS = [
    "What are the tomato planting seasons in Tamil Nadu?",
    "What are the recommended rice cultivation practices?",
    "What are the common banana varieties and planting seasons?",
    "Explain quantum computing.",
]

RETRIEVAL_RESULTS = {}

for q_num, question in enumerate(QUESTIONS, start=1):
    subheading(f"Question {q_num}: {question}")

    t0 = time.perf_counter()
    raw_results = store.search(question, top_k=5)
    elapsed = time.perf_counter() - t0

    min_score = settings.rag_min_similarity
    filtered = [r for r in raw_results if r.get("score", 0.0) >= min_score]
    RETRIEVAL_RESULTS[question] = filtered

    print(f"\n  Retrieved in {elapsed:.3f}s  |  "
          f"raw_hits={len(raw_results)}  "
          f"above_threshold({min_score})={len(filtered)}")

    if not raw_results:
        print("  [NO RESULTS RETURNED]")
        continue

    print(f"\n  {'Rank':<5} {'Score':>6}  {'Sem':>6}  {'Kw':>6}  "
          f"{'Source':<40}  {'Page':>4}  Preview (60 chars)")
    print(f"  {'----':<5} {'------':>6}  {'------':>6}  {'------':>6}  "
          f"{'------':<40}  {'----':>4}  --------")

    for rank, r in enumerate(raw_results[:5], start=1):
        source  = r.get("source", "?")[-38:]
        page    = r.get("page", "?")
        score   = r.get("score", 0.0)
        sem     = r.get("semantic_score", 0.0)
        kw      = r.get("keyword_score", 0.0)
        preview = r.get("text", "")[:60].replace("\n", " ").strip()
        marker  = "+" if score >= min_score else " "
        print(f"  {marker}{rank:<4} {score:>6.4f}  {sem:>6.4f}  {kw:>6.4f}  "
              f"{source:<40}  {str(page):>4}  {preview}")

    grounded = len(filtered) > 0
    verdict = "YES - context available" if grounded else "NO - below threshold (Granite told: no context)"
    print(f"\n  -> Grounded in documents: {verdict}")


# ==============================================================================
# PART 2 - IBM Granite Connectivity
# ==============================================================================

heading("PART 2 - IBM Granite Connectivity")

print(f"\n  model_id            : {settings.granite_model_id}")
print(f"  endpoint            : {settings.watsonx_url}")
print(f"  api_key configured  : {bool(settings.watsonx_api_key)}")
print(f"  project_id config   : {bool(settings.watsonx_project_id)}")

from app.services.granite_service import GraniteService
granite = GraniteService(settings=settings)
result  = granite.test_connection()

print(f"\n  Connection success   : {result.success}")
if result.success:
    print(f"  Latency             : {result.latency_seconds:.2f}s")
    print(f"  Input tokens        : {result.input_tokens}")
    print(f"  Output tokens       : {result.output_tokens}")
    resp_preview = textwrap.shorten(result.sample_response, width=110, placeholder="[truncated]")
    print(f"  Sample response     : {resp_preview}")
    if result.tamil_test_attempted:
        tamil_preview = textwrap.shorten(result.tamil_test_response, width=110, placeholder="[truncated]")
        print(f"  Tamil probe result  : {tamil_preview}")
        print(f"  Tamil probe note    : {result.tamil_test_note[:100]}")
else:
    print(f"  Error type          : {result.ibm_error_type}")
    print(f"  IBM error           : {result.ibm_error_message}")


# ==============================================================================
# PART 3 - End-to-End RAG Answer (tomato, Granite required)
# ==============================================================================

heading("PART 3 - End-to-End RAG Answer (tomato question)")

if not result.success:
    print("\n  [SKIPPED] - Granite unavailable. See Part 2 error above.")
else:
    from app.services.rag.rag_service import RAGService
    rag = RAGService(granite_service=granite, settings=settings)
    rag.load_index(str(_IDX_DIR))

    q = QUESTIONS[0]
    print(f"\n  Question : {q}")
    print("  Running RAG pipeline...")
    t0 = time.perf_counter()
    try:
        answer  = rag.ask_question(q, language="English")
        elapsed = time.perf_counter() - t0
        print(f"\n  Total latency      : {elapsed:.2f}s  (Granite: {answer['latency_seconds']:.2f}s)")
        print(f"  Model              : {answer['model_id']}")
        print(f"  Context used       : {answer['context_used']}")
        print(f"  Input tokens       : {answer['input_tokens']}")
        print(f"  Output tokens      : {answer['output_tokens']}")
        print(f"\n  Sources cited:")
        for s in answer["sources"]:
            print(f"    * {s['source']}  page={s['page']}  score={s['score']}")
        print(f"\n  Answer:")
        for line in answer["answer"].splitlines():
            print(f"    {line}")
    except Exception as exc:
        print(f"  [ERROR] {type(exc).__name__}: {exc}")


# ==============================================================================
# SUMMARY
# ==============================================================================

heading("SUMMARY")
for q_num, (q, hits) in enumerate(RETRIEVAL_RESULTS.items(), start=1):
    tag = "IN-DOMAIN " if hits else "OUT-OF-DOMAIN"
    print(f"  Q{q_num}  [{tag}]  hits={len(hits)}  {q[:60]}")

print(f"\n  Granite available   : {result.success}")
print()
