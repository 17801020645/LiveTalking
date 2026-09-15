import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADMIN = REPO / "frontend" / "src" / "views" / "admin"
USER = REPO / "frontend" / "src" / "views" / "user"
LOGIN = REPO / "frontend" / "src" / "views" / "Login.vue"
CSS = REPO / "frontend" / "src" / "styles.css"


class GalleryAdminPagesTests(unittest.TestCase):
    def test_a1_live_uses_monitor_panels(self):
        src = (ADMIN / "Live.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("开始连接", src)
        self.assertIn("打开 /", src)
        self.assertNotIn("glass card", src)

    def test_a2_avatar_uses_monitor_panels(self):
        src = (ADMIN / "Avatar.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("开始生成", src)
        self.assertNotIn("glass card", src)

    def test_a3_ops_uses_monitor_panels(self):
        src = (ADMIN / "Ops.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("创建普通用户", src)
        self.assertNotIn("glass card", src)

    def test_a4_tts_uses_monitor_panels(self):
        src = (ADMIN / "Tts.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("/tts/", src)
        self.assertNotIn("glass card", src)

    def test_a5_login_user_shell_and_web_untouched_markers(self):
        login = LOGIN.read_text(encoding="utf-8")
        self.assertIn("glass login-card", login)
        self.assertNotIn("monitor-panel", login)
        for name in ("Home.vue", "Assets.vue", "Custom.vue"):
            src = (USER / name).read_text(encoding="utf-8")
            self.assertNotIn("monitor-panel", src)
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".monitor-panel", css)


if __name__ == "__main__":
    unittest.main()
