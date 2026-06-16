"""
Phase 3: Hybrid retrieval (dense + BM25) with RBAC enforced at the query level.
"""
from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import QdrantClient, models

from app.core.config import settings
from app.retrieval.embeddings import embed_dense_one, embed_sparse_one
from app.retrieval.vector_store import DENSE_VECTOR, SPARSE_VECTOR


@dataclass
class RetrievedChunk:
    text: str
    source_document: str
    collection: str
    section_title: str
    chunk_type: str
    score: float


def _rbac_filter(role: str) -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key="access_roles",
                match=models.MatchAny(any=[role]),
            )
        ]
    )


def hybrid_search(client: QdrantClient, query: str, role: str,
                  candidates: int = 10) -> list[RetrievedChunk]:
    dense_vec = embed_dense_one(query)
    sparse_vec = embed_sparse_one(query)
    rbac = _rbac_filter(role)

    result = client.query_points(
        collection_name=settings.collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_vec,
                using=DENSE_VECTOR,
                filter=rbac,
                limit=candidates,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vec.indices.tolist(),
                    values=sparse_vec.values.tolist(),
                ),
                using=SPARSE_VECTOR,
                filter=rbac,
                limit=candidates,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=rbac,
        limit=candidates,
        with_payload=True,
    )

    chunks: list[RetrievedChunk] = []
    for point in result.points:
        p = point.payload
        chunks.append(RetrievedChunk(
            text=p["text"],
            source_document=p["source_document"],
            collection=p["collection"],
            section_title=p["section_title"],
            chunk_type=p["chunk_type"],
            score=point.score,
        ))
    return chunks
