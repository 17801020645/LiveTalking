import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
OPS = REPO / "frontend" / "src" / "views" / "admin" / "Ops.vue"
README = REPO / "README.md"


class AdminEnableUserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        avatars = root / "avatars"
        (avatars / "alice").mkdir(parents=True)
        os.environ["LIVETALKING_BOOTSTRAP_ADMIN"] = "admin"
        os.environ["LIVETALKING_BOOTSTRAP_PASSWORD"] = "secret12"
        app = create_test_application(str(root / "p.db"), str(avatars), web_dir=str(WEB))
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.tmp.cleanup()

    async def login(self, username, password):
        return await self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    async def _create_user(self, username, password):
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": username, "password": password},
        )
        return (await created.json())["data"]["id"]

    async def test_a1_admin_can_enable_disabled_user(self):
        await self.login("admin", "secret12")
        uid = await self._create_user("bobuser", "bobusr1")
        await self.client.post(f"/api/v1/admin/users/{uid}/disable")
        enabled = await self.client.post(f"/api/v1/admin/users/{uid}/enable")
        self.assertEqual(enabled.status, 200)
        listed = await self.client.get("/api/v1/admin/users")
        users = {u["username"]: u for u in (await listed.json())["data"]["users"]}
        self.assertEqual(users["bobuser"]["status"], "active")
        await self.client.post("/api/v1/auth/logout")
        ok = await self.login("bobuser", "bobusr1")
        self.assertEqual(ok.status, 200)
        src = OPS.read_text(encoding="utf-8")
        self.assertIn("启用", src)
        self.assertIn("/enable", src)
        self.assertIn("window.confirm", src)

    async def test_a2_cannot_enable_active_admin_or_as_user(self):
        await self.login("admin", "secret12")
        me = await self.client.get("/api/v1/auth/me")
        admin_id = (await me.json())["data"]["id"]
        self_enable = await self.client.post(f"/api/v1/admin/users/{admin_id}/enable")
        self.assertEqual(self_enable.status, 400)
        uid = await self._create_user("cara", "cara123")
        active = await self.client.post(f"/api/v1/admin/users/{uid}/enable")
        self.assertEqual(active.status, 400)
        await self.client.post("/api/v1/auth/logout")
        unauth = await self.client.post(f"/api/v1/admin/users/{uid}/enable")
        self.assertEqual(unauth.status, 401)
        await self.login("cara", "cara123")
        forbidden = await self.client.post(f"/api/v1/admin/users/{uid}/enable")
        self.assertEqual(forbidden.status, 403)

    async def test_a3_ops_buttons_by_status(self):
        src = OPS.read_text(encoding="utf-8")
        self.assertIn("u.role === 'user' && u.status === 'active'", src)
        self.assertIn("u.role === 'user' && u.status === 'disabled'", src)
        self.assertIn("disableUser", src)
        self.assertIn("enableUser", src)

    async def test_a4_readme_app_entry_and_omni_clone(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("/app/", text)
        self.assertIn("./start.sh", text)
        self.assertIn("./start-omni.sh", text)
        self.assertIn("OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base", text)
        self.assertIn("默认入口", text)
        self.assertNotIn(
            '打开 `http://serverip:8010/index.html`，点击"开始连接"播放数字人视频',
            text,
        )
        self.assertTrue((WEB / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
