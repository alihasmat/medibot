"""
Phase 6B: document RAG answer generation from reranked chunks, with citations.
"""
from __future__ import annotations

from app.rag.llm import complete
from app.retrieval.reranker import RerankedChunk

_SYSTEM = (
    "You are MediBot, an assistant for MediAssist Health Network staff. "
    "Answer the question using ONLY the provided context passages. "
    "If the context does not contain the answer, say you don't have that "
    "information in the documents you can access -- do not guess. "
    "Be concise and clinically precise. Cite the source document(s) you used "
    "at the end like: [Source: <document>]."
)


def _format_context(chunks: list[RerankedChunk]) -> str:
    blocks = []
    for i, r in enumerate(chunks, 1):
        c = r.chunk
        blocks.append(
            f"[Passage {i}] (document: {c.source_document}, "
            f"section: {c.section_title})\n{c.text}"
        )
    return "\n\n".join(blocks)


def generate_answer(question: str, chunks: list[RerankedChunk]) -> str:
    if not chunks:
        return ("I don't have any documents I can access that cover that "
                "question.")
    context = _format_context(chunks)
    return complete(
        system=_SYSTEM,
        user=f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
    ).strip()
