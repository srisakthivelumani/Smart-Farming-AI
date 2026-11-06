"""Check OCR join effect on page 373."""
import io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
ROOT = Path(".").resolve(); sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
from app.services.rag.vector_store import VectorStore
store = VectorStore(); store.load("app/data/faiss_index")

target = next(x for x in store._metadata if x["page"] == 373)

_ocr_join = re.compile(r"([a-z]{3,})\s*[-\s]\s*([a-z]{1,3})\b")
raw_text = target["text"].lower()
text = _ocr_join.sub(lambda m: m.group(1) + m.group(2), raw_text)

words_raw = set(re.findall(r"[a-zA-Z0-9]+", raw_text))
words_new = set(re.findall(r"[a-zA-Z0-9]+", text))

q_terms_all = set(re.findall(r"[a-zA-Z0-9]+", "tomato varieties planting seasons may june october november january february".lower()))
stop = {"what","which","where","when","why","how","the","is","are","was","were","in","on","of","for","to","and","or","a","an","according","document","documents","my","important","discussed","mentioned","their","about","from","with"}
q_terms = q_terms_all - stop

print("Query terms:", sorted(q_terms))
print("\nMatched (raw):", sorted(q_terms & words_raw))
print("Matched (ocr-joined):", sorted(q_terms & words_new))

print("\nDiff (lost by ocr join):", sorted((q_terms & words_raw) - (q_terms & words_new)))
print("Diff (gained by ocr join):", sorted((q_terms & words_new) - (q_terms & words_raw)))

# Show words that got modified
lost = words_raw - words_new
gained = words_new - words_raw
print("\nWords LOST by join (could be query terms):", sorted(w for w in lost if w in q_terms))
