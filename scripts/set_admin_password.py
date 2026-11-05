#!/usr/bin/env python3
"""设置管理员密码；未提供 NEXUS_ADMIN_PASSWORD 时生成随机密码并只打印一次。"""
from __future__ import annotations
import os
import secrets
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from server.platform_auth import hash_password  # noqa: E402

username = os.environ.get("NEXUS_ADMIN_USER", "admin")
password = os.environ.get("NEXUS_ADMIN_PASSWORD") or secrets.token_urlsafe(18)
db_path = os.path.join(ROOT, "data", "platform.db")
con = sqlite3.connect(db_path)
cur = con.execute("UPDATE users SET password_hash=? WHERE username=?", (hash_password(password), username))
con.commit()
if cur.rowcount == 0:
    print(f"用户不存在: {username}", file=sys.stderr)
    raise SystemExit(1)
print(f"用户 {username} 密码已更新")
print(f"新密码（只显示一次）: {password}")
