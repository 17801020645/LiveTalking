import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
USER = REPO / "frontend" / "src" / "views" / "user"
LOGIN = REPO / "frontend" / "src" / "views" / "Login.vue"
LAYOUT = REPO / "frontend" / "src" / "layouts" / "UserLayout.vue"
PW = REPO / "frontend" / "src" / "components" / "PasswordForm.vue"
WEB = REPO / "web"


class GalleryUserShellTests(unittest.TestCase):
    def test_a1_login_is_gallery_monitor(self):
        src = LOGIN.read_text(encoding="utf-8")
        self.assertIn('class="gallery login-wrap"', src)
        self.assertIn("monitor-panel", src)
        self.assertIn("用户名", src)
        self.assertIn("密码", src)
        self.assertNotIn("glass login-card", src)
        self.assertNotIn("glass card", src)

    def test_a2_user_home_is_monitor(self):
        src = (USER / "Home.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("开始连麦", src)
        self.assertIn("发送文字", src)
        self.assertIn("我的资产", src)
        self.assertNotIn("glass card", src)
        self.assertNotIn("glass empty", src)

    def test_a3_assets_are_monitors(self):
        src = (USER / "Assets.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("发布到首页", src)
        self.assertIn("取消发布", src)
        self.assertNotIn("glass card", src)
        self.assertNotIn("glass empty", src)

    def test_a4_custom_uses_monitors(self):
        src = (USER / "Custom.vue").read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("提交订单", src)
        self.assertIn("我的订单", src)
        self.assertNotIn("glass card", src)

    def test_a5_password_form_is_gallery(self):
        src = PW.read_text(encoding="utf-8")
        self.assertIn("monitor-panel", src)
        self.assertIn("当前密码", src)
        self.assertIn("新密码", src)
        self.assertNotIn("glass card", src)
        layout = LAYOUT.read_text(encoding="utf-8")
        self.assertIn('class="shell gallery"', layout)

    def test_a6_web_untouched(self):
        self.assertTrue((WEB / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
