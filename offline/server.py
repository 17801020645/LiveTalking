"""离线任务 API + 最小页面。

启动：
    python -m offline.server --port 8012
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from aiohttp import web

from offline import store
from offline.worker import Worker

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "offline" / "web" / "index.html"


def json_ok(data=None, status: int = 200) -> web.Response:
    body = {"code": 0, "msg": "ok"}
    if data is not None:
        body["data"] = data
    return web.json_response(body, status=status)


def json_err(msg: str, status: int = 400) -> web.Response:
    return web.json_response({"code": -1, "msg": msg}, status=status)


async def index(request: web.Request) -> web.StreamResponse:
    return web.FileResponse(PAGE)


async def health(request: web.Request) -> web.Response:
    worker: Worker = request.app["worker"]
    return json_ok(
        {
            "worker_alive": worker.is_alive(),
            "counts": store.counts(),
        }
    )


async def list_jobs(request: web.Request) -> web.Response:
    jobs = store.list_jobs(limit=50)
    for job in jobs:
        job["text"] = (job.get("text") or "")[:80]
    return json_ok(jobs)


async def create_job(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        return json_err("invalid json")

    text = (body.get("text") or "").strip()
    avatar_id = (body.get("avatar_id") or "avatar_ck").strip()
    voice = (body.get("voice") or "zh-CN-XiaoxiaoNeural").strip()

    if not text:
        return json_err("text is required")
    if len(text) > 20000:
        return json_err("text too long (max 20000)")
    if not (ROOT / "data" / "avatars" / avatar_id).is_dir():
        return json_err(f"avatar not found: {avatar_id}")

    subtitle = bool(body.get("subtitle", True))
    cover = bool(body.get("cover", True))
    bgm = (body.get("bgm") or "").strip()
    if bgm:
        bgm = os.path.basename(bgm)
        if not (ROOT / "data" / "bgm" / bgm).is_file():
            return json_err(f"bgm not found: {bgm}")

    job_id = store.create_job(
        text,
        avatar_id,
        voice,
        subtitle=subtitle,
        bgm=bgm,
        cover=cover,
    )
    return json_ok({"id": job_id})


async def list_bgm(request: web.Request) -> web.Response:
    bgm_dir = ROOT / "data" / "bgm"
    files = []
    if bgm_dir.is_dir():
        files = sorted(
            p.name
            for p in bgm_dir.iterdir()
            if p.is_file() and p.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac")
        )
    return json_ok(files)


async def get_job(request: web.Request) -> web.Response:
    job = store.get_job(request.match_info["job_id"])
    if job is None:
        return json_err("job not found", 404)
    return json_ok(job)


async def retry_job(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    job = store.get_job(job_id)
    if job is None:
        return json_err("job not found", 404)
    if job["status"] not in ("failed", "success"):
        return json_err("only failed/success job can be retried")
    store.update_job(
        job_id,
        status="pending",
        error=None,
        progress=0,
        output_path=None,
        started_at=None,
        finished_at=None,
    )
    return json_ok({"id": job_id})


async def download_asset(request: web.Request) -> web.StreamResponse:
    job = store.get_job(request.match_info["job_id"])
    if job is None:
        return json_err("job not found", 404)
    kind = "cover" if request.path.endswith("/cover") else "subtitle"
    path = job.get("cover_path") if kind == "cover" else job.get("srt_path")
    if not path or not os.path.exists(path):
        return json_err(f"{kind} not ready", 404)
    suffix = ".jpg" if kind == "cover" else ".ass"
    return web.FileResponse(
        path,
        headers={
            "Content-Disposition": f'attachment; filename="{job["id"]}{suffix}"'
        },
    )


async def download_job(request: web.Request) -> web.StreamResponse:
    job = store.get_job(request.match_info["job_id"])
    if job is None:
        return json_err("job not found", 404)
    path = job.get("output_path")
    if job["status"] != "success" or not path or not os.path.exists(path):
        return json_err("output not ready", 404)
    return web.FileResponse(
        path,
        headers={"Content-Disposition": f'attachment; filename="{job["id"]}.mp4"'},
    )


def create_app(worker: Worker) -> web.Application:
    app = web.Application(client_max_size=2 * 1024 * 1024)
    app["worker"] = worker
    app.router.add_get("/", index)
    app.router.add_get("/api/offline/health", health)
    app.router.add_get("/api/offline/jobs", list_jobs)
    app.router.add_post("/api/offline/jobs", create_job)
    app.router.add_get("/api/offline/jobs/{job_id}", get_job)
    app.router.add_post("/api/offline/jobs/{job_id}/retry", retry_job)
    app.router.add_get("/api/offline/jobs/{job_id}/download", download_job)
    app.router.add_get("/api/offline/jobs/{job_id}/cover", download_asset)
    app.router.add_get("/api/offline/jobs/{job_id}/subtitle", download_asset)
    app.router.add_get("/api/offline/bgm", list_bgm)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline digital human API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8012)
    args = parser.parse_args()

    store.init_db()
    stale = store.reset_stale()
    if stale:
        print(f"[server] reset {stale} stale running jobs", flush=True)

    worker = Worker()
    worker.start()
    app = create_app(worker)
    print(f"[server] listening on {args.host}:{args.port}", flush=True)
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
