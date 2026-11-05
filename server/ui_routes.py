"""Serve the React console and proxy offline APIs from the live process.

Keeps UI, live signaling and offline API on one HTTPS origin, avoiding CORS and
mixed-content issues. The offline service itself stays an independent process.
"""

from __future__ import annotations

import glob
import os

from aiohttp import ClientSession, ClientTimeout, web
from PIL import Image

from utils.logger import logger

VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 · 女声", "gender": "female", "provider": "edge"},
    {"id": "zh-CN-YunxiNeural", "name": "云希 · 男声", "gender": "male", "provider": "edge"},
    {"id": "zh-CN-YunxiaNeural", "name": "云夏 · 男声", "gender": "male", "provider": "edge"},
    {"id": "zh-CN-XiaoyiNeural", "name": "晓伊 · 女声", "gender": "female", "provider": "edge"},
]


async def list_avatars(request):
    root = os.path.join("data", "avatars")
    result = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            full = os.path.join(root, name, "full_imgs")
            if not os.path.isdir(full):
                continue
            files = sorted(glob.glob(os.path.join(full, "*.png")) + glob.glob(os.path.join(full, "*.jpg")))
            if not files:
                continue
            try:
                with Image.open(files[0]) as im:
                    width, height = im.size
            except Exception:
                width, height = 0, 0
            result.append({
                "id": name,
                "frames": len(files),
                "width": width,
                "height": height,
                "active": name == "avatar_ck",
            })
    return web.json_response({"code": 0, "msg": "ok", "data": result})


async def avatar_frame(request):
    avatar_id = request.match_info["avatar_id"]
    root = os.path.join("data", "avatars", avatar_id, "full_imgs")
    if not os.path.isdir(root):
        return web.Response(status=404, text="avatar not found")
    files = sorted(glob.glob(os.path.join(root, "*.png")) + glob.glob(os.path.join(root, "*.jpg")))
    if not files:
        return web.Response(status=404, text="frame not found")
    return web.FileResponse(files[0], headers={"Cache-Control": "public, max-age=300"})


async def list_voices(request):
    return web.json_response({"code": 0, "msg": "ok", "data": VOICES})


async def proxy_offline(request):
    target = "http://127.0.0.1:8012" + request.path_qs
    data = None if request.method in ("GET", "HEAD") else await request.read()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "connection", "accept-encoding")
    }
    timeout = ClientTimeout(total=300)
    async with ClientSession(timeout=timeout) as session:
        async with session.request(request.method, target, data=data, headers=headers) as resp:
            out_headers = {}
            for key in ("Content-Type", "Content-Disposition", "Cache-Control"):
                if key in resp.headers:
                    out_headers[key] = resp.headers[key]
            out = web.StreamResponse(status=resp.status, reason=resp.reason, headers=out_headers)
            await out.prepare(request)
            if request.method != "HEAD":
                async for chunk in resp.content.iter_chunked(64 * 1024):
                    await out.write(chunk)
            await out.write_eof()
            return out


async def console_redirect(request):
    raise web.HTTPFound("/console/")


def setup_ui_routes(app, ui_dist: str = "ui_dist") -> None:
    app.router.add_get("/console", console_redirect)
    app.router.add_get("/api/assets/avatars", list_avatars)
    app.router.add_get("/api/assets/avatars/{avatar_id}/frame", avatar_frame)
    app.router.add_get("/api/assets/voices", list_voices)
    app.router.add_route("*", "/api/offline/{tail:.*}", proxy_offline)
    index_file = os.path.join(ui_dist, "index.html")

    async def console_index(request):
        if not os.path.exists(index_file):
            return web.Response(status=404, text="UI not built")
        return web.FileResponse(index_file, headers={"Cache-Control": "no-store"})

    app.router.add_get("/console/", console_index)
    if os.path.isdir(ui_dist):
        app.router.add_static("/console/", path=ui_dist, show_index=False)
        logger.info("[UI] console enabled at /console/ (%s)", os.path.abspath(ui_dist))
    else:
        logger.warning("[UI] %s not found; /console/ disabled", ui_dist)
