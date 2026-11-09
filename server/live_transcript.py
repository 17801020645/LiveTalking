"""Live conversation transcript, kept in memory per WebRTC session."""
from __future__ import annotations

import threading
import time
from collections import OrderedDict

_MAX_SESSIONS = 200
_MAX_MESSAGES = 40


class LiveTranscriptStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: "OrderedDict[str, list[dict]]" = OrderedDict()

    def _entry(self, sessionid: str) -> list[dict]:
        messages = self._data.get(sessionid)
        if messages is None:
            messages = []
            self._data[sessionid] = messages
            while len(self._data) > _MAX_SESSIONS:
                self._data.popitem(last=False)
        else:
            self._data.move_to_end(sessionid)
        return messages

    def begin(self, sessionid: str, text: str) -> None:
        if not sessionid or not text:
            return
        with self._lock:
            messages = self._entry(sessionid)
            messages.append({"role": "user", "text": text, "ts": time.time()})
            messages.append({"role": "assistant", "text": "", "ts": time.time()})
            del messages[:-_MAX_MESSAGES]

    def append_assistant(self, sessionid: str, text: str) -> None:
        if not sessionid or not text:
            return
        with self._lock:
            messages = self._entry(sessionid)
            if messages and messages[-1].get("role") == "assistant":
                messages[-1]["text"] += text
                messages[-1]["ts"] = time.time()
            else:
                messages.append({"role": "assistant", "text": text, "ts": time.time()})
                del messages[:-_MAX_MESSAGES]

    def get(self, sessionid: str) -> dict:
        with self._lock:
            messages = self._data.get(sessionid, [])
            return {"messages": [dict(m) for m in messages]}

    def clear(self, sessionid: str) -> None:
        with self._lock:
            self._data.pop(sessionid, None)


transcript_store = LiveTranscriptStore()
