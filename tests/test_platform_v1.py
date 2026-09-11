import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
FRONTEND_SRC = REPO / "frontend" / "src"


class PlatformV1Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        (self.avatars / "alice").mkdir(parents=True)
        (self.avatars / "bob").mkdir()
        (self.avatars / "alice" / "cover.jpg").write_bytes(b"\xff\xd8\xff")
        (self.avatars / "charlie").mkdir()
        os.environ["LIVETALKING_BOOTSTRAP_ADMIN"] = "admin"
        os.environ["LIVETALKING_BOOTSTRAP_PASSWORD"] = "secret12"
        app = create_test_application(str(root / "p.db"), str(self.avatars), web_dir=str(WEB))
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

    async def test_a1_me_and_wrong_password(self):
        me = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status, 401)
        bad = await self.login("admin", "nope")
        self.assertEqual(bad.status, 401)
        ok = await self.login("admin", "secret12")
        self.assertEqual(ok.status, 200)
        me2 = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me2.status, 200)
        self.assertEqual((await me2.json())["data"]["role"], "admin")

    async def test_a2_a3_roles(self):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "alice", "password": "alice12"},
        )
        self.assertEqual(created.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        forbidden = await self.client.get("/api/v1/admin/users")
        self.assertEqual(forbidden.status, 403)
        layout = (FRONTEND_SRC / "layouts" / "AdminLayout.vue").read_text()
        for label in ("首页", "演示连麦", "Avatar 生成", "管理后台", "TTS 语音管理"):
            self.assertIn(label, layout)
        user_layout = (FRONTEND_SRC / "layouts" / "UserLayout.vue").read_text()
        for label in ("首页", "我的资产", "定制数字人"):
            self.assertIn(label, user_layout)

    async def test_a4_bind_and_isolation(self):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "bobuser", "password": "bobusr1"},
        )
        uid = (await created.json())["data"]["id"]
        bind = await self.client.post(
            f"/api/v1/admin/users/{uid}/subscriptions",
            json={"avatar_id": "alice"},
        )
        self.assertEqual(bind.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("bobuser", "bobusr1")
        listed = await self.client.get("/api/v1/me/avatars")
        ids = [a["avatar_id"] for a in (await listed.json())["data"]["avatars"]]
        self.assertEqual(ids, ["alice"])
        self.assertNotIn("bob", ids)
        self.assertNotIn("charlie", ids)
        missing = await self.client.get("/api/v1/media/avatars/bob/cover")
        self.assertEqual(missing.status, 404)

    async def test_a5_publish_single(self):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "cara", "password": "cara123"},
        )
        uid = (await created.json())["data"]["id"]
        await self.client.post(f"/api/v1/admin/users/{uid}/subscriptions", json={"avatar_id": "alice"})
        await self.client.post(f"/api/v1/admin/users/{uid}/subscriptions", json={"avatar_id": "bob"})
        await self.client.post("/api/v1/auth/logout")
        await self.login("cara", "cara123")
        home0 = await self.client.get("/api/v1/me/home")
        self.assertIsNone((await home0.json())["data"]["published"])
        await self.client.post("/api/v1/me/avatars/alice/publish")
        home1 = await self.client.get("/api/v1/me/home")
        self.assertEqual((await home1.json())["data"]["published"]["avatar_id"], "alice")
        await self.client.post("/api/v1/me/avatars/bob/publish")
        home2 = await self.client.get("/api/v1/me/home")
        self.assertEqual((await home2.json())["data"]["published"]["avatar_id"], "bob")
        assets = await self.client.get("/api/v1/me/avatars")
        published = {a["avatar_id"]: a["is_published"] for a in (await assets.json())["data"]["avatars"]}
        self.assertFalse(published["alice"])
        self.assertTrue(published["bob"])

    async def test_a6_legacy_anonymous(self):
        root = await self.client.get("/", allow_redirects=False)
        self.assertIn(root.status, (200, 302, 301))
        page = await self.client.get("/avatar.html")
        self.assertEqual(page.status, 200)
        offer = await self.client.post("/offer", json={})
        self.assertEqual(offer.status, 200)
        task = await self.client.post("/api/avatar/task", json={})
        self.assertEqual(task.status, 401)

    async def test_a7_frontend_dir_and_web_untouched_markers(self):
        self.assertTrue((REPO / "frontend" / "src" / "layouts" / "AdminLayout.vue").is_file())
        self.assertTrue((WEB / "index.html").is_file())
        self.assertTrue((WEB / "avatar.html").is_file())
        spa = await self.client.get("/app/")
        self.assertIn(spa.status, (200, 503))
        router = (FRONTEND_SRC / "router" / "index.js").read_text()
        self.assertIn("path: '/login'", router)
        self.assertIn("redirect: to.fullPath", router)


if __name__ == "__main__":
    unittest.main()
