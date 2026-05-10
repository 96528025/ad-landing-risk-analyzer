from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from backend.app.models import ScanResult


DB_PATH = Path(__file__).resolve().parents[3] / "storage" / "scans.sqlite3"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                requested_url TEXT NOT NULL,
                final_url TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )


def save_scan(result: ScanResult) -> ScanResult:
    init_db()
    payload = result.model_dump_json()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO scans (created_at, requested_url, final_url, risk_score, risk_level, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result.created_at.isoformat(),
                result.signals.requested_url,
                result.signals.final_url,
                result.risk.score,
                result.risk.level,
                payload,
            ),
        )
        result.id = int(cursor.lastrowid)
    return result


def list_scans(limit: int = 20) -> list[dict]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, created_at, requested_url, final_url, risk_score, risk_level
            FROM scans
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_scan(scan_id: int) -> ScanResult | None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT payload FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if not row:
        return None
    data = json.loads(row["payload"])
    data["created_at"] = datetime.fromisoformat(data["created_at"])
    data["id"] = scan_id
    return ScanResult.model_validate(data)
