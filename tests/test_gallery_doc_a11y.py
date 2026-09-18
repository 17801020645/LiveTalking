import json
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
DESIGN = REPO / "DESIGN.md"
SIDECAR = REPO / ".impeccable" / "design.json"
PRODUCT = REPO / "PRODUCT.md"
CSS = REPO / "frontend" / "src" / "styles.css"
LOGIN = REPO / "frontend" / "src" / "views" / "Login.vue"
OPS = REPO / "frontend" / "src" / "views" / "admin" / "Ops.vue"
PASSWORD = REPO / "frontend" / "src" / "components" / "PasswordForm.vue"
ADMIN_LAYOUT = REPO / "frontend" / "src" / "layouts" / "AdminLayout.vue"
USER_LAYOUT = REPO / "frontend" / "src" / "layouts" / "UserLayout.vue"


class GalleryDocA11yTests(unittest.TestCase):
    def test_a1_design_md_scanned_from_gallery(self):
        text = DESIGN.read_text(encoding="utf-8")
        self.assertNotIn("<!-- SEED:", text)
        self.assertNotIn("[to be resolved during implementation]", text)
        self.assertIn("#111318", text)
        self.assertIn("#4361ee", text)
        self.assertIn("Barlow Condensed", text)
        self.assertIn("Noto Sans SC", text)
        self.assertIn("22px", text)
        self.assertIn(".gallery", text)
        self.assertIn("The Gallery Scope Rule", text)
        front = text.split("---")[1]
        self.assertNotIn("#f0f4fc", front)
        self.assertNotIn("cool-paper", front)
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("--wall: #111318", css)
        self.assertIn("--indigo: #4361ee", css)
        sidecar = json.loads(SIDECAR.read_text(encoding="utf-8"))
        self.assertEqual(sidecar["schemaVersion"], 2)
        self.assertIn("gallery-wall", sidecar["extensions"]["colorMeta"])
        self.assertTrue(sidecar["components"])

    def test_a2_product_names_app_wcag(self):
        text = PRODUCT.read_text(encoding="utf-8")
        self.assertIn("WCAG 2.2 AA", text)
        self.assertIn("/app/", text)
        self.assertNotIn("未决：无无障碍标准", text)
        self.assertIn("定价/许可", text)

    def test_a3_labels_and_skip_link(self):
        login = LOGIN.read_text(encoding="utf-8")
        self.assertIn("<h1 class=\"monitor-name\">", login)
        self.assertIn('for="login-username"', login)
        self.assertIn('id="login-username"', login)
        self.assertIn('for="forgot-token"', login)
        self.assertIn('id="forgot-token"', login)
        self.assertIn('role="alert"', login)
        pw = PASSWORD.read_text(encoding="utf-8")
        self.assertIn('for="pw-current"', pw)
        self.assertIn('id="pw-current"', pw)
        self.assertIn('for="pw-new"', pw)
        ops = OPS.read_text(encoding="utf-8")
        self.assertIn('for="ops-new-user"', ops)
        self.assertIn('id="ops-new-user"', ops)
        self.assertIn('for="ops-new-pass"', ops)
        admin = ADMIN_LAYOUT.read_text(encoding="utf-8")
        user = USER_LAYOUT.read_text(encoding="utf-8")
        self.assertIn("跳到主内容", admin)
        self.assertIn('href="#main-content"', admin)
        self.assertIn('id="main-content"', admin)
        self.assertIn("<main", admin)
        self.assertIn("跳到主内容", user)
        self.assertIn('id="main-content"', user)

    def test_a4_ops_user_row_keyboard_and_selected_text(self):
        ops = OPS.read_text(encoding="utf-8")
        self.assertIn('tabindex="0"', ops)
        self.assertIn("@keydown.enter.prevent", ops)
        self.assertIn("@keydown.space.prevent", ops)
        self.assertIn("row-selected-mark", ops)
        self.assertIn("选中", ops)
        self.assertIn("aria-selected", ops)
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".row-selected-mark", css)

    def test_a5_web_untouched_gallery_materials_remain(self):
        diff = subprocess.run(
            ["git", "diff", "--exit-code", "--", "web/"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(diff.returncode, 0, diff.stdout + diff.stderr)
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("--wall: #111318", css)
        self.assertIn("--indigo: #4361ee", css)
        self.assertIn(".monitor-panel", css)
        self.assertTrue((WEB / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
