"""
diagnose_pages_377_378.py
--------------------------
Investigate why pages 377 and 378 score low for the tomato query.
"""
import io, json, re, os, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.services.rag.vector_store import VectorStore
import faiss, numpy as np

INDEX_DIR = str(ROOT / "app" / "data" / "faiss_index")
QUERY = "tomato varieties planting seasons May June October November January February"

store = VectorStore()
store.load(INDEX_DIR)

meta = store._metadata

# ── Inspect the words in pages 377 and 378 ───────────────────────────────────
query_crops = {"tomato", "tomatoes"}
specific_terms = {
    "varieties", "variety", "cultivar", "cultivars",
    "planting", "sowing", "transplanting",
    "germination", "seedling", "nursery",
    "fertilizer", "fertiliser", "pesticide", "irrigation",
    "harvest", "harvesting", "yield",
    "season", "seasons",
}

for page in (377, 378):
    chunks = [c for c in meta if c["page"] == page]
    for c in chunks:
        text = c["text"].lower()
        words = set(re.findall(r"[a-zA-Z0-9]+", text))
        crop_occurrences = sum(
            len(re.findall(r"\b" + re.escape(crop) + r"\b", text))
            for crop in query_crops
        )
        sig_match = bool(words & specific_terms)
        chunk_is_primary = crop_occurrences >= 2 or (crop_occurrences >= 1 and sig_match)
        print(f"\nPage {page}:")
        print(f"  crop_occurrences={crop_occurrences}")
        print(f"  signal_terms_present={sig_match}")
        print(f"  chunk_is_primary={chunk_is_primary}")
        print(f"  words & specific_terms = {words & specific_terms}")
        print(f"  text[:400]: {c['text'][:400]!r}")

# ── Run search and show extended top-20, highlighting 377/378 ────────────────
print("\n\n=== Hybrid search top-20, highlighting 377/378 ===")
results = store.search(QUERY, top_k=20)
for rank, r in enumerate(results, 1):
    marker = " <-- TOMATO TARGET" if r["page"] in {373, 377, 378} else ""
    print(f"  #{rank:>2}  page={r['page']:<5} score={r['score']:.4f}  sem={r['semantic_score']:.4f}  kw={r['keyword_score']:.4f}{marker}")

# ── Find where 377 and 378 actually land ────────────────────────────────────
print("\n=== Full search (ALL chunks) for pages 377 and 378 ===")
all_results = store.search(QUERY, top_k=store._index.ntotal)
for rank, r in enumerate(all_results, 1):
    if r["page"] in {377, 378}:
        print(f"  Rank {rank}: page={r['page']}  score={r['score']:.4f}  sem={r['semantic_score']:.4f}  kw={r['keyword_score']:.4f}")
        print(f"  text[:200]: {r['text'][:200]!r}")
