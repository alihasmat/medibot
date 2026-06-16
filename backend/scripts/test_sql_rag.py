"""
Phase 5 verification: sql_rag_chain on several analytical questions.
    uv run python backend/scripts/test_sql_rag.py
"""
from app.rag.sql_rag import sql_rag_chain

QUESTIONS = [
    "How many billing claims have been escalated?",
    "Which equipment category has the most open maintenance tickets?",
    "What is the total claimed amount for cardiology claims?",
    "How many maintenance tickets are still unresolved (not resolved)?",
    "Which insurer appears most often in the claims?",
    "What is the average approved amount for approved claims?",
]


def main():
    for q in QUESTIONS:
        print("=" * 70)
        print("Q:", q)
        out = sql_rag_chain(q)
        print("SQL:", out["sql"])
        print("A:", out["answer"])
        print()


if __name__ == "__main__":
    main()
