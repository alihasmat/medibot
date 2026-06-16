"""
Local on-disk Qdrant store: collection setup + indexing.
One collection holds every chunk as a point with TWO named vectors:
  - "dense"  : semantic similarity (bge-small-en-v1.5)
  - "sparse" : BM25 keyword matching (Qdrant/bm25)
"""
from __future__ import annotations

import uuid

from qdrant_client import QdrantClient, models

from app.core.config import settings
from app.ingestion.chunker import MediChunk
from app.retrieval.embeddings import DENSE_DIM, embed_dense, embed_sparse

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"


def get_client() -> QdrantClient:
    return QdrantClient(path=settings.qdrant_path)


def recreate_collection(client: QdrantClient) -> None:
    if client.collection_exists(settings.collection_name):
        client.delete_collection(settings.collection_name)

    client.create_collection(
        collection_name=settings.collection_name,
        vectors_config={
            DENSE_VECTOR: models.VectorParams(
                size=DENSE_DIM,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            SPARSE_VECTOR: models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            ),
        },
    )


def index_chunks(client: QdrantClient, chunks: list[MediChunk],
                 batch_size: int = 32) -> int:
    total = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        texts = [c.text for c in batch]

        dense_vecs = embed_dense(texts)
        sparse_vecs = embed_sparse(texts)

        points = []
        for chunk, dvec, svec in zip(batch, dense_vecs, sparse_vecs):
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    DENSE_VECTOR: dvec,
                    SPARSE_VECTOR: models.SparseVector(
                        indices=svec.indices.tolist(),
                        values=svec.values.tolist(),
                    ),
                },
                payload={
                    "text": chunk.text,
                    "source_document": chunk.source_document,
                    "collection": chunk.collection,
                    "access_roles": chunk.access_roles,
                    "section_title": chunk.section_title,
                    "chunk_type": chunk.chunk_type,
                },
            ))

        client.upsert(collection_name=settings.collection_name, points=points)
        total += len(points)
        print(f"  indexed {total}/{len(chunks)}")

    return total
