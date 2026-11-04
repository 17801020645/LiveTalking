"""离线 TTS：文字 → 16k 单声道 WAV + 可选 ASS 字幕。"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import tempfile

import edge_tts
import soundfile as sf


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _join_text(parts: list[str]) -> str:
    if all(all(ord(c) < 128 for c in p) for p in parts):
        return " ".join(parts)
    return "".join(parts)


_PUNCT = "，。！？；：、,.!?;:"


def _attach_punctuation(
    words: list[tuple[float, float, str]], text: str
) -> list[tuple[float, float, str]]:
    """EdgeTTS 的 WordBoundary 不带标点；按原文补齐，避免字幕连成一片。"""
    pos = 0
    out: list[tuple[float, float, str]] = []
    for s, e, w in words:
        idx = text.find(w, pos)
        if idx < 0:
            out.append((s, e, w))
            continue
        after = idx + len(w)
        punct = ""
        while after < len(text) and text[after] in _PUNCT:
            punct += text[after]
            after += 1
        out.append((s, e, w + punct))
        pos = after
    return out


def _group_cues(words: list[tuple[float, float, str]]) -> list[tuple[float, float, str]]:
    cues: list[tuple[float, float, str]] = []
    cur: list[str] = []
    start = None
    end = 0.0
    chars = 0

    for w_start, w_end, text in words:
        text = (text or "").strip()
        if not text:
            continue
        if start is None:
            start = w_start
        cur.append(text)
        chars += len(text)
        end = w_end
        hard = text.endswith(("。", "！", "？", "；", ".", "!", "?", ";"))
        soft = text.endswith(("，", "：", ",", ":"))
        if chars >= 18 or hard or (soft and chars >= 10):
            cues.append((start, max(end + 0.08, start + 0.5), _join_text(cur)))
            cur, chars, start = [], 0, None

    if cur and start is not None:
        cues.append((start, max(end + 0.08, start + 0.5), _join_text(cur)))

    # 防止字幕重叠
    for i in range(len(cues) - 1):
        if cues[i][1] > cues[i + 1][0]:
            cues[i] = (cues[i][0], max(cues[i][0] + 0.3, cues[i + 1][0] - 0.02), cues[i][2])
    return cues


def _fallback_words(text: str, total: float) -> list[tuple[float, float, str]]:
    parts = [p.strip() for p in re.split(r"(?<=[。！？!?；;])", text) if p.strip()]
    if not parts:
        return [(0.0, total, text)]
    weights = [max(1, len(p)) for p in parts]
    s = sum(weights)
    out = []
    t = 0.0
    for p, w in zip(parts, weights):
        dur = total * w / s
        out.append((t, t + dur, p))
        t += dur
    return out


def _write_ass(
    words: list[tuple[float, float, str]],
    total: float,
    out_path: str,
    resolution: tuple[int, int],
) -> None:
    if not words:
        words = [(0.0, total, "")]
    cues = _group_cues(words)
    if not cues:
        return

    w, h = resolution
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for start, end, text in cues:
        text = text.replace("{", "（").replace("}", "）").replace("\n", "\\N")
        lines.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{text}\n"
        )
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def synthesize(
    text: str,
    voice: str,
    out_wav: str,
    subtitle_path: str | None = None,
    resolution: tuple[int, int] = (720, 1280),
) -> str:
    """用 EdgeTTS 合成，转 16k 单声道 WAV；可选生成 ASS 字幕。"""
    text = (text or "").strip()
    if not text:
        raise ValueError("text is empty")

    fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    words: list[tuple[float, float, str]] = []

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = float(chunk["offset"]) / 1e7
                    end = start + float(chunk["duration"]) / 1e7
                    words.append((start, end, chunk.get("text", "")))

    try:
        asyncio.run(_run())
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-v",
                "error",
                "-i",
                mp3_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                out_wav,
            ],
            check=True,
        )
    finally:
        try:
            os.remove(mp3_path)
        except OSError:
            pass

    if subtitle_path:
        total = float(sf.info(out_wav).duration)
        if not words:
            words = _fallback_words(text, total)
        else:
            words = _attach_punctuation(words, text)
        _write_ass(words, total, subtitle_path, resolution)

    return out_wav
