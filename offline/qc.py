"""离线视频质检：人脸丢失、黑帧、闪烁、SyncNet 口型一致性。

- 人脸：YuNet（models/face_detection_yunet.onnx）
- 黑帧：灰度均值/标准差
- 闪烁：相邻采样帧平均绝对差
- 口型：SyncNet（models/syncnet/syncnet_v2.model）；`lip_corr` 是辅助启发式
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Optional

import cv2
import librosa
import numpy as np

YUNET_PATH = os.path.join("models", "face_detection_yunet.onnx")
_DETECTOR = None
_SYNC_SCORER = None


def _sync_scorer():
    global _SYNC_SCORER
    if _SYNC_SCORER is None and os.path.exists("models/syncnet/syncnet_v2.model"):
        from offline.syncnet import SyncNetScorer

        _SYNC_SCORER = SyncNetScorer()
    return _SYNC_SCORER


def _detector():
    global _DETECTOR
    if _DETECTOR is None and os.path.exists(YUNET_PATH):
        _DETECTOR = cv2.FaceDetectorYN_create(
            YUNET_PATH, "", (320, 320), 0.6, 0.3, 5000
        )
    return _DETECTOR


def _best_lag_corr(a: list[float], b: list[float], max_lag: int = 2) -> float:
    best = 0.0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[lag:], b[: len(a) - lag]
        else:
            x, y = a[: len(b) + lag], b[-lag:]
        c = _pearson(x, y)
        if c > best:
            best = c
    return best


def _pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 5:
        return 0.0
    x = np.asarray(a[:n], dtype=np.float32)
    y = np.asarray(b[:n], dtype=np.float32)
    if x.std() < 1e-6 or y.std() < 1e-6:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def run_qc(
    video_path: str,
    audio_path: Optional[str] = None,
    sample_fps: float = 5.0,
) -> dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"cannot open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    step = max(1, int(round(fps / max(0.5, sample_fps))))

    if audio_path and os.path.exists(audio_path):
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    else:
        tmp_wav = tempfile.mktemp(suffix=".wav")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-nostdin",
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    video_path,
                    "-vn",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    tmp_wav,
                ],
                check=True,
            )
            audio, sr = librosa.load(tmp_wav, sr=16000, mono=True)
        finally:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass
    samples = 0
    face_missing = 0
    black = 0
    flicker = 0
    motions: list[float] = []
    rms_for_motion: list[float] = []
    prev_small = None
    prev_mouth = None
    idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step != 0:
            idx += 1
            continue

        t = idx / fps
        samples += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small_bgr = cv2.resize(
            frame, (320, max(1, int(320 * frame.shape[0] / frame.shape[1])))
        )
        small = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2GRAY)
        small_f = small.astype(np.float32)

        faces = []
        det = _detector()
        if det is not None:
            det.setInputSize((small_bgr.shape[1], small_bgr.shape[0]))
            _, dets = det.detect(small_bgr)
            if dets is not None:
                scale = frame.shape[1] / small_bgr.shape[1]
                faces = [
                    (
                        int(d[0] * scale),
                        int(d[1] * scale),
                        int(d[2] * scale),
                        int(d[3] * scale),
                    )
                    for d in dets
                ]
        if not faces:
            try:
                import face_recognition

                locs = face_recognition.face_locations(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                )
                faces = [(left, top, right - left, bottom - top) for (top, right, bottom, left) in locs]
            except Exception:
                faces = []

        if not faces:
            face_missing += 1
            prev_mouth = None
        else:
            X, Y, W, H = max(faces, key=lambda f: int(f[2]) * int(f[3]))
            mouth = gray[
                Y + int(H * 0.55) : Y + H,
                X : X + int(W * 0.8),
            ]
            if mouth.size:
                mouth = cv2.resize(mouth, (64, 32)).astype(np.float32)
                if prev_mouth is not None:
                    motions.append(float(np.mean(np.abs(mouth - prev_mouth))))
                    a0 = int(t * sr)
                    a1 = int((t + 1.0 / sample_fps) * sr)
                    seg = audio[a0:a1]
                    rms_for_motion.append(
                        float(np.sqrt(np.mean(seg**2))) if len(seg) else 0.0
                    )
                prev_mouth = mouth

        mean = float(gray.mean())
        std = float(gray.std())
        if mean < 12 or std < 3:
            black += 1

        if prev_small is not None:
            diff = float(np.mean(np.abs(small_f - prev_small)))
            if diff > 18:
                flicker += 1
        prev_small = small_f
        idx += 1

    cap.release()

    if samples == 0:
        raise ValueError("no frames sampled")

    face_ratio = face_missing / samples
    black_ratio = black / samples
    flicker_ratio = flicker / samples
    lip_corr = _best_lag_corr(motions, rms_for_motion)

    status = "pass"
    reasons = []
    warnings = []
    if face_ratio > 0.15:
        status = "fail"
        reasons.append(f"face_missing={face_ratio:.2f}")
    elif face_ratio > 0.05:
        status = "warn"
        reasons.append(f"face_missing={face_ratio:.2f}")

    if black_ratio > 0.05:
        status = "fail"
        reasons.append(f"black_frames={black_ratio:.2f}")
    elif black_ratio > 0.01:
        if status == "pass":
            status = "warn"
        reasons.append(f"black_frames={black_ratio:.2f}")

    if flicker_ratio > 0.05:
        status = "fail" if status == "fail" else "warn"
        reasons.append(f"flicker={flicker_ratio:.2f}")
    elif flicker_ratio > 0.02 and status == "pass":
        status = "warn"
        reasons.append(f"flicker={flicker_ratio:.2f}")

    if lip_corr < 0.05:
        warnings.append(f"lip_corr_low={lip_corr:.2f} (heuristic)")

    syncnet = {"status": "not_available"}
    try:
        scorer = _sync_scorer()
        if scorer is not None:
            s = scorer.score(video_path, audio_path)
            conf = float(s["confidence"])
            off = int(s["av_offset"])
            short = (len(audio) / sr) < 5.0
            if short:
                # 短视频的 offset 估计不稳定，放宽到 ±12 帧
                if conf >= 0.30 and abs(off) <= 12:
                    s_status = "pass"
                elif conf >= 0.20 and abs(off) <= 14:
                    s_status = "warn"
                else:
                    s_status = "fail"
            else:
                if conf >= 0.30 and abs(off) <= 5:
                    s_status = "pass"
                elif conf >= 0.20 and abs(off) <= 8:
                    s_status = "warn"
                else:
                    s_status = "fail"
            syncnet = {
                "status": s_status,
                "confidence": round(conf, 4),
                "av_offset": off,
            }
            if s_status == "fail":
                status = "fail"
                reasons.append(f"syncnet={conf:.2f}/offset={off}")
            elif s_status == "warn":
                if status == "pass":
                    status = "warn"
                reasons.append(f"syncnet={conf:.2f}/offset={off}")
    except Exception as exc:  # noqa: BLE001
        syncnet = {"status": "error", "error": str(exc)[:300]}

    result = {
        "status": status,
        "reasons": reasons,
        "warnings": warnings,
        "samples": samples,
        "face_missing_ratio": round(face_ratio, 4),
        "black_ratio": round(black_ratio, 4),
        "flicker_ratio": round(flicker_ratio, 4),
        "lip_corr": round(lip_corr, 4),
        "fps": round(float(fps), 2),
        "duration": round(float(len(audio) / sr), 2),
        "syncnet": syncnet,
    }
    return result


def save_qc(result: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
