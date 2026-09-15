import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_auth import LOGIN_ERROR
from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
OPS = REPO / "frontend" / "src" / "views" / "admin" / "Ops.vue"


class AdminDisableUserTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_a1_admin_can_disable_active_user(self):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "bobuser", "password": "bobusr1"},
        )
        uid = (await created.json())["data"]["id"]
        disabled = await self.client.post(f"/api/v1/admin/users/{uid}/disable")
        self.assertEqual(disabled.status, 200)
        listed = await self.client.get("/api/v1/admin/users")
        users = {u["username"]: u for u in (await listed.json())["data"]["users"]}
        self.assertEqual(users["bobuser"]["status"], "disabled")
        src = OPS.read_text(encoding="utf-8")
        self.assertIn("禁用", src)
        self.assertIn("/disable", src)
        self.assertIn("window.confirm", src)

    async def test_a2_disabled_user_cannot_login(self):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "cara", "password": "cara123"},
        )
        uid = (await created.json())["data"]["id"]
        await self.client.post(f"/api/v1/admin/users/{uid}/disable")
        await self.client.post("/api/v1/auth/logout")
        bad = await self.login("cara", "cara123")
        self.assertEqual(bad.status, 401)
        body = await bad.json()
        self.assertEqual(body["msg"], LOGIN_ERROR)

    async def test_a3_cannot_disable_self_admin_or_as_user(self):
        await self.login("admin", "secret12")
        me = await self.client.get("/api/v1/auth/me")
        admin_id = (await me.json())["data"]["id"]
        self_disable = await self.client.post(f"/api/v1/admin/users/{admin_id}/disable")
        self.assertEqual(self_disable.status, 400)
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "dana", "password": "dana123"},
        )
        uid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")
        unauth = await self.client.post(f"/api/v1/admin/users/{uid}/disable")
        self.assertEqual(unauth.status, 401)
        await self.login("dana", "dana123")
        forbidden = await self.client.post(f"/api/v1/admin/users/{uid}/disable")
        self.assertEqual(forbidden.status, 403)
        src = OPS.read_text(encoding="utf-8")
        self.assertIn("u.role === 'user' && u.status === 'active'", src)

    async def test_a4_web_untouched(self):
        self.assertTrue((WEB / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
