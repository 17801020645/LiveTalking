"""离线数字人 CLI。

用法：
    python -m offline.cli --text "你好，我是数字人。" --avatar-id avatar_ck --output data/offline/demo.mp4
    python -m offline.cli --text-file script.txt --avatar-id avatar_ck
    python -m offline.cli --audio input.wav --avatar-id avatar_ck --output out.mp4
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time

from offline.qc import run_qc, save_qc
from offline.render import OfflineRenderer, headline
from offline.tts import synthesize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="离线数字人：文字/音频 → MP4")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", type=str, help="要播报的文案")
    src.add_argument("--text-file", type=str, help="从文件读取文案")
    src.add_argument("--audio", type=str, help="已有音频（wav/mp3），跳过 TTS")

    parser.add_argument("--avatar-id", type=str, default="avatar_ck")
    parser.add_argument("--voice", type=str, default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--segment-seconds", type=float, default=0.0,
                        help="长音频分段长度；0=自动（取形象时长，最多 30s）")
    parser.add_argument("--overlap-seconds", type=float, default=0.0,
                        help="已弃用：镜像循环不使用交叉淡化")
    parser.add_argument("--no-subtitle", action="store_true", help="不生成/不烧录字幕")
    parser.add_argument("--bgm", type=str, default="", help="背景音乐路径（mp3/wav）")
    parser.add_argument("--bgm-volume", type=float, default=0.12, help="BGM 音量 0-1")
    parser.add_argument("--no-cover", action="store_true", help="不生成封面")
    parser.add_argument("--no-qc", action="store_true", help="不跑自动质检")
    parser.add_argument("--title", type=str, default="", help="封面标题；默认取文案前 20 字")
    parser.add_argument("--keep-wav", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    text = args.text
    if args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            text = f.read()
    if not args.audio and not (text or "").strip():
        print("文案为空", file=sys.stderr)
        return 2

    os.makedirs("data/offline", exist_ok=True)
    output = args.output or os.path.join(
        "data/offline", time.strftime("offline_%Y%m%d_%H%M%S.mp4")
    )
    base = os.path.splitext(output)[0]
    srt_path = (
        base + ".ass"
        if not args.no_subtitle and not args.audio
        else None
    )
    cover_path = None if args.no_cover else base + ".jpg"
    title = args.title or headline(text or "")

    wav_path = args.audio
    temp_wav = False
    if not wav_path:
        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        temp_wav = True
        t0 = time.perf_counter()
        synthesize(text, args.voice, wav_path, subtitle_path=srt_path)
        print(f"[tts] {time.perf_counter() - t0:.2f}s -> {wav_path}", flush=True)

    try:
        t0 = time.perf_counter()
        renderer = OfflineRenderer(
            avatar_id=args.avatar_id,
            batch_size=args.batch_size,
        )
        print(f"[load] {time.perf_counter() - t0:.2f}s", flush=True)

        t0 = time.perf_counter()
        renderer.render(
            audio_path=wav_path,
            output_path=output,
            fps=args.fps,
            crf=args.crf,
            segment_seconds=args.segment_seconds,
            overlap_seconds=args.overlap_seconds,
            subtitle_path=srt_path if srt_path and os.path.exists(srt_path) else None,
            bgm_path=args.bgm or None,
            bgm_volume=args.bgm_volume,
            cover_path=cover_path,
            cover_title=title,
            progress=lambda done, total: print(
                f"[render] {done}/{total}", flush=True
            ),
        )
        print(f"[done] {time.perf_counter() - t0:.2f}s -> {output}", flush=True)
        if srt_path and os.path.exists(srt_path):
            print(f"[subtitle] {srt_path}", flush=True)
        if cover_path and os.path.exists(cover_path):
            print(f"[cover] {cover_path}", flush=True)

        if not args.no_qc:
            qc = run_qc(output, wav_path)
            qc_path = base + ".qc.json"
            save_qc(qc, qc_path)
            print(
                f"[qc] {qc['status']} face_missing={qc['face_missing_ratio']} "
                f"black={qc['black_ratio']} flicker={qc['flicker_ratio']} "
                f"lip_corr={qc['lip_corr']} -> {qc_path}",
                flush=True,
            )
    finally:
        if temp_wav and not args.keep_wav:
            try:
                os.remove(wav_path)
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
