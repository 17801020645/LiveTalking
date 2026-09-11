import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
FRONTEND_SRC = REPO / "frontend" / "src"


class UserLiveTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        (self.avatars / "stock").mkdir(parents=True)
        os.environ["LIVETALKING_BOOTSTRAP_ADMIN"] = "admin"
        os.environ["LIVETALKING_BOOTSTRAP_PASSWORD"] = "secret12"
        app = create_test_application(str(root / "p.db"), str(self.avatars), web_dir=str(WEB))
        self.app = app
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

    async def make_user(self, name="alice"):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": name, "password": "alice12"},
        )
        uid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")
        return uid

    async def test_a1_auth_and_unpublished(self):
        anon = await self.client.post("/api/v1/me/offer", json={"sdp": "x", "type": "offer"})
        self.assertEqual(anon.status, 401)
        await self.make_user()
        await self.login("alice", "alice12")
        denied = await self.client.post("/api/v1/me/offer", json={"sdp": "x", "type": "offer"})
        self.assertEqual(denied.status, 400)
        self.assertIn("发布", (await denied.json())["msg"])
        home = (FRONTEND_SRC / "views" / "user" / "Home.vue").read_text()
        self.assertIn("我的资产", home)

    async def test_a2_a4_published_avatar_forced(self):
        uid = await self.make_user()
        await self.login("admin", "secret12")
        await self.client.post(
            f"/api/v1/admin/users/{uid}/subscriptions",
            json={"avatar_id": "stock"},
        )
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        unbound = await self.client.post(
            "/api/v1/me/offer",
            json={"sdp": "x", "type": "offer", "avatar": "stock"},
        )
        self.assertEqual(unbound.status, 400)
        await self.client.post("/api/v1/me/avatars/stock/publish")
        ok = await self.client.post(
            "/api/v1/me/offer",
            json={"sdp": "x", "type": "offer", "avatar": "someone_else"},
        )
        self.assertEqual(ok.status, 200)
        data = (await ok.json())["data"]
        self.assertEqual(data["avatar_id"], "stock")
        self.assertTrue(data["sessionid"])
        self.assertEqual(self.app["last_me_offer"]["avatar"], "stock")
        self.assertEqual(self.app["last_me_offer"]["client_avatar"], "someone_else")

    async def test_a3_human_uses_sessionid(self):
        uid = await self.make_user()
        await self.login("admin", "secret12")
        await self.client.post(
            f"/api/v1/admin/users/{uid}/subscriptions",
            json={"avatar_id": "stock"},
        )
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        await self.client.post("/api/v1/me/avatars/stock/publish")
        offered = await self.client.post("/api/v1/me/offer", json={"sdp": "x", "type": "offer"})
        sid = (await offered.json())["data"]["sessionid"]
        human = await self.client.post(
            "/human",
            json={"text": "你好", "type": "echo", "interrupt": True, "sessionid": sid},
        )
        self.assertEqual(human.status, 200)
        self.assertEqual(self.app["last_human"]["sessionid"], sid)
        self.assertEqual(self.app["last_human"]["text"], "你好")
        home = (FRONTEND_SRC / "views" / "user" / "Home.vue").read_text()
        self.assertIn("/human", home)
        self.assertIn("sessionid", home)

    async def test_a5_legacy_offer_and_web(self):
        offer = await self.client.post("/offer", json={})
        self.assertEqual(offer.status, 200)
        self.assertTrue((WEB / "index.html").is_file())
        page = await self.client.get("/avatar.html")
        self.assertEqual(page.status, 200)

    async def test_a6_admin_live_uses_legacy_offer(self):
        admin_home = (FRONTEND_SRC / "views" / "admin" / "Home.vue").read_text()
        admin_live = (FRONTEND_SRC / "views" / "admin" / "Live.vue").read_text()
        self.assertIn("去演示连麦", admin_home)
        self.assertNotIn("开始连接", admin_home)
        self.assertIn("打开 /", admin_live)
        self.assertNotIn("/api/v1/me/offer", admin_live)
        self.assertNotIn("开始连麦", admin_live)
        self.assertIn("开始连接", admin_live)
        await self.login("admin", "secret12")
        forbidden = await self.client.post("/api/v1/me/offer", json={"sdp": "x", "type": "offer"})
        self.assertEqual(forbidden.status, 403)


if __name__ == "__main__":
    unittest.main()
