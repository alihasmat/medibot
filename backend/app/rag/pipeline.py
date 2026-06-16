"""
Phase 6C: /chat orchestration -- classify, route to SQL or document RAG.
"""
from __future__ import annotations

from qdrant_client import QdrantClient

from app.core.config import SQL_RAG_ROLES, collections_for_role
from app.rag.llm import complete
from app.rag.sql_rag import sql_rag_chain
from app.rag.doc_rag import generate_answer
from app.retrieval.retriever import hybrid_search
from app.retrieval.reranker import rerank

_CLASSIFY_SYSTEM = (
    "Classify the user's question as exactly one word:\n"
    "- 'analytical' if it asks for counts, totals, averages, statistics, "
    "rankings, or aggregates over billing claims or equipment maintenance "
    "records (data that lives in a database).\n"
    "- 'document' if it asks about policies, procedures, protocols, drug "
    "information, guidelines, codes reference, or any explanatory content.\n"
    "Reply with only the single word: analytical OR document."
)


def classify(question: str) -> str:
    out = complete(_CLASSIFY_SYSTEM, f"Question: {question}").strip().lower()
    return "analytical" if "analytical" in out else "document"


def _refusal(role: str) -> str:
    allowed = collections_for_role(role)
    return (f"As a {role.replace('_', ' ')}, you don't have access to that "
            f"information. I can only answer questions from the "
            f"{', '.join(allowed)} collections.")


def answer_question(client: QdrantClient, question: str, role: str,
                    candidates: int = 15, top_k: int = 3) -> dict:
    kind = classify(question)

    if kind == "analytical":
        if role in SQL_RAG_ROLES:
            out = sql_rag_chain(question)
            return {"answer": out["answer"], "sources": [],
                    "retrieval_type": "sql_rag", "role": role}
        return {
            "answer": (f"As a {role.replace('_', ' ')}, you don't have access "
                       f"to the analytical claims/maintenance database. That "
                       f"data is restricted to billing and admin staff."),
            "sources": [], "retrieval_type": "sql_rag", "role": role,
        }

    cands = hybrid_search(client, question, role=role, candidates=candidates)
    if not cands:
        return {"answer": _refusal(role), "sources": [],
                "retrieval_type": "hybrid_rag", "role": role}

    top = rerank(question, cands, top_k=top_k)
    answer = generate_answer(question, top)
    sources = [
        {"source_document": r.chunk.source_document,
         "section_title": r.chunk.section_title,
         "collection": r.chunk.collection}
        for r in top
    ]
    return {"answer": answer, "sources": sources,
            "retrieval_type": "hybrid_rag", "role": role}
