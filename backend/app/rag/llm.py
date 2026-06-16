"""
Shared Groq LLM client. Used by both SQL RAG (Phase 5) and document RAG (Phase 6).
"""
from __future__ import annotations

from functools import lru_cache

from groq import Groq

from app.core.config import settings


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=settings.groq_api_key)


def complete(system: str, user: str, temperature: float = 0.0) -> str:
    resp = _client().chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content
