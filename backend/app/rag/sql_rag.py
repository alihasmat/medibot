"""
Phase 5: SQL RAG over mediassist.db (NL -> SQL -> clean -> execute -> NL).
Restricted to billing_executive and admin (enforced in API layer).
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from app.core.config import settings
from app.rag.llm import complete

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "mediassist.db"

SCHEMA_PROMPT = """You write SQLite queries for the MediAssist operations database.

Table: claims (85 rows) -- billing/insurance claims
  claim_id TEXT PK, patient_id TEXT, patient_name TEXT,
  department TEXT,        -- one of: nephrology, cardiology, neurology,
                          --   gynaecology, orthopaedics, general_medicine, emergency
  claim_type TEXT,        -- one of: reimbursement, cashless
  diagnosis_code TEXT,    -- ICD-10 codes e.g. 'I21.4'
  insurer TEXT,           -- e.g. 'Bajaj Allianz', 'Star Health', 'HDFC Ergo'
  claimed_amount REAL, approved_amount REAL,
  status TEXT,            -- one of: pending, approved, rejected, submitted, escalated
  submitted_date TEXT,    -- 'YYYY-MM-DD'
  resolved_date TEXT      -- 'YYYY-MM-DD' or NULL

Table: maintenance_tickets (78 rows) -- equipment maintenance
  ticket_id TEXT PK, equipment_name TEXT, equipment_id TEXT,
  category TEXT,          -- one of: sterilisation, infusion, radiology,
                          --   monitoring, surgical, laboratory
  campus TEXT,
  issue_type TEXT,        -- one of: preventive_maintenance, sensor_failure,
                          --   battery_replacement, fault_reported, calibration_due
  fault_code TEXT, raised_by TEXT,
  raised_date TEXT,       -- 'YYYY-MM-DD'
  resolved_date TEXT,     -- 'YYYY-MM-DD' or NULL
  status TEXT,            -- one of: in_progress, resolved, escalated, open
  resolution_note TEXT

RULES:
- All status/category/type values are lowercase. Match them exactly.
- Dates are TEXT in 'YYYY-MM-DD'. Use string comparison or strftime().
- Return ONLY the SQL statement. No markdown, no explanation, no trailing
  semicolon needed. SELECT queries only."""

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|pragma)\b",
    re.IGNORECASE,
)


def clean_sql(raw: str) -> str:
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE).strip("`").strip()
    if "SQLQuery:" in raw:
        raw = raw.split("SQLQuery:")[-1].strip()
    raw = raw.split(";")[0].strip()
    return raw


def _run_sql(sql: str):
    if _FORBIDDEN.search(sql) or not sql.lower().lstrip().startswith("select"):
        raise ValueError("Only read-only SELECT queries are permitted.")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, rows
    finally:
        conn.close()


def sql_rag_chain(question: str) -> dict:
    raw_sql = complete(system=SCHEMA_PROMPT, user=f"Question: {question}\nSQL:")
    sql = clean_sql(raw_sql)

    try:
        cols, rows = _run_sql(sql)
    except Exception as e:
        return {"answer": f"I couldn't run a valid query for that question. ({e})",
                "sql": sql}

    result_preview = (
        "columns: " + ", ".join(cols) + "\nrows: " + repr(rows[:50])
        if rows else "The query returned no rows."
    )
    answer = complete(
        system=("You are a MediAssist operations analyst. Answer the user's "
                "question in one or two clear sentences using ONLY the SQL "
                "result. Include the relevant numbers."),
        user=f"Question: {question}\nSQL: {sql}\nResult:\n{result_preview}\n\nAnswer:",
    )
    return {"answer": answer.strip(), "sql": sql}
