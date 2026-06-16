"""
Phase 6D: FastAPI app -- /login, /chat, /collections/{role}, /health.
Run from medibot root (ingestion must NOT be running):
    uv run uvicorn app.api.main:app --reload --app-dir backend
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import collections_for_role, ALL_ROLES
from app.core.security import authenticate, create_token, decode_role
from app.retrieval.vector_store import get_client
from app.rag.pipeline import answer_question

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["client"] = get_client()
    yield
    _state.clear()


app = FastAPI(title="MediBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    question: str


def current_role(authorization: str = Header(default="")) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    role = decode_role(token) if token else None
    if not role:
        raise HTTPException(status_code=401, detail="Invalid or missing token.")
    return role


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(req: LoginRequest):
    role = authenticate(req.username, req.password)
    if not role:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return {"token": create_token(req.username, role), "role": role,
            "collections": collections_for_role(role)}


@app.get("/collections/{role}")
def collections(role: str):
    if role not in ALL_ROLES:
        raise HTTPException(status_code=404, detail="Unknown role.")
    return {"role": role, "collections": collections_for_role(role)}


@app.post("/chat")
def chat(req: ChatRequest, role: str = Depends(current_role)):
    return answer_question(_state["client"], req.question, role)
