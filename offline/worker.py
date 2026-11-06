"""离线任务 worker：常驻进程，模型只加载一次。"""

from __future__ import annotations

import json
import os
import ssl
import sys
import threading
import time
import traceback
import urllib.request

from offline import store
from offline.qc import run_qc
from offline.render import OfflineRenderer, headline
from offline.tts import synthesize

LIVE_STATUS_URL = os.environ.get(
    "LIVE_STATUS_URL", "http://127.0.0.1:8010/api/live/status"
)
LIVE_IDLE_SECONDS = 15.0


class JobCancelled(Exception):
    pass


class Worker(threading.Thread):
    def __init__(self, poll_interval: float = 1.0, max_cached: int = 2) -> None:
        super().__init__(daemon=True, name="offline-worker")
        self.poll_interval = poll_interval
        self.max_cached = max_cached
        self.stop_event = threading.Event()
        self.renderers: dict[str, OfflineRenderer] = {}
        self.current_job_id: str | None = None
        self.cancel_event = threading.Event()
        self.busy = False
        self._lock = threading.Lock()

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        print("[worker] started", flush=True)
        while not self.stop_event.is_set():
            job = store.claim_next()
            if job is None:
                self.stop_event.wait(self.poll_interval)
                continue
            self.process(job)
        print("[worker] stopped", flush=True)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            if self.current_job_id == job_id:
                self.cancel_event.set()
                return True
        store.update_job(job_id, status="cancelled", stage=None, finished_at=time.time())
        return True

    def unload_models(self) -> bool:
        with self._lock:
            if self.busy:
                return False
            self.renderers.clear()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        print("[worker] models unloaded", flush=True)
        return True

    def _check_cancel(self) -> None:
        if self.cancel_event.is_set():
            raise JobCancelled("cancelled by user")

    def _wait_or_cancel(self, job_id: str) -> None:
        self._check_cancel()
        self._wait_live_idle(job_id)
        self._check_cancel()

    def _live_active(self) -> bool:
        try:
            kw = {}
            if LIVE_STATUS_URL.startswith("https://"):
                kw["context"] = ssl._create_unverified_context()
            with urllib.request.urlopen(LIVE_STATUS_URL, timeout=2, **kw) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return int((data.get("data") or {}).get("active") or 0) > 0
        except Exception as exc:  # noqa: BLE001
            print(f"[worker] live status unavailable: {exc}", file=sys.stderr, flush=True)
            return False

    def _wait_live_idle(self, job_id: str) -> None:
        """实时忙时阻塞；空闲后等 15 秒防抖，再放行。"""
        if not self._live_active():
            return
        store.update_job(job_id, stage="waiting_live")
        print(f"[worker] {job_id} waiting_live", flush=True)
        while not self.stop_event.is_set():
            self._check_cancel()
            if not self._live_active():
                idle_since = time.time()
                while time.time() - idle_since < LIVE_IDLE_SECONDS:
                    self._check_cancel()
                    if self.stop_event.is_set():
                        return
                    if self._live_active():
                        idle_since = time.time()
                    self.stop_event.wait(2)
                break
            self.stop_event.wait(3)
        store.update_job(job_id, stage=None)

    def _get_renderer(self, avatar_id: str) -> OfflineRenderer:
        if avatar_id in self.renderers:
            return self.renderers[avatar_id]
        if len(self.renderers) >= self.max_cached:
            self.renderers.clear()
        t0 = time.perf_counter()
        renderer = OfflineRenderer(avatar_id=avatar_id)
        print(
            f"[worker] loaded avatar={avatar_id} in {time.perf_counter() - t0:.2f}s",
            flush=True,
        )
        self.renderers[avatar_id] = renderer
        return renderer

    def process(self, job: dict) -> None:
        job_id = job["id"]
        avatar_id = job["avatar_id"]
        os.makedirs("data/offline/tmp", exist_ok=True)
        wav_path = os.path.join("data/offline/tmp", f"{job_id}.wav")
        output_path = os.path.join("data/offline", f"{job_id}.mp4")
        srt_path = (
            os.path.join("data/offline", f"{job_id}.ass")
            if job.get("subtitle")
            else None
        )
        cover_path = (
            os.path.join("data/offline", f"{job_id}.jpg")
            if job.get("cover")
            else None
        )
        bgm_path = None
        bgm_name = (job.get("bgm") or "").strip()
        if bgm_name:
            candidate = os.path.join("data/bgm", os.path.basename(bgm_name))
            if os.path.exists(candidate):
                bgm_path = candidate

        with self._lock:
            self.current_job_id = job_id
            self.cancel_event.clear()
            self.busy = True
        try:
            self._check_cancel()
            if not (job.get("text") or "").strip():
                raise ValueError("text is empty")

            t0 = time.perf_counter()
            synthesize(
                job["text"],
                job["voice"],
                wav_path,
                subtitle_path=srt_path,
            )
            print(f"[worker] {job_id} tts {time.perf_counter() - t0:.2f}s", flush=True)

            self._wait_or_cancel(job_id)
            renderer = self._get_renderer(avatar_id)

            last = [-1]

            def progress(done: int, total: int) -> None:
                pct = int(done * 100 / max(total, 1))
                if pct >= last[0] + 10:
                    last[0] = pct
                    store.update_job(job_id, progress=min(pct, 99))

            t0 = time.perf_counter()
            renderer.render(
                wav_path,
                output_path,
                progress=progress,
                segment_seconds=10.0,
                pause_check=lambda: self._wait_or_cancel(job_id),
                subtitle_path=srt_path if srt_path and os.path.exists(srt_path) else None,
                bgm_path=bgm_path,
                bgm_volume=0.12,
                cover_path=cover_path,
                cover_title=headline(job.get("text") or ""),
            )
            elapsed = time.perf_counter() - t0

            qc_status, qc_json = None, None
            try:
                t0 = time.perf_counter()
                qc = run_qc(output_path, wav_path)
                qc_status = qc.get("status")
                qc_json = json.dumps(qc, ensure_ascii=False)
                print(
                    f"[worker] {job_id} qc {qc_status} "
                    f"({time.perf_counter() - t0:.2f}s)",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                qc_status = "error"
                qc_json = json.dumps({"status": "error", "error": str(exc)[:500]}, ensure_ascii=False)
                print(f"[worker] {job_id} qc failed: {exc}", file=sys.stderr, flush=True)

            store.update_job(
                job_id,
                status="success",
                output_path=output_path,
                progress=100,
                error=None,
                finished_at=time.time(),
                srt_path=srt_path if srt_path and os.path.exists(srt_path) else None,
                cover_path=cover_path if cover_path and os.path.exists(cover_path) else None,
                qc_status=qc_status,
                qc_json=qc_json,
                stage=None,
            )
            print(f"[worker] {job_id} done in {elapsed:.2f}s -> {output_path}", flush=True)
        except JobCancelled:
            for path in (output_path, srt_path, cover_path):
                try:
                    if path:
                        os.remove(path)
                except OSError:
                    pass
            store.update_job(
                job_id,
                status="cancelled",
                error="cancelled by user",
                finished_at=time.time(),
                stage=None,
            )
            print(f"[worker] {job_id} cancelled", flush=True)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            store.update_job(
                job_id,
                status="failed",
                error=str(exc)[:1000],
                finished_at=time.time(),
                stage=None,
            )
            print(f"[worker] {job_id} failed: {exc}", file=sys.stderr, flush=True)
        finally:
            with self._lock:
                self.current_job_id = None
                self.busy = False
                self.cancel_event.clear()
            try:
                os.remove(wav_path)
            except OSError:
                pass
