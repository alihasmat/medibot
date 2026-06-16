"""
Phase 2 ingestion: parse all documents and build the Qdrant hybrid index.
Run ONCE:  uv run python backend/scripts/ingest.py
"""
from pathlib import Path

from app.ingestion.chunker import ingest_folder
from app.retrieval.vector_store import get_client, recreate_collection, index_chunks
from app.core.config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main() -> None:
    print(f"Parsing documents from: {DATA_DIR}")
    chunks = ingest_folder(DATA_DIR)
    if not chunks:
        print("No chunks produced; aborting.")
        return

    print(f"\nOpening Qdrant at: {settings.qdrant_path}")
    client = get_client()

    print(f"Creating collection '{settings.collection_name}' (dense + sparse)...")
    recreate_collection(client)

    print(f"Embedding and indexing {len(chunks)} chunks...")
    n = index_chunks(client, chunks)

    info = client.get_collection(settings.collection_name)
    print(f"\nDone. Indexed {n} points.")
    print(f"Collection reports {info.points_count} points.")

    sample, _ = client.scroll(
        collection_name=settings.collection_name,
        limit=1, with_payload=True, with_vectors=True,
    )
    if sample:
        p = sample[0]
        print("\nSample point payload fields:", sorted(p.payload.keys()))
        print("Sample point vectors present:", sorted(p.vector.keys()))
        print("Sample collection:", p.payload["collection"],
              "| access_roles:", p.payload["access_roles"])


if __name__ == "__main__":
    main()
