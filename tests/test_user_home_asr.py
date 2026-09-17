import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
USER_HOME = REPO / "frontend" / "src" / "views" / "user" / "Home.vue"
README = REPO / "README.md"
WEB = REPO / "web"


class UserHomeAsrTests(unittest.TestCase):
    def test_a1_mic_only_when_connected(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("开始说话", src)
        self.assertIn("停止识别", src)
        self.assertIn("startMic", src)
        self.assertIn("!connected || listening || recognizing", src)
        self.assertIn("!connected || !listening || recognizing", src)

    def test_a2_stop_sends_human_echo(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("'/api/asr'", src)
        self.assertIn("is_speaking: true", src)
        self.assertIn("is_speaking: false", src)
        self.assertIn("await sendHuman(recognized)", src)
        self.assertIn("fetch('/human'", src)
        self.assertIn("type: talkType.value", src)
        self.assertIn("sessionid: sessionid.value", src)
        self.assertIn("talkType", src)

    def test_a3_empty_result_and_no_funasr_panel(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("未识别到语音", src)
        self.assertIn("本机 ASR 不可用", src)
        self.assertNotIn("wssip", src)
        self.assertNotIn("2pass", src)
        self.assertNotIn("asr_mode", src)

    def test_a4_web_untouched_readme_mentions_mic(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("/app/user", readme)
        self.assertIn("麦克风说话", readme)
        self.assertTrue((WEB / "index.html").is_file())
        self.assertTrue((WEB / "asr" / "main.js").is_file())


if __name__ == "__main__":
    unittest.main()
