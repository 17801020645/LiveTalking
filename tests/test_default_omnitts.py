import inspect
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests

from config import parse_args
from tts.omnitts import OmniTTS

REPO = Path(__file__).resolve().parents[1]
DOCS_OMNI = REPO / "docs" / "omni_tts.md"
BASE_AVATAR = REPO / "avatars" / "base_avatar.py"


class _Parent:
    pass


def _opt(**kwargs):
    defaults = dict(
        fps=25,
        tts="omnitts",
        TTS_SERVER="http://127.0.0.1:8091",
        REF_FILE="vivian",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class DefaultOmniTTSTests(unittest.TestCase):
    def test_a1_yaml_and_argparse_defaults(self):
        with patch.object(sys, "argv", ["app.py", "--config", str(REPO / "config.yaml")]):
            opt = parse_args()
        self.assertEqual(opt.tts, "omnitts")
        self.assertEqual(opt.TTS_SERVER, "http://127.0.0.1:8091")
        self.assertEqual(opt.REF_FILE, "vivian")

        with patch.object(sys, "argv", ["app.py", "--config", ""]):
            opt = parse_args()
        self.assertEqual(opt.tts, "omnitts")
        self.assertEqual(opt.TTS_SERVER, "http://127.0.0.1:8091")
        self.assertEqual(opt.REF_FILE, "vivian")

    def test_a2_default_client_is_omnitts_not_edge(self):
        with patch.object(sys, "argv", ["app.py", "--config", str(REPO / "config.yaml")]):
            opt = parse_args()
        self.assertEqual(opt.tts, "omnitts")
        client = OmniTTS(opt, _Parent())
        self.assertIsInstance(client, OmniTTS)
        self.assertEqual(client.voice, "vivian")
        self.assertEqual(client.server_url, "http://127.0.0.1:8091")

        src = BASE_AVATAR.read_text(encoding="utf-8")
        self.assertIn('registry.create("tts", opt.tts', src)
        self.assertNotIn("edgetts", inspect.getsource(OmniTTS.txt_to_audio))
        self.assertNotRegex(
            src,
            r"opt\.tts\s*=\s*['\"]edgetts['\"]",
        )

    def test_a3_omni_down_does_not_fallback_or_exit(self):
        client = OmniTTS(_opt(), _Parent())
        with patch(
            "tts.omnitts.requests.post",
            side_effect=requests.exceptions.ConnectionError("8091 down"),
        ):
            chunks = list(
                client._synthesize(
                    text="你好",
                    voice="vivian",
                    language="Auto",
                    speed=1.0,
                    instructions="",
                    task_type="CustomVoice",
                )
            )
        self.assertEqual(chunks, [])

    def test_a4_docs_default_omni_and_switch_back(self):
        text = DOCS_OMNI.read_text(encoding="utf-8")
        self.assertIn("tts: omnitts", text)
        self.assertIn("默认", text)
        self.assertIn("edgetts", text)
        self.assertIn("重启", text)
        self.assertIn("不必停 8091", text)


if __name__ == "__main__":
    unittest.main()
