"""Quick metadata inspection — read-only, no modifications."""
import json
import sys

meta = json.load(open("app/data/faiss_index/metadata.json", encoding="utf-8"))
print(f"Total chunks: {len(meta)}")
sources = sorted(set(c["source"] for c in meta))
print("Sources:", sources)

for src in sources:
    pages = sorted(set(c["page"] for c in meta if c["source"] == src))
    print(f"  {src}: {len(pages)} unique pages, range {pages[0]}–{pages[-1]}")

# Show chunks at horticulture pages 370-380
print("\n--- Horticulture pages 370–382 ---")
for c in meta:
    if "HORT" in c["source"] and 370 <= c["page"] <= 382:
        print(f"  page={c['page']}  text[:120]={c['text'][:120]!r}")
