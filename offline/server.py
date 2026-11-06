"""离线任务 API + 最小页面。

启动：
    python -m offline.server --port 8012
"""

from __future__ import annotations

import argparse
import os
import time
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


def _scope(request: web.Request) -> tuple[str, bool]:
    tenant = (request.headers.get("X-Tenant-Id") or "default").strip() or "default"
    return tenant, (request.headers.get("X-Role") or "user") == "admin"


def _allowed_job(request: web.Request, job_id: str):
    job = store.get_job(job_id)
    if job is None:
        return None, json_err("job not found", 404)
    tenant, is_admin = _scope(request)
    if not is_admin and (job.get("tenant_id") or "default") != tenant:
        return None, json_err("job not found", 404)
    return job, None


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


async def metrics(request: web.Request) -> web.Response:
    worker = request.app["worker"]
    counts = store.counts()
    total = sum(counts.values())
    lines = [
        "# HELP nexus_offline_jobs Number of jobs by status",
        "# TYPE nexus_offline_jobs gauge",
    ]
    for status, value in sorted(counts.items()):
        lines.append(f'nexus_offline_jobs{{status="{status}"}} {value}')
    lines += [
        "# HELP nexus_offline_jobs_total Total jobs",
        "# TYPE nexus_offline_jobs_total gauge",
        f"nexus_offline_jobs_total {total}",
        "# HELP nexus_offline_worker_busy Worker currently rendering",
        "# TYPE nexus_offline_worker_busy gauge",
        f"nexus_offline_worker_busy {1 if worker.busy else 0}",
        "# HELP nexus_offline_worker_alive Worker thread alive",
        "# TYPE nexus_offline_worker_alive gauge",
        f"nexus_offline_worker_alive {1 if worker.is_alive() else 0}",
    ]
    try:
        from offline import store as _store
        con = _store._connect()
        try:
            n = con.execute("SELECT COUNT(*) FROM jobs WHERE qc_status='pass'").fetchone()[0]
        finally:
            con.close()
        lines += [
            "# HELP nexus_offline_qc_pass_total Jobs passing QC",
            "# TYPE nexus_offline_qc_pass_total counter",
            f"nexus_offline_qc_pass_total {n}",
        ]
    except Exception:
        pass
    return web.Response(text="\n".join(lines)+"\n", content_type="text/plain; version=0.0.4")


async def healthz(request: web.Request) -> web.Response:
    worker: Worker = request.app["worker"]
    alive = worker.is_alive()
    return web.json_response(
        {"status": "ok" if alive else "degraded", "service": "nexus-offline",
         "worker_alive": alive, "counts": store.counts()},
        status=200 if alive else 503,
    )


async def list_jobs(request: web.Request) -> web.Response:
    tenant, is_admin = _scope(request)
    jobs = store.list_jobs(limit=50, tenant_id=None if is_admin else tenant)
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

    try:
        priority = max(0, min(2, int(body.get("priority", 0))))
    except (TypeError, ValueError):
        priority = 0

    tenant, _ = _scope(request)
    job_id = store.create_job(
        text,
        avatar_id,
        voice,
        subtitle=subtitle,
        bgm=bgm,
        cover=cover,
        priority=priority,
        tenant_id=tenant,
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
    job, err = _allowed_job(request, request.match_info["job_id"])
    if err:
        return err
    return json_ok(job)


async def retry_job(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    job, err = _allowed_job(request, job_id)
    if err:
        return err
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


async def cancel_job(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    job, err = _allowed_job(request, job_id)
    if err:
        return err
    if job["status"] == "pending":
        store.update_job(job_id, status="cancelled", stage=None, finished_at=time.time())
    elif job["status"] == "running":
        worker = request.app["worker"]
        worker.cancel_job(job_id)
    else:
        return json_err("only pending/running job can be cancelled")
    return json_ok({"id": job_id, "status": "cancelled"})


async def delete_job(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    job, err = _allowed_job(request, job_id)
    if err:
        return err
    if job["status"] in ("pending", "running"):
        return json_err("cancel the job before deleting it")
    for key in ("output_path", "cover_path", "srt_path"):
        path = job.get(key)
        if path:
            try:
                os.remove(path)
            except OSError:
                pass
    store.delete_job(job_id)
    return json_ok({"id": job_id, "deleted": True})


async def unload_models(request: web.Request) -> web.Response:
    worker = request.app["worker"]
    if not worker.unload_models():
        return json_err("worker is busy", 409)
    return json_ok({"unloaded": True})


async def download_asset(request: web.Request) -> web.StreamResponse:
    job, err = _allowed_job(request, request.match_info["job_id"])
    if err:
        return err
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
    job, err = _allowed_job(request, request.match_info["job_id"])
    if err:
        return err
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
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/metrics", metrics)
    app.router.add_get("/api/offline/health", health)
    app.router.add_get("/api/offline/jobs", list_jobs)
    app.router.add_post("/api/offline/jobs", create_job)
    app.router.add_get("/api/offline/jobs/{job_id}", get_job)
    app.router.add_post("/api/offline/jobs/{job_id}/retry", retry_job)
    app.router.add_post("/api/offline/jobs/{job_id}/cancel", cancel_job)
    app.router.add_delete("/api/offline/jobs/{job_id}", delete_job)
    app.router.add_post("/api/offline/unload", unload_models)
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
