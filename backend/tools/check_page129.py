"""Check page 129 scoring in detail."""
import io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
ROOT = Path(".").resolve()
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.services.rag.vector_store import VectorStore
store = VectorStore()
store.load("app/data/faiss_index")

target = next(x for x in store._metadata if x["page"] == 129 and "HORT" in x["source"])
text = target["text"].lower()
words = set(re.findall(r"[a-zA-Z0-9]+", text))

q_crops = {"tomato", "tomatoes"}
other_crops = store._KNOWN_CROPS - q_crops

spec = {
    "varieties", "variety", "cultivar", "cultivars",
    "planting", "sowing", "transplanting",
    "germination", "seedling", "nursery",
    "fertilizer", "fertiliser", "pesticide", "irrigation",
    "harvest", "harvesting", "yield", "season", "seasons",
}

crop_occ = sum(len(re.findall(r"\b" + re.escape(crop) + r"\b", text)) for crop in q_crops)
sig = bool(words & spec)
primary = crop_occ >= 2 or (crop_occ >= 1 and sig)
has_other = bool(words & other_crops)

print(f"page 129:")
print(f"  crop_occ={crop_occ}, sig={sig}, primary={primary}, has_other={has_other}")
print(f"  other crops in chunk: {words & other_crops}")
print(f"  signal terms in chunk: {words & spec}")
print(f"  text[:400]: {target['text'][:400]!r}")
