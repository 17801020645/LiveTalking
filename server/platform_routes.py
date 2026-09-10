###############################################################################
#  /api/v1 platform routes + /app SPA + startup hook
###############################################################################

import os
import sqlite3
import time
from pathlib import Path

from aiohttp import web

from server.platform_auth import (
    bootstrap_admin,
    create_session,
    delete_session,
    hash_password,
    json_error,
    json_ok,
    platform_auth_middleware,
    require_admin,
    require_user,
    verify_password,
)
from server.platform_catalog import avatar_public_dict, resolve_media, scan_avatars
from server.platform_db import COOKIE_NAME, SESSION_DAYS, close_db, connect_db


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
DEFAULT_DB = os.path.join("data", "platform.db")
DEFAULT_AVATARS = os.path.join("data", "avatars")


async def init_platform(app):
    db_path = app.get("platform_db_path") or os.environ.get("LIVETALKING_PLATFORM_DB", DEFAULT_DB)
    avatars_dir = app.get("avatars_dir") or os.environ.get("LIVETALKING_AVATARS_DIR", DEFAULT_AVATARS)
    db = await connect_db(db_path)
    app["platform_db"] = db
    app["avatars_dir"] = avatars_dir
    if "uploads_dir" not in app:
        app["uploads_dir"] = os.path.join("data", "uploads", "orders")
    os.makedirs(app["uploads_dir"], exist_ok=True)
    if "fake_avatar_tasks" not in app:
        app["fake_avatar_tasks"] = os.environ.get("LIVETALKING_FAKE_AVATAR_TASK") == "1"
    await bootstrap_admin(db)
    n = await scan_avatars(db, avatars_dir)
    import asyncio
    app["loop"] = asyncio.get_running_loop()
    from server.task_manager import task_manager
    from server.platform_orders import handle_generation_task

    def _on_task(task):
        loop = app.get("loop")
        if loop:
            asyncio.run_coroutine_threadsafe(handle_generation_task(app, task), loop)

    task_manager.on_status = _on_task
    app.setdefault("user_rtc_sessions", {})
    from utils.logger import logger
    logger.info(f"[platform] db={db_path} avatars_dir={avatars_dir} scanned_new={n}")


async def shutdown_platform(app):
    db = app.get("platform_db")
    if db is not None:
        await close_db(db)


def _user_row(row):
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


async def login(request):
    try:
        body = await request.json()
    except Exception:
        return json_error("无效请求")
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        from server.platform_auth import LOGIN_ERROR
        return json_error(LOGIN_ERROR, status=401)
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT id, username, role, status, password_hash FROM users WHERE username = ?",
        (username,),
    ) as cur:
        row = await cur.fetchone()
    from server.platform_auth import LOGIN_ERROR
    if not row or row["status"] != "active" or not verify_password(password, row["password_hash"]):
        return json_error(LOGIN_ERROR, status=401)
    token = await create_session(db, row["id"])
    resp = json_ok({"id": row["id"], "username": row["username"], "role": row["role"]})
    resp.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="Lax",
        path="/",
        max_age=SESSION_DAYS * 86400,
    )
    return resp


async def logout(request):
    token = request.cookies.get(COOKIE_NAME, "")
    await delete_session(request.app["platform_db"], token)
    resp = json_ok()
    resp.del_cookie(COOKIE_NAME, path="/")
    return resp


async def me(request):
    user = request["user"]
    return json_ok({"id": user["id"], "username": user["username"], "role": user["role"]})


async def admin_list_users(request):
    denied = require_admin(request)
    if denied:
        return denied
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT id, username, role, status, created_at FROM users ORDER BY id ASC"
    ) as cur:
        rows = await cur.fetchall()
    return json_ok({"users": [_user_row(r) for r in rows]})


async def admin_create_user(request):
    denied = require_admin(request)
    if denied:
        return denied
    try:
        body = await request.json()
    except Exception:
        return json_error("无效请求")
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if len(username) < 3:
        return json_error("用户名至少 3 个字符")
    if len(password) < 6:
        return json_error("密码至少 6 个字符")
    db = request.app["platform_db"]
    try:
        cur = await db.execute(
            "INSERT INTO users (username, password_hash, role, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), "user", "active", time.time()),
        )
        await db.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return json_error("用户名已存在")
    return json_ok({"id": user_id, "username": username, "role": "user", "status": "active"})


async def admin_disable_user(request):
    denied = require_admin(request)
    if denied:
        return denied
    user_id = int(request.match_info["user_id"])
    if request["user"]["id"] == user_id:
        return json_error("不能禁用当前登录账号")
    db = request.app["platform_db"]
    await db.execute("UPDATE users SET status = ? WHERE id = ? AND role = ?", ("disabled", user_id, "user"))
    await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    await db.commit()
    return json_ok()


async def admin_list_avatars(request):
    denied = require_admin(request)
    if denied:
        return denied
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT avatar_id, name, cover_path, preview_path, status FROM avatars ORDER BY avatar_id"
    ) as cur:
        rows = await cur.fetchall()
    return json_ok({"avatars": [avatar_public_dict(r, request) for r in rows]})


async def admin_list_user_subs(request):
    denied = require_admin(request)
    if denied:
        return denied
    user_id = int(request.match_info["user_id"])
    db = request.app["platform_db"]
    async with db.execute(
        """
        SELECT a.avatar_id, a.name, a.cover_path, a.preview_path, a.status, s.is_published
        FROM subscriptions s
        JOIN avatars a ON a.avatar_id = s.avatar_id
        WHERE s.user_id = ?
        ORDER BY a.avatar_id
        """,
        (user_id,),
    ) as cur:
        rows = await cur.fetchall()
    return json_ok({"subscriptions": [avatar_public_dict(r, request) for r in rows]})


async def admin_bind(request):
    denied = require_admin(request)
    if denied:
        return denied
    user_id = int(request.match_info["user_id"])
    try:
        body = await request.json()
    except Exception:
        return json_error("无效请求")
    avatar_id = (body.get("avatar_id") or "").strip()
    if not avatar_id:
        return json_error("缺少 avatar_id")
    db = request.app["platform_db"]
    async with db.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)) as cur:
        user = await cur.fetchone()
    if not user:
        return json_error("用户不存在", status=404)
    if user["role"] != "user":
        return json_error("只能给普通用户绑定形象")
    async with db.execute("SELECT avatar_id FROM avatars WHERE avatar_id = ?", (avatar_id,)) as cur:
        avatar = await cur.fetchone()
    if not avatar:
        return json_error("形象不存在", status=404)
    try:
        await db.execute(
            "INSERT INTO subscriptions (user_id, avatar_id, is_published, created_at) VALUES (?, ?, 0, ?)",
            (user_id, avatar_id, time.time()),
        )
        await db.commit()
    except Exception:
        return json_error("已经绑定过该形象")
    return json_ok()


async def admin_unbind(request):
    denied = require_admin(request)
    if denied:
        return denied
    user_id = int(request.match_info["user_id"])
    avatar_id = request.match_info["avatar_id"]
    db = request.app["platform_db"]
    await db.execute(
        "DELETE FROM subscriptions WHERE user_id = ? AND avatar_id = ?",
        (user_id, avatar_id),
    )
    await db.commit()
    return json_ok()


async def me_avatars(request):
    user = request["user"]
    db = request.app["platform_db"]
    async with db.execute(
        """
        SELECT a.avatar_id, a.name, a.cover_path, a.preview_path, a.status, s.is_published
        FROM subscriptions s
        JOIN avatars a ON a.avatar_id = s.avatar_id
        WHERE s.user_id = ?
        ORDER BY a.avatar_id
        """,
        (user["id"],),
    ) as cur:
        rows = await cur.fetchall()
    return json_ok({"avatars": [avatar_public_dict(r, request) for r in rows]})


async def me_home(request):
    user = request["user"]
    db = request.app["platform_db"]
    async with db.execute(
        """
        SELECT a.avatar_id, a.name, a.cover_path, a.preview_path, a.status, s.is_published
        FROM subscriptions s
        JOIN avatars a ON a.avatar_id = s.avatar_id
        WHERE s.user_id = ? AND s.is_published = 1
        """,
        (user["id"],),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return json_ok({"published": None})
    return json_ok({"published": avatar_public_dict(row, request)})


async def me_publish(request):
    user = request["user"]
    if user["role"] != "user":
        return json_error("仅普通用户可发布到首页", status=403)
    avatar_id = request.match_info["avatar_id"]
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT id FROM subscriptions WHERE user_id = ? AND avatar_id = ?",
        (user["id"], avatar_id),
    ) as cur:
        sub = await cur.fetchone()
    if not sub:
        return json_error("形象不存在", status=404)
    await db.execute("UPDATE subscriptions SET is_published = 0 WHERE user_id = ?", (user["id"],))
    await db.execute(
        "UPDATE subscriptions SET is_published = 1 WHERE user_id = ? AND avatar_id = ?",
        (user["id"], avatar_id),
    )
    await db.commit()
    return json_ok()


async def me_unpublish(request):
    user = request["user"]
    if user["role"] != "user":
        return json_error("仅普通用户可取消发布", status=403)
    avatar_id = request.match_info["avatar_id"]
    db = request.app["platform_db"]
    cur = await db.execute(
        "UPDATE subscriptions SET is_published = 0 WHERE user_id = ? AND avatar_id = ?",
        (user["id"], avatar_id),
    )
    await db.commit()
    if cur.rowcount == 0:
        return json_error("形象不存在", status=404)
    return json_ok()


async def me_offer(request):
    denied = require_user(request)
    if denied:
        return denied
    user = request["user"]
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT avatar_id FROM subscriptions WHERE user_id = ? AND is_published = 1",
        (user["id"],),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return json_error("请先在资产页发布一个数字人")
    published = row["avatar_id"]
    live = request.app.setdefault("user_rtc_sessions", {})
    if live.get(user["id"]):
        return json_error("已有进行中的连麦，请先断开")
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    params = dict(body)
    params["avatar"] = published
    rtc = request.app.get("rtc_manager")
    if rtc is None or request.app.get("fake_avatar_tasks"):
        sid = f"u{user['id']}-{int(time.time() * 1000)}"
        live[user["id"]] = sid
        request.app["last_me_offer"] = {
            "avatar": published,
            "client_avatar": body.get("avatar"),
            "user_id": user["id"],
        }
        return json_ok({"sdp": "ok", "type": "answer", "sessionid": sid, "avatar_id": published})
    if not params.get("sdp") or not params.get("type"):
        return json_error("缺少 SDP")
    data, err = await rtc.answer_offer(params)
    if err:
        return json_error(err, status=503)
    live[user["id"]] = data["sessionid"]
    data["avatar_id"] = published
    return json_ok(data)


async def me_hangup(request):
    denied = require_user(request)
    if denied:
        return denied
    user = request["user"]
    live = request.app.setdefault("user_rtc_sessions", {})
    sid = live.pop(user["id"], None)
    if sid and not request.app.get("fake_avatar_tasks"):
        from server.session_manager import session_manager
        session_manager.remove_session(sid)
    return json_ok()


async def _can_access_avatar(request, avatar_id: str) -> bool:
    user = request["user"]
    if user["role"] == "admin":
        return True
    db = request.app["platform_db"]
    async with db.execute(
        "SELECT 1 FROM subscriptions WHERE user_id = ? AND avatar_id = ?",
        (user["id"], avatar_id),
    ) as cur:
        return await cur.fetchone() is not None


def _guess_ctype(path: str):
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
    }.get(ext, "application/octet-stream")


async def media_cover(request):
    avatar_id = request.match_info["avatar_id"]
    if not await _can_access_avatar(request, avatar_id):
        return json_error("形象不存在", status=404)
    cover, _, _ = resolve_media(request.app["avatars_dir"], avatar_id)
    if not cover or not os.path.isfile(cover):
        return json_error("无封面", status=404)
    return web.FileResponse(cover, headers={"Content-Type": _guess_ctype(cover)})


async def media_preview(request):
    avatar_id = request.match_info["avatar_id"]
    if not await _can_access_avatar(request, avatar_id):
        return json_error("形象不存在", status=404)
    _, preview, _ = resolve_media(request.app["avatars_dir"], avatar_id)
    if not preview or not os.path.isfile(preview):
        return json_error("无预览", status=404)
    return web.FileResponse(preview, headers={"Content-Type": _guess_ctype(preview)})


async def spa_index(request):
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        return web.Response(
            status=503,
            text="frontend/dist 不存在，请在 frontend/ 执行 npm install && npm run build",
        )
    return web.FileResponse(index)


async def spa_fallback(request):
    rel = request.match_info.get("path", "")
    if rel.startswith("assets/"):
        asset = FRONTEND_DIST / rel
        if asset.is_file():
            return web.FileResponse(asset)
        return web.Response(status=404, text="not found")
    return await spa_index(request)


def setup_v1_routes(app):
    app.router.add_post("/api/v1/auth/login", login)
    app.router.add_post("/api/v1/auth/logout", logout)
    app.router.add_get("/api/v1/auth/me", me)
    app.router.add_get("/api/v1/admin/users", admin_list_users)
    app.router.add_post("/api/v1/admin/users", admin_create_user)
    app.router.add_post("/api/v1/admin/users/{user_id}/disable", admin_disable_user)
    app.router.add_get("/api/v1/admin/avatars", admin_list_avatars)
    app.router.add_get("/api/v1/admin/users/{user_id}/subscriptions", admin_list_user_subs)
    app.router.add_post("/api/v1/admin/users/{user_id}/subscriptions", admin_bind)
    app.router.add_delete("/api/v1/admin/users/{user_id}/subscriptions/{avatar_id}", admin_unbind)
    app.router.add_get("/api/v1/me/avatars", me_avatars)
    app.router.add_get("/api/v1/me/home", me_home)
    app.router.add_post("/api/v1/me/avatars/{avatar_id}/publish", me_publish)
    app.router.add_post("/api/v1/me/avatars/{avatar_id}/unpublish", me_unpublish)
    app.router.add_post("/api/v1/me/offer", me_offer)
    app.router.add_post("/api/v1/me/hangup", me_hangup)
    app.router.add_get("/api/v1/media/avatars/{avatar_id}/cover", media_cover)
    app.router.add_get("/api/v1/media/avatars/{avatar_id}/preview", media_preview)
    from server.platform_orders import setup_order_routes
    setup_order_routes(app)


def setup_frontend_routes(app):
    app.router.add_get("/app", spa_index)
    app.router.add_get("/app/", spa_index)
    app.router.add_get("/app/{path:.*}", spa_fallback)


def create_test_application(db_path, avatars_dir, web_dir=None, uploads_dir=None):
    """Lightweight app for tests: platform APIs + anonymous legacy stubs."""
    app = web.Application(middlewares=[platform_auth_middleware])
    app["platform_db_path"] = db_path
    app["avatars_dir"] = avatars_dir
    app["fake_avatar_tasks"] = True
    if uploads_dir:
        app["uploads_dir"] = uploads_dir
    setup_v1_routes(app)
    setup_frontend_routes(app)

    async def offer(_request):
        return web.json_response({"sdp": "ok"})

    async def avatar_task(request):
        denied = require_admin(request)
        if denied:
            return denied
        return web.json_response({"code": 0, "msg": "ok", "data": {"task_id": "t"}})

    async def human(request):
        body = await request.json()
        request.app["last_human"] = body
        return web.json_response({"code": 0, "msg": "ok"})

    app.router.add_post("/offer", offer)
    app.router.add_post("/api/avatar/task", avatar_task)
    app.router.add_post("/human", human)
    if web_dir:
        from server.routes import index
        app.router.add_get("/", index)
        app.router.add_static("/", path=web_dir)
    app.on_startup.append(init_platform)
    app.on_cleanup.append(shutdown_platform)
    return app


def attach_platform(app):
    """Register /api/v1 and /app before setup_routes() so they win over static /."""
    if platform_auth_middleware not in app.middlewares:
        app.middlewares.append(platform_auth_middleware)
    setup_v1_routes(app)
    setup_frontend_routes(app)
    if init_platform not in app.on_startup:
        app.on_startup.append(init_platform)
    if shutdown_platform not in app.on_cleanup:
        app.on_cleanup.append(shutdown_platform)
