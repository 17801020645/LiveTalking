###############################################################################
#  Platform SQLite: users, sessions, avatars, subscriptions
###############################################################################

import asyncio
import os
import sqlite3

COOKIE_NAME = "lt_session"
SESSION_DAYS = 7

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    cover_path TEXT,
    preview_path TEXT,
    status TEXT NOT NULL DEFAULT 'ready',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    avatar_id TEXT NOT NULL,
    is_published INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    UNIQUE(user_id, avatar_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    material_type TEXT NOT NULL,
    video_path TEXT,
    image_path TEXT,
    audio_path TEXT,
    script_text TEXT NOT NULL DEFAULT '',
    reject_reason TEXT NOT NULL DEFAULT '',
    result_avatar_id TEXT,
    task_id TEXT,
    admin_id INTEGER,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
"""


class _Cursor:
    def __init__(self, rows, lastrowid, rowcount):
        self._rows = list(rows)
        self._i = 0
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    async def fetchone(self):
        if self._i >= len(self._rows):
            return None
        row = self._rows[self._i]
        self._i += 1
        return row

    async def fetchall(self):
        rest = self._rows[self._i:]
        self._i = len(self._rows)
        return rest

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Execute:
    def __init__(self, db, sql, params):
        self._db = db
        self._sql = sql
        self._params = params

    def __await__(self):
        return self._run().__await__()

    async def _run(self):
        async with self._db._lock:
            cur = self._db._conn.execute(self._sql, self._params)
            rows = cur.fetchall()
            return _Cursor(rows, cur.lastrowid, cur.rowcount)

    async def __aenter__(self):
        return await self._run()

    async def __aexit__(self, *exc):
        return False


class Database:
    def __init__(self, path: str):
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._lock = asyncio.Lock()

    def execute(self, sql, params=()):
        return _Execute(self, sql, params)

    async def executescript(self, sql):
        async with self._lock:
            self._conn.executescript(sql)

    async def commit(self):
        async with self._lock:
            self._conn.commit()

    async def close(self):
        async with self._lock:
            self._conn.close()


async def connect_db(path: str) -> Database:
    return Database(path)


async def close_db(db: Database):
    await db.close()
