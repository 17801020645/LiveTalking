###############################################################################
#  Copyright (C) 2024 LiveTalking@lipku https://github.com/lipku/LiveTalking
#  email: lipku@foxmail.com
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#       http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
#
#  Avatar 基类 — 合并自 basereal.py，集成到 Async Pipeline
#

import math
from numpy.typing import NDArray
import torch
import numpy as np
import subprocess
import os
import time
import cv2
import glob
import resampy
import queue
from queue import Queue
from threading import Thread, Event
from io import BytesIO
import soundfile as sf
import asyncio
from enum import Enum
import json
import importlib
import registry

import torch.multiprocessing as mp
from dataclasses import dataclass, field

from av import AudioFrame, VideoFrame
from fractions import Fraction

from utils.logger import logger
from utils.image import read_imgs,mirror_index

# class State(Enum):
#     INIT=0
#     WAIT=1
#     QUESTION=2
#     ANSWER=3

@dataclass
class AudioFrameData:
    """音频帧数据结构，包含音频数据、类型和用户自定义数据"""
    data: NDArray[np.float32]
    type: int = 0  # 默认值：0表示正常语音，非0表示特殊音频类型（如静音、自定义）
    userdata: dict = field(default_factory=dict)

class BaseAvatar:
    """数字人基类，负责TTS、ASR、推理、渲染输出等核心流程的协调"""
    def __init__(self, opt):
        """
        初始化数字人
        :param opt: 配置参数对象，包含模型路径、传输方式、TTS类型等
        """
        self.opt = opt
        self.sample_rate = 16000  # 音频采样率
        self.chunk = self.sample_rate // (opt.fps*2) # 320 samples per chunk (20ms) 每个音频块的长度
        self.sessionid = self.opt.sessionid

        self.speaking = False  # 当前是否正在说话（用于状态展示）
        self.recording = False  # 是否正在录制视频
        self._record_video_pipe = None  # 录制视频的ffmpeg进程管道
        self._record_audio_pipe = None  # 录制音频的ffmpeg进程管道
        self.width = self.height = 0  # 视频帧宽高

        self.custom_audiotype = 0  # 当前使用的自定义音频类型，0表示无自定义
        self.custom_img_cycle = {}  # 自定义图像循环缓存，key为音频类型
        self.custom_audio_cycle = {}  # 自定义音频循环缓存
        self.custom_audio_index = {}  # 自定义音频播放索引
        self.custom_index = {}  # 自定义图像播放索引
        self.msgqueues = []  # 消息队列列表，用于通知外部事件
        # self.custom_opt = {}
        self.__loadcustom()  # 加载自定义配置

        self.batch_size = opt.batch_size  # 推理批次大小
        self.res_frame_queue = Queue(self.batch_size*2)  # 结果帧队列，用于推理线程与渲染线程通信
        self.render_event = Event()  # 渲染事件，可能用于线程同步

        # TTS模块映射表，根据配置动态导入对应的TTS实现
        _tts_modules = {
            'edgetts': 'tts.edge',
            'gpt-sovits': 'tts.sovits',
            'xtts': 'tts.xtts',
            'cosyvoice': 'tts.cosyvoice',
            'fishtts': 'tts.fish',
            'tencent': 'tts.tencent',
            'doubao': 'tts.doubao',
            'indextts2': 'tts.indextts2',
            'azuretts': 'tts.azure',
            'qwentts': 'tts.qwentts',
            'omnitts': 'tts.omnitts'
        }

        # 根据配置导入并创建TTS模块实例
        if opt.tts in _tts_modules:
            importlib.import_module(_tts_modules[opt.tts])
            self.tts = registry.create("tts", opt.tts, opt=opt, parent=self)
        else:
            logger.error(f"TTS module {opt.tts} not found.")

        # 输出模块映射表，支持webrtc、rtmp推流和虚拟摄像头等
        _output_modules = {
            'webrtc': 'streamout.webrtc',
            'rtcpush': 'streamout.webrtc',
            'rtmp': 'streamout.rtmp',
            'virtualcam': 'streamout.virtualcam'
        }

        # 初始化输出模块
        if opt.transport in _output_modules:
            try:
                importlib.import_module(_output_modules[opt.transport])
                self.output = registry.create("streamout", opt.transport, opt=opt, parent=self)
            except ModuleNotFoundError:
                logger.error(f"Output transport module {_output_modules[opt.transport]} not found.")
        else:
            logger.error(f"Output transport {opt.transport} not found in map.")

    # 如果系统没有使用 pipeline，或者为了向后兼容原来的 ttsreal.py
    def put_msg_txt(self, msg, datainfo:dict={}):
        """将文本消息送入TTS模块进行处理"""
        if hasattr(self, 'tts'):
            self.tts.put_msg_txt(msg, datainfo)
    
    def put_audio_frame(self, audio_chunk:NDArray[np.float32], datainfo:dict={}): 
        """将音频块送入ASR模块（或相关处理）"""
        if hasattr(self, 'asr'):
            self.asr.put_audio_frame(audio_chunk, datainfo)

    def put_audio_file(self, filebyte, datainfo:dict={}): 
        """将音频文件字节流分块送入处理"""
        input_stream = BytesIO(filebyte)
        stream = self.__create_bytes_stream(input_stream)
        streamlen = stream.shape[0]
        idx = 0
        first = True
        while streamlen >= self.chunk:
            eventpoint = {}
            if first:
                eventpoint = {'status': 'start'}
                first = False
            if streamlen - self.chunk < self.chunk:
                eventpoint = {'status': 'end'}
            eventpoint.update(**datainfo) 
            self.put_audio_frame(stream[idx:idx+self.chunk], eventpoint)
            streamlen -= self.chunk
            idx += self.chunk

    def put_audio_filepath(self, filepath, datainfo:dict={}): 
        """从文件路径读取音频并分块送入处理"""
        stream = self.__create_bytes_stream(filepath)
        streamlen = stream.shape[0]
        idx = 0
        first = True
        while streamlen >= self.chunk:
            eventpoint = {}
            if first:
                eventpoint = {'status': 'start'}
                first = False
            if streamlen - self.chunk < self.chunk:
                eventpoint = {'status': 'end'}
            eventpoint.update(**datainfo) 
            self.put_audio_frame(stream[idx:idx+self.chunk], eventpoint)
            streamlen -= self.chunk
            idx += self.chunk
    
    def __create_bytes_stream(self, byte_stream):
        """将音频文件字节流解析为numpy数组，并重采样到目标采样率"""
        stream, sample_rate = sf.read(byte_stream) # [T*sample_rate,] float64
        logger.info(f'[INFO]put audio stream {sample_rate}: {stream.shape}')
        stream = stream.astype(np.float32)

        if stream.ndim > 1:
            logger.info(f'[WARN] audio has {stream.shape[1]} channels, only use the first.')
            stream = stream[:, 0]
    
        if sample_rate != self.sample_rate and stream.shape[0] > 0:
            logger.info(f'[WARN] audio sample rate is {sample_rate}, resampling into {self.sample_rate}.')
            stream = resampy.resample(x=stream, sr_orig=sample_rate, sr_new=self.sample_rate)

        return stream

    def flush_talk(self):
        """清空TTS和ASR中的未处理任务，重置自定义音频状态"""
        if hasattr(self, 'tts') and hasattr(self.tts, 'flush_talk'):
            self.tts.flush_talk()
        if hasattr(self, 'asr') and hasattr(self.asr, 'flush_talk'):
            self.asr.flush_talk()
        self.custom_audiotype = 0  

    # def flush(self):
    #     self.flush_talk()

    def is_speaking(self) -> bool:
        """返回当前是否正在说话"""
        return self.speaking
    
    def __loadcustom(self):
        """加载自定义图像和音频，用于特殊状态（如静音或特定音效）的展示"""
        if not hasattr(self.opt, 'customopt') or not self.opt.customopt:
            return
        for item in self.opt.customopt:
            logger.info(item)
            # 加载自定义图像序列
            input_img_list = glob.glob(os.path.join(item['imgpath'], '*.[jpJP][pnPN]*[gG]'))
            input_img_list = sorted(input_img_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
            self.custom_img_cycle[item['audiotype']] = read_imgs(input_img_list)
            # 加载自定义音频（如果有）
            if item.get('audiopath'):
                self.custom_audio_cycle[item['audiotype']], sample_rate = sf.read(item['audiopath'], dtype='float32')
                self.custom_audio_index[item['audiotype']] = 0
            self.custom_index[item['audiotype']] = 0
            # self.custom_opt[item['audiotype']] = item

    def init_customindex(self):
        """重置所有自定义索引，回到初始状态"""
        self.custom_audiotype = 0
        for key in self.custom_audio_index:
            self.custom_audio_index[key] = 0
        for key in self.custom_index:
            self.custom_index[key] = 0

    def add_msgqueue(self, msgqueue):
        """注册消息队列，用于向外发送状态通知"""
        self.msgqueues.append(msgqueue)

    def send_msg(self, msg):
        """向所有注册的消息队列发送消息"""
        for q in self.msgqueues:
            q.put(msg)

    def notify(self, eventpoint:dict):
        """根据事件点信息发送通知（如音频播放开始/结束）"""
        if eventpoint and eventpoint.get('status'):
            logger.info("notify:%s", eventpoint)
            self.send_msg(json.dumps(eventpoint))

    def start_recording(self):
        """开始录制视频和音频，使用ffmpeg进程管道写入数据"""
        if self.recording:
            return
        # 视频录制命令：将BGR帧编码为H264
        command = ['ffmpeg',
                    '-y', '-an',
                    '-f', 'rawvideo',
                    '-vcodec','rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-s', "{}x{}".format(self.width, self.height),
                    '-r', str(25),
                    '-i', '-',
                    '-pix_fmt', 'yuv420p', 
                    '-vcodec', "h264",
                    f'temp{self.opt.sessionid}.mp4']
        self._record_video_pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)

        # 音频录制命令：16kHz单声道16位PCM编码为AAC
        acommand = ['ffmpeg',
                    '-y', '-vn',
                    '-f', 's16le',
                    '-ac', '1',
                    '-ar', '16000',
                    '-i', '-',
                    '-acodec', 'aac',
                    f'temp{self.opt.sessionid}.aac']
        self._record_audio_pipe = subprocess.Popen(acommand, shell=False, stdin=subprocess.PIPE)

        self.recording = True
    
    def record_video_data(self, image):
        """写入一帧视频数据到ffmpeg管道"""
        if self.width == 0:
            self.height, self.width, _ = image.shape
        if self.recording:
            self._record_video_pipe.stdin.write(image.tobytes()) #tostring()

    def record_audio_data(self, frame):
        """写入一段音频数据到ffmpeg管道"""
        if self.recording:
            self._record_audio_pipe.stdin.write(frame.tobytes())
		
    def stop_recording(self):
        """停止录制，合并音视频为最终文件"""
        if not self.recording:
            return
        self.recording = False 
        self._record_video_pipe.stdin.close()
        self._record_video_pipe.wait()
        self._record_audio_pipe.stdin.close()
        self._record_audio_pipe.wait()
        
        # 合并临时音视频文件
        record_path = os.path.join('data', 'record')
        os.makedirs(record_path, exist_ok=True)
        output_file = os.path.join(record_path, f"{self.opt.sessionid}.mp4")
        
        temp_aac = f"temp{self.opt.sessionid}.aac"
        temp_mp4 = f"temp{self.opt.sessionid}.mp4"
        
        cmd_combine_audio = f"ffmpeg -y -i {temp_aac} -i {temp_mp4} -c:v copy -c:a copy {output_file}"
        os.system(cmd_combine_audio)
        
        # 删除临时文件
        try:
            os.remove(temp_aac)
            os.remove(temp_mp4)
        except Exception as e:
            logger.error(f"Error removing temp files: {e}")

    # def mirror_index(self, size, index):
    #     turn = index // size
    #     res = index % size
    #     if turn % 2 == 0:
    #         return res
    #     else:
    #         return size - res - 1 
    
    def get_custom_audio_stream(self, audiotype):
        """获取自定义音频流的一段数据，自动循环并更新索引"""
        idx = self.custom_audio_index[audiotype]
        stream = self.custom_audio_cycle[audiotype][idx:idx+self.chunk]
        self.custom_audio_index[audiotype] += self.chunk
        if self.custom_audio_index[audiotype] >= self.custom_audio_cycle[audiotype].shape[0]:
            # 如果播放完毕，切换回静音状态
            self.custom_audiotype = 1
        return stream
    
    def set_custom_state(self, audiotype, reinit=True):
        """设置当前使用的自定义状态（音频和图像类型）"""
        print('set_custom_state:', audiotype)
        if self.custom_audio_index.get(audiotype) is None:
            return
        self.custom_audiotype = audiotype
        if reinit:
            self.custom_audio_index[audiotype] = 0
            self.custom_index[audiotype] = 0

    # ========================== 核心渲染及 Pipeline 桥接 ==========================
    def get_avatar_length(self):
        """获取数字人帧序列长度（用于循环）"""
        if hasattr(self, 'frame_list_cycle'):
            return len(self.frame_list_cycle)
        return 1
        
    def inference(self, quit_event):
        """
        推理线程：从ASR获取特征，批量推理生成说话人脸帧，并放入结果队列
        :param quit_event: 多进程事件，用于控制线程退出
        """
        length = self.get_avatar_length()  # 总帧数
        index = 0  # 当前播放的帧索引
        count = 0  # 用于统计推理性能的计数器
        counttime = 0
        last_speaking = False  # 上一次是否为说话状态

        # syncnet_T = 12  # 时间步
        # weight_dtype = torch.float16  # 数据类型
        # infernum = 0
        logger.info('start inference')
        while not quit_event.is_set():
            starttime = time.perf_counter()
            audiofeat_batch = []
            try:
                # 从ASR获取音频特征（用于驱动口型的特征）
                audiofeat_batch = self.asr.feat_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
                
            is_all_silence = True
            audio_frames: list[AudioFrameData] = []
            # 从输出队列获取与这批特征对应的音频块（用于播放和状态判断）
            for _ in range(self.batch_size * 2):
                audioframe:AudioFrameData = self.asr.output_queue.get()
                if audioframe.type == 0:
                    is_all_silence = False               
                audio_frames.append(audioframe)

            # 检测状态变化（当前批次是否全为静音）
            current_speaking = not is_all_silence

            if is_all_silence: # 全为静音数据，不需要推理，直接使用完整图像帧
                for i in range(self.batch_size):
                    idx = mirror_index(length, index)  # 计算镜像循环索引
                    self.res_frame_queue.put((None, audio_frames[i*2:i*2+2], idx))
                    index = index + 1
            else:
                # 从静音切换到说话且配置了自定义说话起始视频时，重置帧索引
                if current_speaking and not last_speaking and self.custom_index.get(1) is not None:
                    index = 0
                t = time.perf_counter()

                # 调用具体数字人实现的推理函数，得到生成的人脸帧
                pred = self.inference_batch(index, audiofeat_batch)

                counttime += (time.perf_counter() - t)
                count += self.batch_size
                if count >= 100:
                    logger.info(f"------actual avg infer fps:{count/counttime:.4f}")
                    count = 0
                    counttime = 0
                # 将推理结果放入队列，每个结果对应两帧音频（因为音频块是20ms，视频帧是40ms）
                for i, res_frame in enumerate(pred):
                    self.res_frame_queue.put((res_frame, audio_frames[i*2:i*2+2], mirror_index(length, index)))
                    index = index + 1
                    
            if current_speaking != last_speaking:
                logger.info(f"inference 状态切换：{'说话' if last_speaking else '静音'} → {'说话' if current_speaking else '静音'}")
                last_speaking = current_speaking         
        logger.info('baseavatar inference thread stop')

    def process_frames(self,quit_event):
        """
        渲染线程：从结果队列取出推理帧，进行后处理（如贴回原图），并通过输出模块推送音视频
        :param quit_event: 线程事件，用于控制退出
        """
        enable_transition = False  # 设置为False禁用过渡效果，True启用
        
        _last_speaking = False
        _transition_start = time.time()
        if enable_transition:
            _transition_duration = 0.1  # 过渡时间
            _last_silent_frame = None  # 静音帧缓存
            _last_speaking_frame = None  # 说话帧缓存

        self.output.start()  # 启动输出模块（如webrtc、rtmp等）
        
        while not quit_event.is_set():
            try:
                audio_frames: list[AudioFrameData]
                res_frame,audio_frames,idx = self.res_frame_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
            
            # 检测状态变化（当前音频帧是否全为静音）
            current_speaking = not (audio_frames[0].type!=0 and audio_frames[1].type!=0)
            if current_speaking != _last_speaking:
                logger.info(f"状态切换：{'说话' if _last_speaking else '静音'} → {'说话' if current_speaking else '静音'}")
                _transition_start = time.time()
            _last_speaking = current_speaking

            if audio_frames[0].type!=0 and audio_frames[1].type!=0: # 全为静音数据，使用完整图像或自定义静音视频
                self.speaking = False
                audiotype = audio_frames[0].type
                if self.custom_index.get(audiotype) is not None: # 有自定义视频（如静音时的动画）
                    mirindex = mirror_index(len(self.custom_img_cycle[audiotype]),self.custom_index[audiotype])
                    target_frame = self.custom_img_cycle[audiotype][mirindex]
                    self.custom_index[audiotype] += 1
                else:
                    target_frame = self.frame_list_cycle[idx]  # 使用预渲染的完整帧序列
                
                if enable_transition:
                    # 说话→静音过渡
                    if time.time() - _transition_start < _transition_duration and _last_speaking_frame is not None:
                        alpha = min(1.0, (time.time() - _transition_start) / _transition_duration)
                        combine_frame = cv2.addWeighted(_last_speaking_frame, 1-alpha, target_frame, alpha, 0)
                    else:
                        combine_frame = target_frame
                    # 缓存静音帧
                    _last_silent_frame = combine_frame.copy()
                else:
                    combine_frame = target_frame
            else:
                self.speaking = True
                try:
                    # 将推理得到的局部人脸贴回原图对应位置
                    current_frame = self.paste_back_frame(res_frame,idx)
                except Exception as e:
                    logger.warning(f"paste_back_frame error: {e}")
                    continue
                if enable_transition:
                    # 静音→说话过渡
                    if time.time() - _transition_start < _transition_duration and _last_silent_frame is not None:
                        alpha = min(1.0, (time.time() - _transition_start) / _transition_duration)
                        combine_frame = cv2.addWeighted(_last_silent_frame, 1-alpha, current_frame, alpha, 0)
                    else:
                        combine_frame = current_frame
                    # 缓存说话帧
                    _last_speaking_frame = combine_frame.copy()
                else:
                    combine_frame = current_frame

            # 在画面上添加水印
            cv2.putText(combine_frame, "LiveTalking", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (128,128,128), 1)
            
            # 使用统一输出接口推送视频帧
            self.output.push_video_frame(combine_frame)
            self.record_video_data(combine_frame)

            # 推送对应的两帧音频
            for audio_frame in audio_frames:
                #frame,type,eventpoint = audio_frame
                frame = (audio_frame.data * 32767).astype(np.int16)  # 转换为16位整型

                # 使用统一输出接口推送音频帧
                self.output.push_audio_frame(frame, audio_frame.userdata)
                self.record_audio_data(frame)
                
            # if self.opt.transport == 'virtualcam' and hasattr(self.output, '_cam') and self.output._cam:
            #     self.output._cam.sleep_until_next_frame()

        self.output.stop()
        logger.info('baseavatar process_frames thread stop') 

    def render(self,quit_event):
        """
        主渲染循环：启动TTS、推理线程和渲染线程，并驱动ASR运行
        :param quit_event: 多进程事件，用于控制整体退出
        """
        self.quit_event = quit_event
        
        self.init_customindex()  # 重置自定义索引
        self.tts.render(quit_event)  # 启动TTS渲染（通常内部会启动线程）

        # 创建推理线程的事件
        infer_quit_event = mp.Event()
        infer_thread = Thread(target=self.inference, args=(infer_quit_event,))
        infer_thread.start()
        
        # 创建渲染输出线程的事件
        process_quit_event = Event()
        process_thread = Thread(target=self.process_frames, args=(process_quit_event,))
        process_thread.start()

        count=0
        totaltime=0
        _starttime=time.perf_counter()
        _totalframe=0
        # 主循环：运行ASR的每个时间步，驱动整个pipeline
        while not quit_event.is_set(): 
            t = time.perf_counter()
            self.asr.run_step()

            # 根据输出缓冲区大小控制节奏，避免堆积
            buffer_size = self.output.get_buffer_size() if hasattr(self.output, 'get_buffer_size') else 0
            if buffer_size >= 5:
                logger.debug('sleep qsize=%d', buffer_size)
                time.sleep(0.04 * buffer_size * 0.8)
        logger.info('baseavatar render thread stop')

        # 通知子线程退出并等待
        infer_quit_event.set()
        infer_thread.join()

        process_quit_event.set()
        process_thread.join()