"""
Phase 6A: authentication. Five demo users, bcrypt-hashed passwords (bcrypt
library directly -- avoids the passlib/bcrypt version bug), role-carrying JWT.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings

_ALGO = "HS256"
_TOKEN_TTL_HOURS = 12


def _hash(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())


def _verify(pw: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(pw.encode("utf-8"), hashed)


_RAW_USERS = {
    "dr.mehta":    ("doctor-pass",   "doctor"),
    "nurse.priya": ("nurse-pass",    "nurse"),
    "billing.ravi": ("billing-pass", "billing_executive"),
    "tech.anand":  ("tech-pass",     "technician"),
    "admin.sys":   ("admin-pass",    "admin"),
}

USERS = {
    u: {"hash": _hash(pw), "role": role}
    for u, (pw, role) in _RAW_USERS.items()
}

DEMO_CREDENTIALS = {u: {"password": pw, "role": role}
                    for u, (pw, role) in _RAW_USERS.items()}


def authenticate(username: str, password: str) -> str | None:
    rec = USERS.get(username)
    if not rec or not _verify(password, rec["hash"]):
        return None
    return rec["role"]


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGO)


def decode_role(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGO])
        return payload.get("role")
    except JWTError:
        return None
