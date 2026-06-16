"""
Phase 4: Cross-encoder reranking.
Reads query + each candidate TOGETHER, scores jointly, keeps top-k.
Model: Xenova/ms-marco-MiniLM-L-6-v2 (via fastembed).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.core.config import settings
from app.retrieval.retriever import RetrievedChunk


@lru_cache(maxsize=1)
def _reranker() -> TextCrossEncoder:
    return TextCrossEncoder(model_name=settings.rerank_model)


@dataclass
class RerankedChunk:
    chunk: RetrievedChunk
    rerank_score: float


def rerank(query: str, candidates: list[RetrievedChunk],
           top_k: int = 3, log: bool = False) -> list[RerankedChunk]:
    if not candidates:
        return []

    docs = [c.text for c in candidates]
    scores = list(_reranker().rerank(query, docs))

    ranked = sorted(
        (RerankedChunk(chunk=c, rerank_score=float(s))
         for c, s in zip(candidates, scores)),
        key=lambda r: r.rerank_score,
        reverse=True,
    )

    if log:
        print(f"\n[rerank] query: {query!r}")
        print(f"[rerank] {len(candidates)} candidates -> keeping top {top_k}")
        for new_pos, r in enumerate(ranked):
            old_pos = candidates.index(r.chunk)
            marker = "  <-- KEPT" if new_pos < top_k else ""
            print(f"  rerank#{new_pos:<2} (was hybrid#{old_pos:<2}) "
                  f"score={r.rerank_score:7.3f}  "
                  f"[{r.chunk.collection}] {r.chunk.section_title[:40]}{marker}")

    return ranked[:top_k]
