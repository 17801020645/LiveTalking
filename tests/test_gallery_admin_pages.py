import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADMIN = REPO / "frontend" / "src" / "views" / "admin"
CSS = REPO / "frontend" / "src" / "styles.css"


class GalleryAdminPagesTests(unittest.TestCase):
    def test_a1_live_uses_monitor_panels(self):
        src = (ADMIN / "Live.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("开始连接", src)
        self.assertIn("开始说话", src)
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

    def test_a5_monitor_css_and_web_index_remain(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".monitor-panel", css)
        self.assertTrue((REPO / "web" / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
