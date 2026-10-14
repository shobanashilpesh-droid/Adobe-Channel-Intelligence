"""Local SQLite case tracking. Demo-only; no Adobe orders or purchases are submitted."""
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "demo_cases.db"
STATUSES = ("OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED")


def connect():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY, case_type TEXT NOT NULL,
        customer_id TEXT, reseller_id TEXT, subscription_id TEXT,
        summary TEXT NOT NULL, owner TEXT NOT NULL,
        status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    )""")
    con.commit()
    return con


def create_case(case_type, customer_id, reseller_id, subscription_id, summary, owner="Ingram Operations"):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    case_id = "CASE-" + uuid.uuid4().hex[:8].upper()
    with connect() as con:
        con.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?)", (
            case_id, case_type, customer_id, reseller_id, subscription_id,
            summary, owner, "OPEN", now, now
        ))
    return case_id


def list_cases(reseller_id=None):
    with connect() as con:
        if reseller_id:
            rows = con.execute("SELECT * FROM cases WHERE reseller_id=? ORDER BY created_at DESC", (reseller_id,)).fetchall()
        else:
            rows = con.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def update_case(case_id, status):
    if status not in STATUSES:
        raise ValueError("Invalid case status")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as con:
        con.execute("UPDATE cases SET status=?,updated_at=? WHERE case_id=?", (status, now, case_id))
