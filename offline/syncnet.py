"""SyncNet 口型一致性评分。

模型与预处理参考 LatentSync / SyncNet：
- `S` 网络（joonson/syncnet_python）
- 权重 `models/syncnet/syncnet_v2.model`
- 224×224 视频帧 + 20 维 MFCC，5 帧视频 / 20 帧音频为一条样本
"""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
from typing import Optional

import cv2
import librosa
import numpy as np
import python_speech_features
import torch
import torch.nn as nn


class S(nn.Module):
    def __init__(self, num_layers_in_fc_layers: int = 1024):
        super().__init__()
        self.netcnnaud = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 1), stride=(1, 1)),
            nn.Conv2d(64, 192, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(192),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(1, 2)),
            nn.Conv2d(192, 384, kernel_size=(3, 3), padding=(1, 1)),
            nn.BatchNorm2d(384),
            nn.ReLU(inplace=True),
            nn.Conv2d(384, 256, kernel_size=(3, 3), padding=(1, 1)),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=(3, 3), padding=(1, 1)),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(2, 2)),
            nn.Conv2d(256, 512, kernel_size=(5, 4), padding=(0, 0)),
            nn.BatchNorm2d(512),
            nn.ReLU(),
        )
        self.netfcaud = nn.Sequential(
            nn.Linear(512, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, num_layers_in_fc_layers),
        )
        self.netfclip = nn.Sequential(
            nn.Linear(512, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, num_layers_in_fc_layers),
        )
        self.netcnnlip = nn.Sequential(
            nn.Conv3d(3, 96, kernel_size=(5, 7, 7), stride=(1, 2, 2), padding=0),
            nn.BatchNorm3d(96),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2)),
            nn.Conv3d(96, 256, kernel_size=(1, 5, 5), stride=(1, 2, 2), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1)),
            nn.Conv3d(256, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.Conv3d(256, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.Conv3d(256, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2)),
            nn.Conv3d(256, 512, kernel_size=(1, 6, 6), padding=0),
            nn.BatchNorm3d(512),
            nn.ReLU(inplace=True),
        )

    def forward_aud(self, x):
        mid = self.netcnnaud(x)
        mid = mid.view((mid.size()[0], -1))
        return self.netfcaud(mid)

    def forward_lip(self, x):
        mid = self.netcnnlip(x)
        mid = mid.view((mid.size()[0], -1))
        return self.netfclip(mid)


def _calc_pdist(feat1, feat2, vshift: int = 15):
    win_size = vshift * 2 + 1
    feat2p = torch.nn.functional.pad(feat2, (0, 0, vshift, vshift))
    dists = []
    for i in range(len(feat1)):
        dists.append(
            torch.nn.functional.pairwise_distance(
                feat1[[i], :].repeat(win_size, 1),
                feat2p[i : i + win_size, :],
            )
        )
    return dists


class SyncNetScorer:
    def __init__(
        self,
        model_path: str = "models/syncnet/syncnet_v2.model",
        device: Optional[str] = None,
    ) -> None:
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model = S().to(self.device).eval()
        state = torch.load(model_path, map_location="cpu", weights_only=True)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        state = {k.removeprefix("module."): v for k, v in state.items()}
        self.model.load_state_dict(state, strict=True)

    @torch.no_grad()
    def score(
        self,
        video_path: str,
        audio_path: Optional[str] = None,
        batch_size: int = 20,
        vshift: int = 15,
    ) -> dict:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"cannot open video: {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        images = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            images.append(cv2.resize(frame, (224, 224)))
        cap.release()
        if len(images) < 6:
            raise ValueError("video too short for SyncNet")

        tmp_wav = None
        if not audio_path or not os.path.exists(audio_path):
            tmp_wav = tempfile.mktemp(suffix=".wav")
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
            audio_path = tmp_wav
        try:
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        finally:
            if tmp_wav:
                try:
                    os.remove(tmp_wav)
                except OSError:
                    pass

        mfcc = python_speech_features.mfcc(
            audio,
            16000,
            winlen=0.025,
            winstep=0.01,
            numcep=13,
            nfilt=26,
            nfft=512,
            lowfreq=0,
            highfreq=None,
        )
        mfcc = np.stack([np.array(i) for i in zip(*mfcc)])
        cct = torch.from_numpy(
            np.expand_dims(np.expand_dims(mfcc, axis=0), axis=0).astype(np.float32)
        )

        im = np.stack(images, axis=3)
        im = np.expand_dims(im, axis=0)
        im = np.transpose(im, (0, 3, 4, 1, 2))
        imtv = torch.from_numpy(im.astype(np.float32))

        min_length = min(len(images), math.floor(len(audio) / 640))
        lastframe = min_length - 5
        if lastframe <= 0:
            raise ValueError("audio/video too short for SyncNet")

        im_feat, cc_feat = [], []
        for i in range(0, lastframe, batch_size):
            im_batch = [
                imtv[:, :, v : v + 5, :, :]
                for v in range(i, min(lastframe, i + batch_size))
            ]
            im_in = torch.cat(im_batch, 0).to(self.device)
            im_feat.append(self.model.forward_lip(im_in).cpu())

            cc_batch = [
                cct[:, :, :, v * 4 : v * 4 + 20]
                for v in range(i, min(lastframe, i + batch_size))
            ]
            cc_in = torch.cat(cc_batch, 0).to(self.device)
            cc_feat.append(self.model.forward_aud(cc_in).cpu())

        im_feat = torch.cat(im_feat, 0)
        cc_feat = torch.cat(cc_feat, 0)
        dists = _calc_pdist(im_feat, cc_feat, vshift=vshift)
        mean_dists = torch.mean(torch.stack(dists, 1), 1)
        min_dist, minidx = torch.min(mean_dists, 0)
        conf = float(torch.median(mean_dists) - min_dist)
        offset = int(vshift - minidx.item())

        return {
            "confidence": round(conf, 4),
            "av_offset": offset,
            "frames": len(images),
            "fps": round(float(fps), 2),
        }
