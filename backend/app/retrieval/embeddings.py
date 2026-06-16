"""
Local embedding models (fastembed) shared across ingestion and retrieval.
- Dense  : BAAI/bge-small-en-v1.5  -> 384-dim semantic vector
- Sparse : Qdrant/bm25             -> sparse keyword vector (BM25)
"""
from __future__ import annotations

from functools import lru_cache

from fastembed import TextEmbedding, SparseTextEmbedding

from app.core.config import settings


@lru_cache(maxsize=1)
def dense_model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.dense_model)


@lru_cache(maxsize=1)
def sparse_model() -> SparseTextEmbedding:
    return SparseTextEmbedding(model_name=settings.sparse_model)


DENSE_DIM = 384


def embed_dense(texts: list[str]) -> list[list[float]]:
    return [vec.tolist() for vec in dense_model().embed(texts)]


def embed_sparse(texts: list[str]):
    return list(sparse_model().embed(texts))


def embed_dense_one(text: str) -> list[float]:
    return next(iter(dense_model().embed([text]))).tolist()


def embed_sparse_one(text: str):
    return next(iter(sparse_model().embed([text])))
