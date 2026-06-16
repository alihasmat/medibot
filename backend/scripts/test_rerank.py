"""
Phase 4 verification: retrieve (top-10) -> rerank (top-3), with score logging.
    uv run python backend/scripts/test_rerank.py
"""
from app.retrieval.vector_store import get_client
from app.retrieval.retriever import hybrid_search
from app.retrieval.reranker import rerank


def run(client, query, role):
    print("=" * 70)
    print(f"ROLE: {role}  |  QUERY: {query}")
    candidates = hybrid_search(client, query, role=role, candidates=10)
    top = rerank(query, candidates, top_k=3, log=True)
    print(f"\n  Final {len(top)} chunks sent to LLM:")
    for r in top:
        print(f"    [{r.chunk.collection}] {r.chunk.source_document} "
              f"-- {r.chunk.section_title[:45]} (score {r.rerank_score:.3f})")
    print()


def main():
    client = get_client()
    run(client, "what is the protocol for managing STEMI?", "doctor")
    run(client, "correct IV cannula size for a paediatric patient under 5kg",
        "nurse")
    run(client, "ICD-10 code I21.0 package rate", "billing_executive")


if __name__ == "__main__":
    main()
