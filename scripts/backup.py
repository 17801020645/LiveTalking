#!/usr/bin/env python3
"""SQLite + 关键配置备份，保留最近 N 天。"""
from __future__ import annotations
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST_ROOT = Path(os.environ.get("BACKUP_DIR", str(ROOT / "data" / "backups")))
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "7"))

DATA_ROOT = Path(os.environ.get("DATA_ROOT", str(ROOT / "data")))
SOURCES = [
    DATA_ROOT / "platform.db",
    DATA_ROOT / "offline" / "jobs.db",
]


def backup_sqlite(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_con = sqlite3.connect(str(src))
    dst_con = sqlite3.connect(str(dst))
    try:
        src_con.backup(dst_con)
        return True
    finally:
        dst_con.close()
        src_con.close()


def main() -> dict:
    ts = time.strftime("%Y%m%d-%H%M%S")
    dest = DEST_ROOT / ts
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"created_at": ts, "files": []}
    for src in SOURCES:
        rel = src.relative_to(ROOT)
        dst = dest / rel.name
        if backup_sqlite(src, dst):
            manifest["files"].append({"source": str(rel), "size": dst.stat().st_size})
    for cfg in ("config.yaml", "requirements.txt"):
        src = ROOT / cfg
        if src.is_file():
            shutil.copy2(src, dest / cfg)
            manifest["files"].append({"source": cfg, "size": (dest / cfg).stat().st_size})
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    cutoff = time.time() - RETENTION_DAYS * 86400
    removed = []
    for child in DEST_ROOT.iterdir():
        if child.is_dir() and child.stat().st_mtime < cutoff:
            shutil.rmtree(child, ignore_errors=True)
            removed.append(child.name)
    manifest["removed"] = removed
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    main()
