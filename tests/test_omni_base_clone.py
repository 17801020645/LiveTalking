import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from config import parse_args
from tts.omnitts import OmniTTS

REPO = Path(__file__).resolve().parents[1]
START_OMNI = REPO / "start-omni.sh"
DOCS_OMNI = REPO / "docs" / "omni_tts.md"
TTS_VUE = REPO / "frontend" / "src" / "views" / "admin" / "Tts.vue"


class _Parent:
    pass


class OmniBaseCloneTests(unittest.TestCase):
    def test_a1_start_omni_defaults_customvoice(self):
        src = START_OMNI.read_text(encoding="utf-8")
        self.assertIn('MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}"', src)
        self.assertNotIn('MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-Base}"', src)

    def test_a2_docs_and_admin_copy_for_base(self):
        docs = DOCS_OMNI.read_text(encoding="utf-8")
        self.assertIn("OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base", docs)
        self.assertIn("HF_HUB_OFFLINE=0", docs)
        self.assertIn("omni_tts_task_type: Base", docs)
        self.assertNotIn("本轮不部署", docs)
        page = TTS_VUE.read_text(encoding="utf-8")
        self.assertIn("0.6B-Base", page)
        self.assertNotIn("未部署 Base", page)

    def test_a3_admin_page_task_type_by_voice(self):
        src = TTS_VUE.read_text(encoding="utf-8")
        self.assertIn("uploadedNames.value.includes(voice.value) ? 'Base' : 'CustomVoice'", src)

    def test_a4_config_task_type_default_and_client(self):
        with patch.object(sys, "argv", ["app.py", "--config", str(REPO / "config.yaml")]):
            opt = parse_args()
        self.assertEqual(opt.omni_tts_task_type, "CustomVoice")
        client = OmniTTS(opt, _Parent())
        self.assertEqual(client.task_type, "CustomVoice")

        with patch.object(sys, "argv", ["app.py", "--config", ""]):
            opt = parse_args()
        self.assertEqual(opt.omni_tts_task_type, "CustomVoice")

        base_opt = SimpleNamespace(
            fps=25,
            tts="omnitts",
            TTS_SERVER="http://127.0.0.1:8091",
            REF_FILE="cloned",
            omni_tts_task_type="Base",
        )
        cloned = OmniTTS(base_opt, _Parent())
        self.assertEqual(cloned.task_type, "Base")
        self.assertEqual(cloned.voice, "cloned")

        captured = {}

        def _fake_post(url, json=None, **_kwargs):
            captured["url"] = url
            captured["json"] = json
            resp = MagicMock()
            resp.status_code = 200
            resp.iter_content.return_value = []
            return resp

        with patch("tts.omnitts.requests.post", side_effect=_fake_post):
            list(
                cloned._synthesize(
                    text="你好",
                    voice="cloned",
                    language="Auto",
                    speed=1.0,
                    instructions="",
                    task_type=cloned.task_type,
                )
            )
        self.assertEqual(captured["url"], "http://127.0.0.1:8091/v1/audio/speech")
        self.assertEqual(captured["json"]["task_type"], "Base")
        self.assertEqual(captured["json"]["voice"], "cloned")


if __name__ == "__main__":
    unittest.main()
