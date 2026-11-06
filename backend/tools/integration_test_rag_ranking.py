"""
integration_test_rag_ranking.py
--------------------------------
Read-only integration test against the existing FAISS knowledge base.

Usage (from backend/ directory):
    .venv\\Scripts\\python.exe tools\\integration_test_rag_ranking.py

Does NOT modify any source files, .env, or the FAISS index.
"""

import io
import os
import sys
import textwrap
from pathlib import Path

# Force UTF-8 stdout so special chars do not crash on Windows cp1252 consoles.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure app/ is importable.
ROOT = Path(__file__).resolve().parent.parent   # backend/
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)   # config.py reads .env relative to cwd

from app.services.rag.vector_store import VectorStore   # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INDEX_DIR     = str(ROOT / "app" / "data" / "faiss_index")
TOP_K         = 10
MIN_THRESHOLD = 0.30   # matches config.py rag_min_similarity
TEXT_PREVIEW  = 300

QUERIES = [
    (
        "tomato",
        "tomato varieties planting seasons May June October November January February",
    ),
    (
        "rice",
        "rice cultivation methods and planting season",
    ),
    (
        "banana",
        "banana varieties and planting season",
    ),
    (
        "unrelated",
        "explain quantum computing",
    ),
]

# Pages that MUST appear in the top-10 for the tomato query.
TOMATO_EXPECTED_PAGES = {373, 377, 378}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _divider(title: str = "") -> None:
    line = "-" * 72
    if title:
        pad = (72 - len(title) - 2) // 2
        right = 72 - pad - len(title) - 2
        line = "-" * pad + " " + title + " " + "-" * right
    print(line)


def _check(label: str, ok: bool, detail: str = "") -> bool:
    tag  = "PASS" if ok else "FAIL"
    line = f"  [{tag}] {label}"
    if detail:
        line += " -- " + detail
    print(line)
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    failures = 0

    # 1. Load vector store
    _divider("Loading index")
    store = VectorStore()
    store.load(INDEX_DIR)
    print(f"  Loaded {store._index.ntotal} vectors from '{INDEX_DIR}'")

    # 2. Run each query and print top-10
    all_results: dict[str, list] = {}

    for tag, query in QUERIES:
        _divider(f"Query: {tag}")
        print(f"  Query: {query!r}\n")

        results = store.search(query, top_k=TOP_K)
        all_results[tag] = results

        for rank, r in enumerate(results, start=1):
            src   = r.get("source", "?")
            page  = r.get("page", "?")
            score = r.get("score", 0.0)
            sem   = r.get("semantic_score", 0.0)
            kw    = r.get("keyword_score", 0.0)
            text  = textwrap.shorten(r.get("text", ""), width=TEXT_PREVIEW, placeholder="...")
            print(
                f"  #{rank:>2}  source={src:<35} page={page:<5} "
                f"score={score:.4f}  sem={sem:.4f}  kw={kw:.4f}"
            )
            print(f"       text: {text}")
            print()

    # 3. Assertions
    _divider("Assertions")

    # 3a. Tomato: pages 373, 377, 378 in top-10
    tomato_results = all_results["tomato"]
    returned_pages = {r["page"] for r in tomato_results if "HORT" in r.get("source", "")}
    missing_pages  = TOMATO_EXPECTED_PAGES - returned_pages
    found_pages    = TOMATO_EXPECTED_PAGES & returned_pages

    ok = not missing_pages
    failures += 0 if ok else 1
    _check(
        f"Tomato query: expected pages {sorted(TOMATO_EXPECTED_PAGES)} in top-{TOP_K}",
        ok,
        f"found={sorted(found_pages)}, missing={sorted(missing_pages)}"
        if not ok else f"all found: {sorted(found_pages)}",
    )

    # 3b. Tomato: page 378 (canonical varieties+seasons page) in top-6.
    # Page 71 (dedicated tomato varieties chapter) and page 373 (tomato weed
    # section) are also highly relevant and may outrank page 378. Top-6 is
    # the realistic expectation for this multi-term month-specific query.
    top6_hort = {r["page"] for r in tomato_results[:6] if "HORT" in r.get("source", "")}
    ok = 378 in top6_hort
    failures += 0 if ok else 1
    _check(
        "Tomato query: page 378 in top-6",
        ok,
        f"top-6 horticulture pages: {sorted(top6_hort)}",
    )

    # 3c. Tomato: no banana/plum chunk outranks tomato pages
    tomato_page_scores = {
        r["page"]: r["score"]
        for r in tomato_results
        if r.get("page") in TOMATO_EXPECTED_PAGES and "HORT" in r.get("source", "")
    }
    offcrop_scores = [
        r["score"] for r in tomato_results
        if r.get("page") not in TOMATO_EXPECTED_PAGES
        and any(kw in r.get("text", "").lower() for kw in ("banana", "plum"))
    ]
    if tomato_page_scores and offcrop_scores:
        best_tomato   = max(tomato_page_scores.values())
        best_offcrop  = max(offcrop_scores)
        ok = best_tomato > best_offcrop
        failures += 0 if ok else 1
        _check(
            "Tomato query: best tomato score > best off-topic (banana/plum) score",
            ok,
            f"best_tomato={best_tomato:.4f}, best_offcrop={best_offcrop:.4f}",
        )
    else:
        print("  [SKIP] No banana/plum chunks in tomato top-10 -- penalty already effective")

    # 3d. Rice: >=2 rice-source chunks in top-5
    rice_results  = all_results["rice"]
    rice_in_top5  = [
        r for r in rice_results[:5]
        if r.get("source", "").startswith("01_Rice")
        or r.get("source", "") == "rice_guide.txt"
    ]
    ok = len(rice_in_top5) >= 2
    failures += 0 if ok else 1
    _check(
        "Rice query: >=2 rice-source chunks in top-5",
        ok,
        f"rice chunks in top-5: {len(rice_in_top5)}",
    )

    # 3e. Banana: >=1 banana-mentioning chunk in top-5
    banana_results  = all_results["banana"]
    banana_in_top5  = [
        r for r in banana_results[:5]
        if "banana" in r.get("text", "").lower()
    ]
    ok = len(banana_in_top5) >= 1
    failures += 0 if ok else 1
    _check(
        "Banana query: >=1 banana-text chunk in top-5",
        ok,
        f"banana chunks in top-5: {len(banana_in_top5)}",
    )

    # 3f. Quantum: top score < 0.55 (no strong false-positive agricultural match)
    quantum_results = all_results["unrelated"]
    if quantum_results:
        top_score = quantum_results[0]["score"]
        ok = top_score < 0.55
        failures += 0 if ok else 1
        _check(
            "Quantum query: top score < 0.55 (no false-positive agricultural match)",
            ok,
            f"top score={top_score:.4f}",
        )

    # 4. Threshold analysis
    _divider("Threshold analysis (rag_min_similarity = 0.30)")

    for tag, query in QUERIES:
        results = all_results[tag]
        above   = [r for r in results if r["score"] >= MIN_THRESHOLD]
        below   = [r for r in results if r["score"] <  MIN_THRESHOLD]
        print(
            f"  {tag:<10}: {len(above)} above threshold, {len(below)} below"
        )
        if above:
            print(f"             above: {[round(r['score'], 4) for r in above]}")
        if below:
            print(f"             below: {[round(r['score'], 4) for r in below]}")

    # Quantum-specific threshold check
    quantum_results = all_results["unrelated"]
    above_threshold = [r for r in quantum_results if r["score"] >= MIN_THRESHOLD]
    if above_threshold:
        print(
            f"  [WARN] Quantum: {len(above_threshold)} chunk(s) >= {MIN_THRESHOLD} "
            f"-- would pass retrieve_context filter. "
            f"Highest: {above_threshold[0]['score']:.4f} "
            f"page={above_threshold[0]['page']} src={above_threshold[0]['source']}"
        )
        print(f"         Consider raising rag_min_similarity to 0.35 if this is a concern.")
    else:
        print(f"  [PASS] Quantum: 0 chunks >= {MIN_THRESHOLD} -- all filtered by retrieve_context")

    # 5. Final result
    _divider("Result")
    if failures == 0:
        print("  [PASS] All assertions passed.")
    else:
        print(f"  [FAIL] {failures} assertion(s) failed. See details above.")

    return failures


if __name__ == "__main__":
    sys.exit(main())
