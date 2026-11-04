"""MuseTalk 音频特征处理。

来源：TMElyralab/MuseTalk `musetalk/utils/audio_processor.py`（MIT），
按离线渲染场景做了最小保留。
"""

from __future__ import annotations

import math
import os

import librosa
import torch
from einops import rearrange
from transformers import AutoFeatureExtractor


class AudioProcessor:
    def __init__(self, feature_extractor_path: str = "openai/whisper-tiny/") -> None:
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(feature_extractor_path)

    def get_audio_feature(self, wav_path: str, start_index: int = 0, weight_dtype=None):
        if not os.path.exists(wav_path):
            return None
        audio, sampling_rate = librosa.load(wav_path, sr=16000)
        assert sampling_rate == 16000

        segment_length = 30 * sampling_rate
        segments = [
            audio[i : i + segment_length]
            for i in range(0, len(audio), segment_length)
        ]

        features = []
        for segment in segments:
            feature = self.feature_extractor(
                segment, return_tensors="pt", sampling_rate=sampling_rate
            ).input_features
            if weight_dtype is not None:
                feature = feature.to(dtype=weight_dtype)
            features.append(feature)

        return features, len(audio)

    def get_whisper_chunk(
        self,
        whisper_input_features,
        device,
        weight_dtype,
        whisper,
        librosa_length: int,
        fps: int = 25,
        audio_padding_length_left: int = 2,
        audio_padding_length_right: int = 2,
    ):
        audio_feature_length_per_frame = 2 * (
            audio_padding_length_left + audio_padding_length_right + 1
        )
        whisper_feature = []
        for input_feature in whisper_input_features:
            input_feature = input_feature.to(device).to(weight_dtype)
            audio_feats = whisper.encoder(
                input_feature, output_hidden_states=True
            ).hidden_states
            audio_feats = torch.stack(audio_feats, dim=2)
            whisper_feature.append(audio_feats)

        whisper_feature = torch.cat(whisper_feature, dim=1)
        sr = 16000
        audio_fps = 50
        fps = int(fps)
        whisper_idx_multiplier = audio_fps / fps
        num_frames = math.floor((librosa_length / sr) * fps)
        actual_length = math.floor((librosa_length / sr) * audio_fps)
        whisper_feature = whisper_feature[:, :actual_length, ...]

        padding_nums = math.ceil(whisper_idx_multiplier)
        whisper_feature = torch.cat(
            [
                torch.zeros_like(
                    whisper_feature[:, : padding_nums * audio_padding_length_left]
                ),
                whisper_feature,
                torch.zeros_like(
                    whisper_feature[:, : padding_nums * 3 * audio_padding_length_right]
                ),
            ],
            1,
        )

        audio_prompts = []
        for frame_index in range(num_frames):
            audio_index = math.floor(frame_index * whisper_idx_multiplier)
            audio_clip = whisper_feature[
                :, audio_index : audio_index + audio_feature_length_per_frame
            ]
            if audio_clip.shape[1] != audio_feature_length_per_frame:
                raise ValueError(
                    f"audio clip shape {audio_clip.shape} at frame {frame_index}"
                )
            audio_prompts.append(audio_clip)

        audio_prompts = torch.cat(audio_prompts, dim=0)
        audio_prompts = rearrange(audio_prompts, "b c h w -> b (c h) w")
        return audio_prompts
