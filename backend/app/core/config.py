"""
Core configuration and the canonical RBAC mapping.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str
    jwt_secret: str
    groq_model: str = "llama-3.3-70b-versatile"

    qdrant_path: str = "./qdrant_data"

    dense_model: str = "BAAI/bge-small-en-v1.5"
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"

    collection_name: str = "medibot_docs"


settings = Settings()

COLLECTION_ACCESS: dict[str, list[str]] = {
    "general":   ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "clinical":  ["doctor", "admin"],
    "nursing":   ["nurse", "doctor", "admin"],
    "billing":   ["billing_executive", "admin"],
    "equipment": ["technician", "admin"],
}

ALL_ROLES = ["doctor", "nurse", "billing_executive", "technician", "admin"]

SQL_RAG_ROLES = {"billing_executive", "admin"}


def collections_for_role(role: str) -> list[str]:
    """Return the list of collection names a given role may read."""
    return [c for c, roles in COLLECTION_ACCESS.items() if role in roles]


def roles_for_collection(collection: str) -> list[str]:
    """Return the access_roles list to stamp on a chunk from this collection."""
    return COLLECTION_ACCESS[collection]
