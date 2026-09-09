###############################################################################
#  Password hashing, session cookies, auth middleware
###############################################################################

import hashlib
import hmac
import os
import secrets
import time

from aiohttp import web

from server.platform_db import COOKIE_NAME, SESSION_DAYS

PBKDF2_ITERATIONS = 210_000
LOGIN_ERROR = "用户名或密码错误"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_s, salt_hex, digest_hex = stored.split("$", 3)
        if algo != "pbkdf2":
            return False
        iterations = int(iter_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _public_path(path: str, method: str) -> bool:
    if path == "/api/v1/auth/login" and method == "POST":
        return True
    return not path.startswith("/api/v1/")


async def load_user_by_token(db, token: str):
    if not token:
        return None
    now = time.time()
    async with db.execute(
        """
        SELECT u.id, u.username, u.role, u.status
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ?
        """,
        (token, now),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return None
    if row["status"] != "active":
        return None
    return {"id": row["id"], "username": row["username"], "role": row["role"], "status": row["status"]}


def json_error(msg: str, code: int = -1, status: int = 400):
    return web.json_response({"code": code, "msg": msg}, status=status)


def json_ok(data=None, status: int = 200):
    body = {"code": 0, "msg": "ok"}
    if data is not None:
        body["data"] = data
    return web.json_response(body, status=status)


@web.middleware
async def platform_auth_middleware(request, handler):
    if _public_path(request.path, request.method):
        return await handler(request)
    db = request.app.get("platform_db")
    if db is None:
        return json_error("platform not ready", status=503)
    token = request.cookies.get(COOKIE_NAME, "")
    user = await load_user_by_token(db, token)
    if not user:
        return json_error("未登录", status=401)
    request["user"] = user
    return await handler(request)


async def create_session(db, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    expires = now + SESSION_DAYS * 86400
    await db.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now, expires),
    )
    await db.commit()
    return token


async def delete_session(db, token: str):
    if not token:
        return
    await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()


async def bootstrap_admin(db):
    async with db.execute("SELECT COUNT(*) AS n FROM users") as cur:
        row = await cur.fetchone()
    if row["n"] > 0:
        return False
    username = (os.environ.get("LIVETALKING_BOOTSTRAP_ADMIN") or "").strip()
    password = os.environ.get("LIVETALKING_BOOTSTRAP_PASSWORD") or ""
    if not username or not password:
        from utils.logger import logger
        logger.warning(
            "[platform] 用户表为空且未设置 LIVETALKING_BOOTSTRAP_ADMIN / "
            "LIVETALKING_BOOTSTRAP_PASSWORD，管理端无法登录"
        )
        return False
    await db.execute(
        "INSERT INTO users (username, password_hash, role, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, hash_password(password), "admin", "active", time.time()),
    )
    await db.commit()
    from utils.logger import logger
    logger.info(f"[platform] 已创建引导管理员: {username}")
    return True


def require_admin(request):
    user = request.get("user")
    if not user or user["role"] != "admin":
        return json_error("需要管理员权限", status=403)
    return None
