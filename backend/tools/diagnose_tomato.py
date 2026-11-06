"""
diagnose_tomato.py
-------------------
Deep diagnostic for the tomato retrieval problem.
Read-only. Run from backend/.
"""
import io, json, os, re, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.services.rag.vector_store import VectorStore

INDEX_DIR = str(ROOT / "app" / "data" / "faiss_index")
QUERY     = "tomato varieties planting seasons May June October November January February"

store = VectorStore()
store.load(INDEX_DIR)

# 1. Fetch raw FAISS top-200 semantic scores for the query
import faiss, numpy as np
qe = store._model.encode([QUERY], convert_to_numpy=True).astype(np.float32)
faiss.normalize_L2(qe)
raw_scores, raw_idx = store._index.search(qe, min(200, store._index.ntotal))

print("=== Raw FAISS semantic scores for pages 373/377/378 ===")
for idx, sc in zip(raw_idx[0], raw_scores[0]):
    if idx == -1: continue
    chunk = store._metadata[int(idx)]
    if chunk.get("page") in {373, 377, 378}:
        print(f"  faiss_rank={list(raw_idx[0]).index(idx)+1}  page={chunk['page']}  sem={sc:.4f}")
        print(f"  text[:200]: {chunk['text'][:200]!r}")
        print()

print("=== Full text of pages 373, 377, 378 ===")
meta = json.load(open("app/data/faiss_index/metadata.json", encoding="utf-8"))
for c in meta:
    if c.get("page") in {373, 377, 378}:
        print(f"\n--- page {c['page']} ---")
        print(c["text"])

# 2. Where does "tomato" actually appear?
print("\n=== Chunks where 'tomato' appears in text (first 10) ===")
count = 0
for i, c in enumerate(meta):
    if "tomato" in c.get("text", "").lower():
        print(f"  idx={i}  page={c['page']}  src={c['source']}")
        print(f"  text[:200]: {c['text'][:200]!r}")
        print()
        count += 1
        if count >= 10:
            break

# 3. Hybrid search top-10 with full score breakdown
print("=== Hybrid search top-10 for tomato query ===")
results = store.search(QUERY, top_k=10)
for rank, r in enumerate(results, 1):
    print(f"  #{rank}  page={r['page']}  score={r['score']:.4f}  sem={r['semantic_score']:.4f}  kw={r['keyword_score']:.4f}")
    print(f"     text[:150]: {r['text'][:150]!r}")
