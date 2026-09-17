import os
import tempfile
import unittest
from pathlib import Path

from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer

from server.platform_auth import LOGIN_ERROR
from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
OPS = REPO / "frontend" / "src" / "views" / "admin" / "Ops.vue"
README = REPO / "README.md"


class AdminDeleteUserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        (self.avatars / "alice").mkdir(parents=True)
        os.environ["LIVETALKING_BOOTSTRAP_ADMIN"] = "admin"
        os.environ["LIVETALKING_BOOTSTRAP_PASSWORD"] = "secret12"
        app = create_test_application(
            str(root / "p.db"),
            str(self.avatars),
            web_dir=str(WEB),
            uploads_dir=str(root / "uploads"),
        )
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

    def video_form(self, text="hi"):
        data = FormData()
        data.add_field("material_type", "video")
        data.add_field("script_text", text)
        data.add_field("video", b"\x00\x00mp4", filename="clip.mp4", content_type="video/mp4")
        return data

    async def test_a1_admin_can_delete_active_or_disabled_user(self):
        await self.login("admin", "secret12")
        active_id = await self._create_user("bobuser", "bobusr1")
        disabled_id = await self._create_user("cara", "cara123")
        await self.client.post(f"/api/v1/admin/users/{disabled_id}/disable")

        deleted = await self.client.post(f"/api/v1/admin/users/{active_id}/delete")
        self.assertEqual(deleted.status, 200)
        disabled_deleted = await self.client.post(f"/api/v1/admin/users/{disabled_id}/delete")
        self.assertEqual(disabled_deleted.status, 200)

        listed = await self.client.get("/api/v1/admin/users")
        names = {u["username"] for u in (await listed.json())["data"]["users"]}
        self.assertNotIn("bobuser", names)
        self.assertNotIn("cara", names)

        await self.client.post("/api/v1/auth/logout")
        bad = await self.login("bobuser", "bobusr1")
        self.assertEqual(bad.status, 401)
        self.assertEqual((await bad.json())["msg"], LOGIN_ERROR)
        also_bad = await self.login("cara", "cara123")
        self.assertEqual(also_bad.status, 401)
        self.assertEqual((await also_bad.json())["msg"], LOGIN_ERROR)

    async def test_a2_cannot_delete_admin_self_or_as_user(self):
        await self.login("admin", "secret12")
        me = await self.client.get("/api/v1/auth/me")
        admin_id = (await me.json())["data"]["id"]
        self_delete = await self.client.post(f"/api/v1/admin/users/{admin_id}/delete")
        self.assertEqual(self_delete.status, 400)
        missing = await self.client.post("/api/v1/admin/users/99999/delete")
        self.assertEqual(missing.status, 404)
        uid = await self._create_user("dana", "dana123")
        await self.client.post("/api/v1/auth/logout")
        unauth = await self.client.post(f"/api/v1/admin/users/{uid}/delete")
        self.assertEqual(unauth.status, 401)
        await self.login("dana", "dana123")
        forbidden = await self.client.post(f"/api/v1/admin/users/{uid}/delete")
        self.assertEqual(forbidden.status, 403)

    async def test_a3_ops_delete_button_and_orders_cascade(self):
        src = OPS.read_text(encoding="utf-8")
        self.assertIn("删除", src)
        self.assertIn("/delete", src)
        self.assertIn("deleteUser", src)
        self.assertIn("window.confirm", src)
        self.assertIn("v-if=\"u.role === 'user'\"", src)
        self.assertNotIn("u.role === 'admin'", src)

        await self.login("admin", "secret12")
        uid = await self._create_user("erin", "erin123")
        await self.client.post(
            f"/api/v1/admin/users/{uid}/subscriptions",
            json={"avatar_id": "alice"},
        )
        await self.client.post("/api/v1/auth/logout")
        await self.login("erin", "erin123")
        created = await self.client.post("/api/v1/me/orders", data=self.video_form())
        self.assertEqual(created.status, 200)
        oid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")

        await self.login("admin", "secret12")
        before = await self.client.get("/api/v1/admin/orders")
        before_ids = {o["id"] for o in (await before.json())["data"]["orders"]}
        self.assertIn(oid, before_ids)

        deleted = await self.client.post(f"/api/v1/admin/users/{uid}/delete")
        self.assertEqual(deleted.status, 200)
        after = await self.client.get("/api/v1/admin/orders")
        after_ids = {o["id"] for o in (await after.json())["data"]["orders"]}
        self.assertNotIn(oid, after_ids)
        self.assertTrue((self.avatars / "alice").is_dir())

        text = README.read_text(encoding="utf-8")
        self.assertIn("用户（禁用/启用/删除）", text)

    async def test_a4_web_untouched(self):
        self.assertTrue((WEB / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
