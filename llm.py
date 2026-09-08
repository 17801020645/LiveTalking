import os
import re
import time
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from avatars.base_avatar import BaseAvatar
from utils.logger import logger

_SENTENCE_ENDS = ",.!;:，。！？：；"


def _sanitize_for_speech(text: str) -> str:
    """去掉 Markdown 标记，避免 TTS 把星号、井号等读出来。"""
    if not text:
        return text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"_{2,}", "", text)
    text = text.replace("\n", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _speak(avatar_session: "BaseAvatar", text: str, datainfo: dict) -> None:
    spoken = _sanitize_for_speech(text)
    if spoken:
        logger.info(spoken)
        avatar_session.put_msg_txt(spoken, datainfo)


def _resolve_api_key(opt) -> str:
    """CLI/YAML 明文 > 指定环境变量 > LLM_API_KEY > DASHSCOPE_API_KEY。"""
    key = (getattr(opt, "llm_api_key", None) or "").strip()
    if key:
        return key
    env_name = getattr(opt, "llm_api_key_env", None) or "LLM_API_KEY"
    for name in (env_name, "LLM_API_KEY", "DASHSCOPE_API_KEY"):
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return ""


def llm_response(message, avatar_session: "BaseAvatar", datainfo: dict = {}):
    try:
        opt = avatar_session.opt
        base_url = (getattr(opt, "llm_base_url", None) or "").rstrip("/")
        model = getattr(opt, "llm_model", None) or "qwen-plus"
        system_prompt = getattr(opt, "llm_system_prompt", None) or (
            "你是一个知识助手，尽量以简短、口语化的方式输出。不要使用Markdown，不要用星号或井号强调。"
        )
        api_key = _resolve_api_key(opt)
        if not api_key:
            # 部分本地服务（Ollama 等）不校验 Key，给占位以免 SDK 拒绝初始化
            api_key = "dummy"

        start = time.perf_counter()
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        logger.info(
            f"llm Time init: {time.perf_counter()-start:.4f}s, "
            f"model={model}, base_url={base_url or 'default'}, message={message}"
        )

        create_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "stream": True,
        }
        if getattr(opt, "llm_stream_usage", False):
            create_kwargs["stream_options"] = {"include_usage": True}

        completion = client.chat.completions.create(**create_kwargs)
        result = ""
        first = True
        for chunk in completion:
            if len(chunk.choices) > 0:
                if first:
                    logger.info(f"llm Time to first chunk: {time.perf_counter()-start:.4f}s")
                    first = False
                msg = chunk.choices[0].delta.content
                if msg is None:
                    continue
                lastpos = 0
                for i, char in enumerate(msg):
                    if char in _SENTENCE_ENDS:
                        result = result + msg[lastpos:i + 1]
                        lastpos = i + 1
                        if len(result) > 10:
                            _speak(avatar_session, result, datainfo)
                            result = ""
                result = result + msg[lastpos:]
        logger.info(f"llm Time to last chunk: {time.perf_counter()-start:.4f}s")
        if result:
            _speak(avatar_session, result, datainfo)

    except Exception:
        logger.exception("llm exception:")
        return
