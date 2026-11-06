"""轻量 Prometheus 指标；不引入额外依赖。"""
from __future__ import annotations

import threading
import time

_started = time.time()
_lock = threading.Lock()
_counters: dict[tuple[str, str, str], int] = {}
_duration_sum: dict[tuple[str, str], float] = {}
_duration_count: dict[tuple[str, str], int] = {}


def _normalize(path: str) -> str:
    if path.startswith("/api/offline/jobs/"):
        return "/api/offline/jobs/{id}"
    if path.startswith("/record/"):
        return "/record/{id}"
    return path


def record(method: str, path: str, status: int, seconds: float) -> None:
    path = _normalize(path)
    with _lock:
        key = (method, path, str(status))
        _counters[key] = _counters.get(key, 0) + 1
        dk = (method, path)
        _duration_sum[dk] = _duration_sum.get(dk, 0.0) + seconds
        _duration_count[dk] = _duration_count.get(dk, 0) + 1


def render(active_sessions: int) -> str:
    lines = [
        "# HELP nexus_live_sessions_active Active WebRTC sessions",
        "# TYPE nexus_live_sessions_active gauge",
        f"nexus_live_sessions_active {active_sessions}",
        "# HELP nexus_process_start_time_seconds Process start time",
        "# TYPE nexus_process_start_time_seconds gauge",
        f"nexus_process_start_time_seconds {_started:.3f}",
        "# HELP nexus_http_requests_total HTTP requests",
        "# TYPE nexus_http_requests_total counter",
    ]
    with _lock:
        for (method, path, status), value in sorted(_counters.items()):
            lines.append(
                f'nexus_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}'
            )
        lines.append("# HELP nexus_http_request_duration_seconds_sum HTTP request duration sum")
        lines.append("# TYPE nexus_http_request_duration_seconds_sum counter")
        for (method, path), value in sorted(_duration_sum.items()):
            lines.append(
                f'nexus_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {value:.6f}'
            )
        lines.append("# HELP nexus_http_request_duration_seconds_count HTTP request duration count")
        lines.append("# TYPE nexus_http_request_duration_seconds_count counter")
        for (method, path), value in sorted(_duration_count.items()):
            lines.append(
                f'nexus_http_request_duration_seconds_count{{method="{method}",path="{path}"}} {value}'
            )
    return "\n".join(lines) + "\n"


def middleware_factory():
    from aiohttp import web

    @web.middleware
    async def metrics_middleware(request: web.Request, handler):
        t0 = time.perf_counter()
        resp = await handler(request)
        if request.path != "/metrics":
            record(request.method, request.path, resp.status, time.perf_counter() - t0)
        return resp

    return metrics_middleware
