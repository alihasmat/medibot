"""
Standalone Phase 1 inspection: parse all documents and print a report.
Run once before indexing (Phase 2).
    cd backend
    uv run python scripts/inspect_chunks.py
"""
from collections import Counter
from pathlib import Path

from app.ingestion.chunker import ingest_folder

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main() -> None:
    print(f"Reading documents from: {DATA_DIR}")
    chunks = ingest_folder(DATA_DIR)

    if not chunks:
        print("\nNo chunks produced. Check that data/<collection>/*.pdf exist.")
        return

    by_collection = Counter(c.collection for c in chunks)
    by_type = Counter(c.chunk_type for c in chunks)

    print("\n--- Chunks per collection ---")
    for col, n in sorted(by_collection.items()):
        print(f"  {col:12s} {n:4d}")

    print("\n--- Chunks per type ---")
    for t, n in sorted(by_type.items()):
        print(f"  {t:8s} {n:4d}")

    incomplete = [
        c for c in chunks
        if not all([c.source_document, c.collection, c.access_roles,
                    c.section_title, c.chunk_type])
    ]
    print(f"\n--- Metadata completeness ---")
    print(f"  chunks with all 5 fields populated: {len(chunks) - len(incomplete)}/{len(chunks)}")
    if incomplete:
        print(f"  WARNING: {len(incomplete)} chunk(s) missing a field")

    print("\n--- Sample chunks (confirm heading appears in the text) ---")
    seen_cols = set()
    for c in chunks:
        if c.collection in seen_cols:
            continue
        seen_cols.add(c.collection)
        print(f"\n  [{c.collection}] {c.source_document}")
        print(f"    section_title : {c.section_title}")
        print(f"    chunk_type    : {c.chunk_type}")
        print(f"    access_roles  : {c.access_roles}")
        print(f"    embedded text : {c.text[:220].strip()!r}...")

    tables = [c for c in chunks if c.chunk_type == "table"]
    if tables:
        print(f"\n--- Found {len(tables)} table chunk(s); first one: ---")
        print(f"    {tables[0].text[:300].strip()!r}")


if __name__ == "__main__":
    main()
