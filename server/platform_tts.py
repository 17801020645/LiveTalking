###############################################################################
#  Admin TTS proxy: 8010 → Omni (default http://127.0.0.1:8091)
###############################################################################

import json
import os

import aiohttp
from aiohttp import web

from server.platform_auth import json_error, json_ok, require_admin

DEFAULT_UPSTREAM = "http://127.0.0.1:8091"
VOICES_TIMEOUT = aiohttp.ClientTimeout(total=15, connect=10, sock_connect=10)
SPEECH_TIMEOUT = aiohttp.ClientTimeout(total=60, connect=10, sock_connect=10)
UNAVAILABLE = "TTS 上游不可用"


def tts_upstream(request) -> str:
    env = (os.environ.get("LIVETALKING_TTS_UPSTREAM") or "").strip()
    if env:
        return env.rstrip("/")
    opt = request.app.get("opt")
    server = ""
    if opt is not None:
        server = (getattr(opt, "TTS_SERVER", None) or "").strip()
    return (server or DEFAULT_UPSTREAM).rstrip("/")


def _json_msg(body: bytes, fallback=UNAVAILABLE):
    try:
        data = json.loads(body.decode("utf-8") or "{}")
        if isinstance(data, dict):
            return str(data.get("detail") or data.get("message") or data.get("msg") or fallback)
    except Exception:
        pass
    return fallback


async def admin_tts_voices(request):
    denied = require_admin(request)
    if denied:
        return denied
    url = f"{tts_upstream(request)}/v1/audio/voices"
    try:
        async with aiohttp.ClientSession(timeout=VOICES_TIMEOUT) as session:
            async with session.get(url) as resp:
                body = await resp.read()
                if resp.status >= 500 or resp.status < 0:
                    return json_error(UNAVAILABLE, status=502)
                if resp.status >= 400:
                    return json_error(_json_msg(body), status=resp.status)
                try:
                    data = json.loads(body.decode("utf-8"))
                except Exception:
                    return json_error(UNAVAILABLE, status=502)
                return json_ok(data)
    except (aiohttp.ClientError, TimeoutError, OSError):
        return json_error(UNAVAILABLE, status=502)


async def admin_tts_upload_voice(request):
    denied = require_admin(request)
    if denied:
        return denied
    url = f"{tts_upstream(request)}/v1/audio/voices"
    body = await request.read()
    headers = {}
    if request.content_type:
        headers["Content-Type"] = request.headers.get("Content-Type", request.content_type)
    try:
        async with aiohttp.ClientSession(timeout=SPEECH_TIMEOUT) as session:
            async with session.post(url, data=body, headers=headers) as resp:
                upstream = await resp.read()
                if resp.status >= 500:
                    return json_error(UNAVAILABLE, status=502)
                if resp.status >= 400:
                    return json_error(_json_msg(upstream), status=resp.status)
                try:
                    data = json.loads(upstream.decode("utf-8") or "{}")
                except Exception:
                    data = {"ok": True}
                return json_ok(data if isinstance(data, dict) else {"ok": True})
    except (aiohttp.ClientError, TimeoutError, OSError):
        return json_error(UNAVAILABLE, status=502)


async def admin_tts_delete_voice(request):
    denied = require_admin(request)
    if denied:
        return denied
    name = request.match_info["name"]
    url = f"{tts_upstream(request)}/v1/audio/voices/{name}"
    try:
        async with aiohttp.ClientSession(timeout=VOICES_TIMEOUT) as session:
            async with session.delete(url) as resp:
                body = await resp.read()
                if resp.status in (404, 405):
                    return json_error("服务器不支持删除操作，请手动管理", status=resp.status)
                if resp.status >= 500:
                    return json_error(UNAVAILABLE, status=502)
                if resp.status >= 400:
                    return json_error(_json_msg(body), status=resp.status)
                return json_ok({"deleted": name})
    except (aiohttp.ClientError, TimeoutError, OSError):
        return json_error(UNAVAILABLE, status=502)


async def admin_tts_speech(request):
    denied = require_admin(request)
    if denied:
        return denied
    try:
        payload = await request.json()
    except Exception:
        return json_error("无效的 JSON")
    url = f"{tts_upstream(request)}/v1/audio/speech"
    try:
        async with aiohttp.ClientSession(timeout=SPEECH_TIMEOUT) as session:
            async with session.post(url, json=payload) as resp:
                body = await resp.read()
                if resp.status >= 500:
                    return json_error(UNAVAILABLE, status=502)
                if resp.status >= 400:
                    return json_error(_json_msg(body), status=resp.status)
                content_type = resp.content_type or "audio/mpeg"
                return web.Response(body=body, status=200, content_type=content_type)
    except (aiohttp.ClientError, TimeoutError, OSError):
        return json_error(UNAVAILABLE, status=502)


def setup_tts_routes(app):
    app.router.add_get("/api/v1/admin/tts/voices", admin_tts_voices)
    app.router.add_post("/api/v1/admin/tts/voices", admin_tts_upload_voice)
    app.router.add_delete("/api/v1/admin/tts/voices/{name}", admin_tts_delete_voice)
    app.router.add_post("/api/v1/admin/tts/speech", admin_tts_speech)
