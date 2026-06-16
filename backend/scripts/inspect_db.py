"""
Phase 5 step 0: inspect mediassist.db so we build the SQL chain against the
REAL schema (table names, columns, types, and sample values/formats).
    uv run python backend/scripts/inspect_db.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "mediassist.db"


def main():
    print(f"DB: {DB_PATH}\n")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()]
    print("Tables:", tables, "\n")

    for t in tables:
        print("=" * 60)
        print(f"TABLE: {t}")
        print("-- columns --")
        for cid, name, ctype, notnull, dflt, pk in cur.execute(
                f"PRAGMA table_info({t})").fetchall():
            print(f"  {name:24s} {ctype:10s}"
                  f"{' PK' if pk else ''}{' NOT NULL' if notnull else ''}")

        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"-- row count: {n} --")

        print("-- 3 sample rows --")
        cols = [d[0] for d in cur.execute(f"SELECT * FROM {t} LIMIT 1").description]
        for row in cur.execute(f"SELECT * FROM {t} LIMIT 3").fetchall():
            print("  " + " | ".join(f"{c}={v!r}" for c, v in zip(cols, row)))

        # distinct values for low-cardinality columns (helps the LLM know
        # exact string formats like 'Escalated' vs 'escalated')
        print("-- distinct values in likely-categorical columns --")
        for cid, name, ctype, *_ in cur.execute(f"PRAGMA table_info({t})").fetchall():
            distinct = cur.execute(
                f"SELECT COUNT(DISTINCT {name}) FROM {t}").fetchone()[0]
            if distinct <= 15:
                vals = [r[0] for r in cur.execute(
                    f"SELECT DISTINCT {name} FROM {t} "
                    f"WHERE {name} IS NOT NULL LIMIT 15").fetchall()]
                print(f"  {name}: {vals}")
        print()

    conn.close()


if __name__ == "__main__":
    main()
