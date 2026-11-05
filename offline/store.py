"""离线任务存储（SQLite）。"""

from __future__ import annotations

import os
import sqlite3
import time
import uuid

DB_PATH = os.environ.get("OFFLINE_DB", "data/offline/jobs.db")

FIELDS = {
    "status",
    "text",
    "avatar_id",
    "voice",
    "output_path",
    "error",
    "progress",
    "started_at",
    "finished_at",
    "subtitle",
    "bgm",
    "cover",
    "srt_path",
    "cover_path",
    "qc_status",
    "qc_json",
    "stage",
}


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _connect()
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                text TEXT NOT NULL,
                avatar_id TEXT NOT NULL,
                voice TEXT NOT NULL,
                output_path TEXT,
                error TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                started_at REAL,
                finished_at REAL
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, created_at)")
        cols = {row[1] for row in con.execute("PRAGMA table_info(jobs)")}
        migrations = {
            "subtitle": "INTEGER NOT NULL DEFAULT 1",
            "bgm": "TEXT NOT NULL DEFAULT ''",
            "cover": "INTEGER NOT NULL DEFAULT 1",
            "srt_path": "TEXT",
            "cover_path": "TEXT",
            "qc_status": "TEXT",
            "qc_json": "TEXT",
            "stage": "TEXT",
        }
        for name, ddl in migrations.items():
            if name not in cols:
                con.execute(f"ALTER TABLE jobs ADD COLUMN {name} {ddl}")
        con.commit()
    finally:
        con.close()


def create_job(
    text: str,
    avatar_id: str,
    voice: str,
    subtitle: bool = True,
    bgm: str = "",
    cover: bool = True,
) -> str:
    job_id = uuid.uuid4().hex
    con = _connect()
    try:
        con.execute(
            "INSERT INTO jobs(id, status, text, avatar_id, voice, subtitle, bgm, cover, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                "pending",
                text,
                avatar_id,
                voice,
                int(bool(subtitle)),
                bgm or "",
                int(bool(cover)),
                time.time(),
            ),
        )
        con.commit()
    finally:
        con.close()
    return job_id


def get_job(job_id: str) -> dict | None:
    con = _connect()
    try:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def list_jobs(limit: int = 50) -> list[dict]:
    con = _connect()
    try:
        rows = con.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def claim_next() -> dict | None:
    con = _connect()
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT * FROM jobs WHERE status='pending' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            con.commit()
            return None
        con.execute(
            "UPDATE jobs SET status='running', started_at=?, progress=0 WHERE id=?",
            (time.time(), row["id"]),
        )
        con.commit()
        job = dict(row)
        job["status"] = "running"
        job["progress"] = 0
        return job
    finally:
        con.close()


def update_job(job_id: str, **fields) -> None:
    bad = set(fields) - FIELDS
    if bad:
        raise ValueError(f"invalid fields: {bad}")
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    con = _connect()
    try:
        con.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), job_id))
        con.commit()
    finally:
        con.close()


def reset_stale() -> int:
    con = _connect()
    try:
        cur = con.execute(
            "UPDATE jobs SET status='failed', error='worker restarted', finished_at=? "
            "WHERE status='running'",
            (time.time(),),
        )
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def counts() -> dict:
    con = _connect()
    try:
        rows = con.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}
    finally:
        con.close()
