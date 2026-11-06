"""Verify OCR repair on page 377."""
import io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
ROOT = Path(".").resolve(); sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
from app.services.rag.vector_store import VectorStore
store = VectorStore(); store.load("app/data/faiss_index")

target = next(x for x in store._metadata if x["page"] == 377)
q_crops = {"tomato", "tomatoes"}

# Simulate OCR repairs
ocr_repairs = []
for crop in q_crops:
    if len(crop) >= 5:
        for split_at in range(4, len(crop)):
            prefix = re.escape(crop[:split_at])
            suffix = re.escape(crop[split_at:])
            pat = re.compile(r"\b" + prefix + r"\s*[-\s]?\s*" + suffix + r"\b", re.IGNORECASE)
            ocr_repairs.append((pat, crop))

raw_text = target["text"].lower()
text = raw_text
for pat, replacement in ocr_repairs:
    text = pat.sub(replacement, text)

words = set(re.findall(r"[a-zA-Z0-9]+", text))
other_crops = store._KNOWN_CROPS - q_crops
crop_occ = sum(len(re.findall(r"\b" + re.escape(crop) + r"\b", text)) for crop in q_crops)
has_other = bool(words & other_crops)

print(f"crop_occ after OCR repair = {crop_occ}")
print(f"has_other = {has_other}, other crops: {words & other_crops}")

# Find what's around "tomat" in original text
import re as _re
for m in _re.finditer(r"tomat\w*", target["text"], re.IGNORECASE):
    start = max(0, m.start()-20)
    end = min(len(target["text"]), m.end()+20)
    print(f"  Found: {target['text'][start:end]!r}")
