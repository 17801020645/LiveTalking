"""生产基线中间件：安全头、同源校验、登录限速、Cookie Secure。"""
from __future__ import annotations

import os
import threading
import time

from aiohttp import web

LOGIN_PATH = "/api/v1/auth/login"
MAX_FAILS = int(os.environ.get("LOGIN_MAX_FAILS", "5"))
WINDOW = int(os.environ.get("LOGIN_WINDOW_SECONDS", "300"))
BLOCK = int(os.environ.get("LOGIN_BLOCK_SECONDS", "300"))
TRUST_PROXY = os.environ.get("TRUST_PROXY", "0") == "1"
HSTS = os.environ.get("PROD_HSTS", "0") == "1"

_fails: dict[str, list[float]] = {}
_blocked: dict[str, float] = {}
_lock = threading.Lock()


def _client_ip(request: web.Request) -> str:
    if TRUST_PROXY:
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
    return request.remote or "unknown"


def _key(request: web.Request) -> str:
    return f"{_client_ip(request)}|{request.path}"


def is_secure(request: web.Request) -> bool:
    if request.secure:
        return True
    if TRUST_PROXY and request.headers.get("X-Forwarded-Proto", "").lower() == "https":
        return True
    return os.environ.get("NEXUS_COOKIE_SECURE", "0") == "1"


def _rate_state(key: str):
    now = time.time()
    with _lock:
        blocked_until = _blocked.get(key, 0)
        if blocked_until > now:
            return False, int(blocked_until - now)
        if blocked_until:
            _blocked.pop(key, None)
        hits = [t for t in _fails.get(key, []) if now - t < WINDOW]
        _fails[key] = hits
        return True, 0


def _record_fail(key: str) -> None:
    now = time.time()
    with _lock:
        hits = [t for t in _fails.get(key, []) if now - t < WINDOW]
        hits.append(now)
        _fails[key] = hits
        if len(hits) >= MAX_FAILS:
            _blocked[key] = now + BLOCK


def _clear(key: str) -> None:
    with _lock:
        _fails.pop(key, None)
        _blocked.pop(key, None)


def _same_origin(request: web.Request) -> bool:
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return True
    origin = request.headers.get("Origin")
    if not origin:
        return True  # curl/server-to-server；浏览器跨站会带 Origin
    host = request.headers.get("Host", "")
    if TRUST_PROXY:
        host = request.headers.get("X-Forwarded-Host", host)
    proto = "https" if is_secure(request) else "http"
    allowed = {f"{proto}://{host}", f"https://{host}", f"http://{host}"}
    return origin in allowed


@web.middleware
async def prod_security_middleware(request: web.Request, handler):
    key = _key(request)
    if request.path == LOGIN_PATH and request.method == "POST":
        ok, wait = _rate_state(key)
        if not ok:
            return web.json_response(
                {"code": -1, "msg": f"登录尝试过多，请 {wait} 秒后再试"},
                status=429,
                headers={"Retry-After": str(wait)},
            )
    if not _same_origin(request):
        return web.json_response({"code": -1, "msg": "cross-origin request rejected"}, status=403)

    resp = await handler(request)

    if request.path == LOGIN_PATH and request.method == "POST":
        if resp.status == 401:
            _record_fail(key)
        elif 200 <= resp.status < 300:
            _clear(key)

    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Permissions-Policy", "microphone=(self), camera=(), geolocation=()")
    resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resp.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self' ws: wss:; "
        "font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
    if HSTS and is_secure(request):
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.path.startswith("/api/") or request.path in ("/healthz", "/readyz"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp
