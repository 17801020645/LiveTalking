import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "frontend" / "src" / "views" / "admin" / "Live.vue"
USER_HOME = REPO / "frontend" / "src" / "views" / "user" / "Home.vue"
WEB = REPO / "web"


class AdminLiveAsrTests(unittest.TestCase):
    def test_a1_mic_only_when_connected(self):
        src = LIVE.read_text(encoding="utf-8")
        self.assertIn("开始说话", src)
        self.assertIn("停止识别", src)
        self.assertIn("startMic", src)
        self.assertIn("!connected || listening || recognizing", src)
        self.assertIn("!connected || !listening || recognizing", src)

    def test_a2_stop_sends_human_with_talk_type(self):
        src = LIVE.read_text(encoding="utf-8")
        self.assertIn("'/api/asr'", src)
        self.assertIn("is_speaking: true", src)
        self.assertIn("is_speaking: false", src)
        self.assertIn("await sendHuman(recognized)", src)
        self.assertIn("fetch('/human'", src)
        self.assertIn("type: talkType.value", src)
        self.assertIn("sessionid: sessionid.value", src)

    def test_a3_empty_result_and_no_funasr_panel(self):
        src = LIVE.read_text(encoding="utf-8")
        self.assertIn("未识别到语音", src)
        self.assertIn("本机 ASR 不可用", src)
        self.assertNotIn("wssip", src)
        self.assertNotIn("2pass", src)
        self.assertNotIn("asr_mode", src)

    def test_a4_no_index_html_link_web_untouched(self):
        src = LIVE.read_text(encoding="utf-8")
        self.assertNotIn("打开 /index.html", src)
        self.assertNotIn('href="/index.html"', src)
        user = USER_HOME.read_text(encoding="utf-8")
        self.assertNotIn("startMic", user)
        self.assertNotIn("/api/asr", user)
        self.assertTrue((WEB / "index.html").is_file())
        self.assertTrue((WEB / "asr" / "main.js").is_file())


if __name__ == "__main__":
    unittest.main()
