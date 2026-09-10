###############################################################################
#  CORS: same-origin + current Host + LIVETALKING_CORS_ORIGINS allowlist
###############################################################################

import os

from aiohttp import web

ALLOW_HEADERS = "Authorization, Content-Type, Cookie, X-Requested-With, Accept"
ALLOW_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
EXPOSE_HEADERS = "Content-Type, Content-Length"


def parse_cors_origins(raw=None):
    text = raw if raw is not None else os.environ.get("LIVETALKING_CORS_ORIGINS", "")
    return {item.strip().rstrip("/") for item in text.split(",") if item.strip()}


def request_origin(request) -> str:
    host = request.host
    proto = request.headers.get("X-Forwarded-Proto") or request.scheme or "http"
    proto = proto.split(",")[0].strip()
    return f"{proto}://{host}".rstrip("/")


def origin_allowed(request, origin: str) -> bool:
    if not origin:
        return False
    origin = origin.rstrip("/")
    if origin == request_origin(request):
        return True
    extra = set(request.app.get("cors_origins") or [])
    extra |= parse_cors_origins()
    return origin in extra


def apply_cors_headers(request, resp):
    origin = (request.headers.get("Origin") or "").strip()
    if not origin or not origin_allowed(request, origin):
        return resp
    resp.headers["Access-Control-Allow-Origin"] = origin.rstrip("/")
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Headers"] = ALLOW_HEADERS
    resp.headers["Access-Control-Allow-Methods"] = ALLOW_METHODS
    resp.headers["Access-Control-Expose-Headers"] = EXPOSE_HEADERS
    resp.headers["Vary"] = "Origin"
    return resp


@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
        apply_cors_headers(request, resp)
        return resp
    resp = await handler(request)
    apply_cors_headers(request, resp)
    return resp
