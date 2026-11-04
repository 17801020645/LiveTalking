"""离线数字人渲染模块。

设计目标：
- 复用现有的 MuseTalk 1.5 权重、`data/avatars/<id>` 资产与贴回逻辑
- 不经过 WebRTC、不经过实时音频队列，按音频时长批量渲染
- 长音频按段提取特征、连续写帧；形象帧使用镜像循环，段间不硬切、不做交叉淡化（避免重影）
- 输出 H.264 + AAC 的 MP4
"""

from __future__ import annotations

import glob
import os
import pickle
import re
import shutil
import subprocess
import tempfile
from typing import Callable, Optional

import cv2
import librosa
import numpy as np
import soundfile as sf
import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import WhisperModel

from avatars.musetalk.myutil import get_image_blending
from avatars.musetalk.utils.preprocessing import read_imgs
from avatars.musetalk.utils.utils import load_all_model

from offline.audio_processor import AudioProcessor

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def headline(text: str, max_len: int = 16) -> str:
    """取第一句做封面标题，避免把句号带到下一行。"""
    first = re.split(r"[。！？!?]", (text or "").strip())[0].strip()
    first = first.strip("，,；;：: ")
    return first[:max_len]


def make_cover(
    video_path: str,
    cover_path: str,
    title: str = "",
    at_seconds: float = 1.0,
) -> str:
    """从成片抽一帧做封面；有标题时用 Noto Sans CJK 叠加。"""
    tmp_png = tempfile.mktemp(suffix=".png")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-v",
                "error",
                "-ss",
                f"{max(0.0, at_seconds):.2f}",
                "-i",
                video_path,
                "-frames:v",
                "1",
                tmp_png,
            ],
            check=True,
        )
        img = Image.open(tmp_png).convert("RGB")
        if title:
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype(FONT_PATH, 54)
            except OSError:
                font = ImageFont.load_default()
            lines = [title[i : i + 12] for i in range(0, len(title), 12)][:2]
            y = 80
            for line in lines:
                draw.text(
                    (img.width // 2, y),
                    line,
                    font=font,
                    fill=(255, 255, 255),
                    anchor="ma",
                    stroke_width=3,
                    stroke_fill=(0, 0, 0),
                )
                y += 72
        img.save(cover_path, quality=92)
    finally:
        try:
            os.remove(tmp_png)
        except OSError:
            pass
    return cover_path


def mirror_index(size: int, index: int) -> int:
    """0..size-1..0.. 的镜像索引，避免 20s 循环处硬跳。"""
    turn = index // size
    res = index % size
    return res if turn % 2 == 0 else size - res - 1


def make_cover_from_frame(frame_path: str, cover_path: str, title: str = "") -> str:
    """用干净帧（未烧字幕）做封面，再叠加标题。"""
    img = Image.open(frame_path).convert("RGB")
    if title:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(FONT_PATH, 50)
        except OSError:
            font = ImageFont.load_default()
        title = headline(title, 26)
        lines = []
        cur = ""
        for ch in title:
            if len(cur) >= 13:
                lines.append(cur)
                cur = ""
            cur += ch
        if cur:
            lines.append(cur)
        lines = lines[:2]
        y = 80
        for line in lines:
            draw.text(
                (img.width // 2, y),
                line,
                font=font,
                fill=(255, 255, 255),
                anchor="ma",
                stroke_width=3,
                stroke_fill=(0, 0, 0),
            )
            y += 68
    img.save(cover_path, quality=92)
    return cover_path


def load_avatar(avatar_id: str):
    """从 data/avatars/<id> 读取 MuseTalk 资产。"""
    avatar_path = f"./data/avatars/{avatar_id}"
    with open(f"{avatar_path}/coords.pkl", "rb") as f:
        coord_list = pickle.load(f)
    with open(f"{avatar_path}/mask_coords.pkl", "rb") as f:
        mask_coords_list = pickle.load(f)

    input_img_list = sorted(
        glob.glob(os.path.join(f"{avatar_path}/full_imgs", "*.[jpJP][pnPN]*[gG]")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0]),
    )
    frame_list = read_imgs(input_img_list)

    mask_list = sorted(
        glob.glob(os.path.join(f"{avatar_path}/mask", "*.[jpJP][pnPN]*[gG]")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0]),
    )
    masks = read_imgs(mask_list)

    latents = torch.load(f"{avatar_path}/latents.pt")
    return frame_list, masks, coord_list, mask_coords_list, latents


class OfflineRenderer:
    def __init__(
        self,
        avatar_id: str,
        device: str = "cuda",
        batch_size: int = 8,
        whisper_dir: str = "./models/whisper",
    ) -> None:
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.batch_size = int(batch_size)

        self.vae, self.unet, self.pe = load_all_model(device=self.device)
        self.pe = self.pe.half().to(self.device)
        self.vae.vae = self.vae.vae.half().to(self.device)
        self.unet.model = self.unet.model.half().to(self.device)
        self.timesteps = torch.tensor([0], device=self.device)

        (
            self.frames,
            self.masks,
            self.coords,
            self.mask_coords,
            self.latents,
        ) = load_avatar(avatar_id)

        self.audio_processor = AudioProcessor(feature_extractor_path=whisper_dir)
        self.whisper = (
            WhisperModel.from_pretrained(whisper_dir)
            .to(self.device, dtype=self.unet.model.dtype)
            .eval()
        )

    def _paste_back(self, pred_frame: np.ndarray, idx: int) -> np.ndarray:
        bbox = self.coords[idx]
        x1, y1, x2, y2 = bbox
        ori_frame = self.frames[idx].copy()
        res_frame = cv2.resize(
            pred_frame.astype(np.uint8), (int(x2 - x1), int(y2 - y1))
        )
        return get_image_blending(
            ori_frame, res_frame, bbox, self.masks[idx], self.mask_coords[idx]
        )

    @torch.no_grad()
    def _render_frames(
        self,
        audio_path: str,
        frame_dir: str,
        frame_offset: int,
        fps: int,
        progress: Optional[Callable[[int, int], None]] = None,
        total_estimate: int = 0,
    ) -> int:
        """渲染一段音频到共享帧目录；frame_offset 保证段间连续。"""
        features, librosa_length = self.audio_processor.get_audio_feature(audio_path)
        chunks = self.audio_processor.get_whisper_chunk(
            features,
            self.device,
            self.unet.model.dtype,
            self.whisper,
            librosa_length,
            fps=fps,
            audio_padding_length_left=2,
            audio_padding_length_right=2,
        )
        total = int(chunks.shape[0])
        if total <= 0:
            raise ValueError("音频为空，无法生成视频")

        for start in range(0, total, self.batch_size):
            end = min(start + self.batch_size, total)
            whisper_batch = chunks[start:end].to(
                self.device, dtype=self.unet.model.dtype
            )
            audio_feature = self.pe(whisper_batch)

            # 全局镜像索引：20s 处不回到第 0 帧，而是原路返回，避免硬切
            idxs = [
                mirror_index(len(self.frames), frame_offset + i)
                for i in range(start, end)
            ]
            latent_batch = torch.cat(
                [self.latents[i] for i in idxs],
                dim=0,
            ).to(self.device, dtype=self.unet.model.dtype)

            pred_latents = self.unet.model(
                latent_batch,
                self.timesteps,
                encoder_hidden_states=audio_feature,
            ).sample
            recon = self.vae.decode_latents(pred_latents)

            for i, pred_frame in enumerate(recon):
                frame = self._paste_back(pred_frame, idxs[i])
                cv2.imwrite(
                    os.path.join(frame_dir, f"{frame_offset + start + i:08d}.png"),
                    frame,
                )

            if progress is not None:
                progress(
                    min(frame_offset + end, total_estimate or frame_offset + total),
                    total_estimate or frame_offset + total,
                )

        return total

    @torch.no_grad()
    def render(
        self,
        audio_path: str,
        output_path: str,
        fps: int = 25,
        crf: int = 18,
        progress: Optional[Callable[[int, int], None]] = None,
        segment_seconds: float = 0.0,
        overlap_seconds: float = 0.0,
        subtitle_path: str | None = None,
        bgm_path: str | None = None,
        bgm_volume: float = 0.12,
        cover_path: str | None = None,
        cover_title: str = "",
    ) -> str:
        """渲染完整音频。长音频按段提取特征，但连续写帧、不做交叉淡化。"""
        duration = float(librosa.get_duration(path=audio_path))
        if duration <= 0:
            raise ValueError("音频为空")

        avatar_seconds = len(self.frames) / fps
        if segment_seconds <= 0:
            segment_seconds = min(30.0, max(5.0, avatar_seconds))
        segment_seconds = float(segment_seconds)
        # overlap_seconds 保留参数兼容，镜像循环下不需要交叉淡化
        _ = overlap_seconds

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        frame_dir = tempfile.mkdtemp(prefix="offline_frames_")
        try:
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            total_estimate = max(1, int(round(duration * fps)))
            frames_done = 0
            seg_index = 0
            start = 0.0
            while start < duration - 1e-6:
                end = min(start + segment_seconds, duration)
                s0 = max(0, int(round(start * sr)))
                s1 = min(len(audio), int(round(end * sr)))
                seg_wav = os.path.join(frame_dir, f"seg_{seg_index}.wav")
                sf.write(seg_wav, audio[s0:s1], 16000, subtype="PCM_16")

                n = self._render_frames(
                    seg_wav,
                    frame_dir,
                    frame_offset=frames_done,
                    fps=fps,
                    progress=progress,
                    total_estimate=total_estimate,
                )
                frames_done += n
                seg_index += 1
                start = end
                try:
                    os.remove(seg_wav)
                except OSError:
                    pass

            if progress is not None:
                progress(frames_done, max(frames_done, total_estimate))

            if cover_path:
                idx = min(
                    max(0, frames_done - 1),
                    int(max(0.2, duration * 0.15) * fps),
                )
                frame_file = os.path.join(frame_dir, f"{idx:08d}.png")
                if os.path.exists(frame_file):
                    make_cover_from_frame(frame_file, cover_path, cover_title)

            inputs = [
                "-framerate",
                str(fps),
                "-i",
                os.path.join(frame_dir, "%08d.png"),
                "-i",
                audio_path,
            ]
            if bgm_path and os.path.exists(bgm_path):
                inputs += ["-stream_loop", "-1", "-i", bgm_path]

            fc: list[str] = []
            vmap, amap = "0:v", "1:a"
            if subtitle_path and os.path.exists(subtitle_path):
                sub = (
                    subtitle_path.replace("\\", "\\\\")
                    .replace(":", "\\:")
                    .replace("'", "\\'")
                )
                fc.append(f"[0:v]ass=filename='{sub}'[v]")
                vmap = "[v]"
            if bgm_path and os.path.exists(bgm_path):
                fc.append(f"[2:a]volume={bgm_volume}[bg]")
                fc.append(
                    "[1:a][bg]amix=inputs=2:duration=first:"
                    "dropout_transition=0:normalize=0[a]"
                )
                amap = "[a]"

            cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", *inputs]
            if fc:
                cmd += ["-filter_complex", ";".join(fc)]
            cmd += [
                "-map",
                vmap,
                "-map",
                amap,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(crf),
                "-c:a",
                "aac",
                "-shortest",
                output_path,
            ]
            subprocess.run(cmd, check=True)
        finally:
            shutil.rmtree(frame_dir, ignore_errors=True)

        return output_path
