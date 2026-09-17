import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
USER_HOME = REPO / "frontend" / "src" / "views" / "user" / "Home.vue"
README = REPO / "README.md"


class UserHomeChatTests(unittest.TestCase):
    def test_a1_echo_or_chat_when_connected(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn('v-model="talkType"', src)
        self.assertIn('talkType = ref(\'echo\')', src)
        self.assertIn("value=\"echo\"", src)
        self.assertIn("value=\"chat\"", src)
        self.assertIn("type: talkType.value", src)
        self.assertIn("fetch('/human'", src)
        self.assertIn(":disabled=\"!connected\"", src)
        self.assertIn("@click=\"sendText\"", src)

    def test_a2_interrupt_uses_session(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("打断", src)
        self.assertIn("async function interrupt()", src)
        self.assertIn("fetch('/interrupt_talk'", src)
        self.assertIn("sessionid: sessionid.value", src)
        self.assertIn(":disabled=\"!connected\"", src)
        self.assertIn("@click=\"interrupt\"", src)

    def test_a3_mic_follows_talk_type(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("await sendHuman(recognized)", src)
        self.assertIn("type: talkType.value", src)
        self.assertIn("未识别到语音", src)

    def test_a4_web_untouched_readme_echo_chat(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("echo/chat 与打断", readme)
        result = subprocess.run(
            ["git", "diff", "--exit-code", "--", "web/"],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
