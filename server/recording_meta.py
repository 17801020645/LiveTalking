"""记录录制会话的租户归属。简单 JSON，够 POC 用。"""
from __future__ import annotations
import json, os, threading

META = os.path.join("data", "record", "sessions.json")
_LOCK = threading.Lock()


def _load() -> dict:
    try:
        with open(META, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(META), exist_ok=True)
    tmp = META + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, META)


def set_owner(session_id: str, tenant_id: str, username: str) -> None:
    with _LOCK:
        data = _load()
        data[session_id] = {"tenant_id": tenant_id or "default", "username": username}
        _save(data)


def get_owner(session_id: str) -> dict | None:
    with _LOCK:
        return _load().get(session_id)
