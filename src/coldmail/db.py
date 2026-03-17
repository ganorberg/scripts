from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from coldmail.config import DB_PATH
from coldmail.models import Lead

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    company_name TEXT,
    title TEXT,
    company_size TEXT,
    source TEXT,
    campaign_id TEXT,
    verified_status TEXT DEFAULT 'unverified',
    uploaded_to_instantly INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_verified_status ON leads(verified_status);
CREATE INDEX IF NOT EXISTS idx_campaign_id ON leads(campaign_id);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(path)
    conn.executescript(SCHEMA)
    conn.close()


def insert_leads(leads: list[Lead], db_path: Optional[Path] = None) -> tuple[int, int]:
    """Insert leads, skipping duplicates. Returns (inserted, skipped)."""
    conn = get_connection(db_path)
    inserted = 0
    skipped = 0
    for lead in leads:
        try:
            conn.execute(
                """INSERT INTO leads (email, first_name, last_name, company_name,
                   title, company_size, source, campaign_id, verified_status,
                   uploaded_to_instantly)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    lead.email,
                    lead.first_name,
                    lead.last_name,
                    lead.company_name,
                    lead.title,
                    lead.company_size,
                    lead.source,
                    lead.campaign_id,
                    lead.verified_status,
                    int(lead.uploaded_to_instantly),
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    conn.close()
    return inserted, skipped


def get_unverified_leads(
    limit: int, campaign_id: Optional[str] = None, db_path: Optional[Path] = None
) -> list[dict]:
    conn = get_connection(db_path)
    if campaign_id:
        rows = conn.execute(
            "SELECT * FROM leads WHERE verified_status = 'unverified' AND campaign_id = ? LIMIT ?",
            (campaign_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM leads WHERE verified_status = 'unverified' LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_verified_status(email: str, status: str, db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    conn.execute(
        "UPDATE leads SET verified_status = ?, updated_at = datetime('now') WHERE email = ?",
        (status, email),
    )
    conn.commit()
    conn.close()


def get_uploadable_leads(campaign_id: str, db_path: Optional[Path] = None) -> list[dict]:
    """Get verified leads not yet uploaded for a campaign."""
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT * FROM leads
           WHERE campaign_id = ?
           AND verified_status = 'ok'
           AND uploaded_to_instantly = 0""",
        (campaign_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_uploaded(emails: list[str], db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    for email in emails:
        conn.execute(
            "UPDATE leads SET uploaded_to_instantly = 1, updated_at = datetime('now') "
            "WHERE email = ?",
            (email,),
        )
    conn.commit()
    conn.close()


def get_stats(db_path: Optional[Path] = None) -> dict:
    conn = get_connection(db_path)
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    by_status = conn.execute(
        "SELECT verified_status, COUNT(*) as cnt FROM leads GROUP BY verified_status"
    ).fetchall()
    uploaded = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE uploaded_to_instantly = 1"
    ).fetchone()[0]
    by_campaign = conn.execute(
        "SELECT campaign_id, COUNT(*) as cnt FROM leads GROUP BY campaign_id"
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "by_status": {row["verified_status"]: row["cnt"] for row in by_status},
        "uploaded": uploaded,
        "by_campaign": {row["campaign_id"]: row["cnt"] for row in by_campaign},
    }
