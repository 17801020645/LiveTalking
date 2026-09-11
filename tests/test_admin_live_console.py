import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
FRONTEND_SRC = REPO / "frontend" / "src"
ADMIN_HOME = FRONTEND_SRC / "views" / "admin" / "Home.vue"
ADMIN_LIVE = FRONTEND_SRC / "views" / "admin" / "Live.vue"
ADMIN_LAYOUT = FRONTEND_SRC / "layouts" / "AdminLayout.vue"


class AdminLiveConsoleTests(unittest.IsolatedAsyncioTestCase):
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

    async def login(self, username="admin", password="secret12"):
        return await self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    async def test_a1_home_todos_only(self):
        page = ADMIN_HOME.read_text()
        for label in ("待处理订单", "活跃连麦", "生成中任务", "去演示连麦"):
            self.assertIn(label, page)
        self.assertNotIn("开始连接", page)
        self.assertNotIn("发送文字", page)
        self.assertNotIn("打断", page)
        self.assertNotIn("/offer", page)

    async def test_a2_live_page_and_nav(self):
        layout = ADMIN_LAYOUT.read_text()
        self.assertLess(layout.find("演示连麦"), layout.find("Avatar 生成"))
        self.assertIn('to="/admin/live"', layout)
        page = ADMIN_LIVE.read_text()
        for label in ("请选择形象", "开始连接", "发送文字", "打断", "打开 /", "Echo 复读", "Chat LLM"):
            self.assertIn(label, page)
        self.assertIn("starting || !avatarId", page)
        self.assertIn("btn-interrupt", page)
        self.assertIn("is-fired", page)
        self.assertIn("已停止讲话", page)
        self.assertNotIn("avatars.value[0]", page)
        self.assertNotIn("/humanaudio", page)
        self.assertNotIn("/record", page)
        self.assertNotIn("/set_audiotype", page)

    async def test_a3_offer_uses_selected_avatar_and_human_echo(self):
        await self.login()
        listed = await self.client.get("/api/v1/admin/avatars")
        ids = [a["avatar_id"] for a in (await listed.json())["data"]["avatars"]]
        self.assertIn("stock", ids)
        offered = await self.client.post(
            "/offer",
            json={"sdp": "x", "type": "offer", "avatar": "stock"},
        )
        self.assertEqual(offered.status, 200)
        self.assertEqual(self.app["last_offer"]["avatar"], "stock")
        sid = (await offered.json())["sessionid"]
        human = await self.client.post(
            "/human",
            json={"text": "你好", "type": "echo", "interrupt": True, "sessionid": sid},
        )
        self.assertEqual(human.status, 200)
        self.assertEqual(self.app["last_human"]["type"], "echo")
        self.assertEqual(self.app["last_human"]["sessionid"], sid)
        page = ADMIN_LIVE.read_text()
        self.assertIn("fetch('/offer'", page)
        self.assertIn("avatar: avatarId.value", page)
        self.assertIn("type: talkType.value", page)
        self.assertIn("Chat LLM", page)

    async def test_a4_interrupt(self):
        page = ADMIN_LIVE.read_text()
        self.assertIn("/interrupt_talk", page)
        await self.client.post("/interrupt_talk", json={"sessionid": "legacy-sid"})
        self.assertEqual(self.app["last_interrupt"]["sessionid"], "legacy-sid")

    async def test_a5_user_home_unchanged(self):
        user_home = (FRONTEND_SRC / "views" / "user" / "Home.vue").read_text()
        self.assertIn("开始连麦", user_home)
        self.assertIn("/api/v1/me/offer", user_home)
        await self.login()
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "alice", "password": "alice12"},
        )
        self.assertEqual(created.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        forbidden = await self.client.get("/api/v1/admin/avatars")
        self.assertEqual(forbidden.status, 403)

    async def test_a6_legacy_offer_and_web(self):
        offer = await self.client.post("/offer", json={})
        self.assertEqual(offer.status, 200)
        page = await self.client.get("/avatar.html")
        self.assertEqual(page.status, 200)
        self.assertTrue((WEB / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
