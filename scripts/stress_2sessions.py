#!/usr/bin/env python3
"""P3: 2 路实时 + 离线模型常驻的轻量稳定性压测。

每 30 秒给两个会话各送一段 4 秒音频（/humanaudio），
每 10 秒记录 active / GPU；结果写 /tmp/p3_stress.json。
"""
import argparse
import asyncio
import json
import ssl
import subprocess
import time
from pathlib import Path

import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription

SSL_CTX = ssl._create_unverified_context()


def gpu_mb() -> int:
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        text=True,
    ).strip().splitlines()[0]
    return int(out)


async def request_json(url, method="GET", **kwargs):
    connector = aiohttp.TCPConnector(ssl=SSL_CTX)
    async with aiohttp.ClientSession(connector=connector) as s:
        async with s.request(method, url, **kwargs) as r:
            return r.status, await r.json(content_type=None)


async def connect(tag: str, base: str):
    pc = RTCPeerConnection()
    pc.addTransceiver("video", direction="recvonly")
    pc.addTransceiver("audio", direction="recvonly")

    @pc.on("track")
    def on_track(track):
        async def consume():
            try:
                while True:
                    await track.recv()
            except Exception:
                pass
        asyncio.create_task(consume())

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    status, data = await request_json(
        base + "/offer",
        method="POST",
        json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
    )
    if status != 200 or data.get("code") == -1:
        await pc.close()
        raise RuntimeError(f"{tag} rejected: {status} {data}")
    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=data["sdp"], type=data["type"])
    )
    print(f"{tag} session={data['sessionid']}", flush=True)
    return pc, data["sessionid"]


async def send_audio(base: str, sid: str, audio: bytes) -> int:
    form = aiohttp.FormData()
    form.add_field("file", audio, filename="clip.wav", content_type="audio/wav")
    form.add_field("sessionid", sid)
    status, _ = await request_json(base + "/humanaudio", method="POST", data=form)
    return status


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--interval", type=float, default=30)
    ap.add_argument("--url", default="https://127.0.0.1:8010")
    ap.add_argument("--audio", default="/tmp/p3_clip.wav")
    args = ap.parse_args()

    audio = Path(args.audio).read_bytes()
    started = time.time()
    deadline = started + args.minutes * 60
    max_gpu = 0
    max_active = 0
    sessions_created = 0
    reconnects = 0
    audio_ok = 0
    audio_fail = 0
    errors = []
    pcs = []
    sids = []
    last_send = 0.0
    last_progress = 0.0

    async def ensure_two():
        nonlocal pcs, sids, sessions_created, reconnects
        _, st = await request_json(args.url + "/api/live/status")
        if int(st.get("data", {}).get("active", 0)) >= 2:
            return
        for pc in pcs:
            await pc.close()
        pcs, sids = [], []
        reconnects += 1
        for i in range(2):
            pc, sid = await connect(f"client{i+1}", args.url)
            pcs.append(pc)
            sids.append(sid)
            sessions_created += 1
            await asyncio.sleep(2)

    await ensure_two()
    while time.time() < deadline:
        now = time.time()
        try:
            _, st = await request_json(args.url + "/api/live/status")
            active = int(st.get("data", {}).get("active", 0))
            used = gpu_mb()
            max_active = max(max_active, active)
            max_gpu = max(max_gpu, used)
            if active < 2:
                errors.append(f"active={active} at {round(now-started)}s")
                await ensure_two()
            if now - last_send >= args.interval:
                for sid in list(sids):
                    try:
                        code = await send_audio(args.url, sid, audio)
                        if code == 200:
                            audio_ok += 1
                        else:
                            audio_fail += 1
                            errors.append(f"humanaudio HTTP {code}")
                    except Exception as exc:  # noqa: BLE001
                        audio_fail += 1
                        errors.append(f"humanaudio: {exc}")
                last_send = now
            if now - last_progress >= 60:
                print(
                    f"{round(now-started)}s active={active} gpu={used}MB "
                    f"max={max_gpu}MB ok={audio_ok} fail={audio_fail}",
                    flush=True,
                )
                last_progress = now
        except Exception as exc:  # noqa: BLE001
            errors.append(f"loop: {exc}")
            await asyncio.sleep(5)
        await asyncio.sleep(10)

    for pc in pcs:
        await pc.close()
    await asyncio.sleep(3)
    try:
        _, final = await request_json(args.url + "/api/live/status")
    except Exception:
        final = {}

    result = {
        "minutes": args.minutes,
        "started": started,
        "elapsed_s": round(time.time() - started, 1),
        "max_gpu_mb": max_gpu,
        "max_active": max_active,
        "sessions_created": sessions_created,
        "reconnects": reconnects,
        "audio_ok": audio_ok,
        "audio_fail": audio_fail,
        "errors": errors[-20:],
        "final_status": final,
    }
    Path("/tmp/p3_stress.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print("RESULT " + json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
