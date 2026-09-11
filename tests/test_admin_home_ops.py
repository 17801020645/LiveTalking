import os
import tempfile
import unittest
from pathlib import Path

from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application
from server.session_manager import session_manager
from server.task_manager import task_manager

WEB = Path(__file__).resolve().parents[1] / "web"
FRONTEND_HOME = Path(__file__).resolve().parents[1] / "frontend" / "src" / "views" / "admin" / "Home.vue"


class AdminHomeOpsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        self.avatars.mkdir()
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
        self._session_ids = []

    async def asyncTearDown(self):
        for sid in self._session_ids:
            session_manager.remove_session(sid)
        await self.client.close()
        self.tmp.cleanup()

    async def login(self, username="admin", password="secret12"):
        return await self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    def video_form(self):
        data = FormData()
        data.add_field("material_type", "video")
        data.add_field("script_text", "hi")
        data.add_field("video", b"\x00\x00mp4", filename="clip.mp4", content_type="video/mp4")
        return data

    async def test_a1_admin_sees_counts(self):
        await self.login()
        resp = await self.client.get("/api/v1/admin/home")
        self.assertEqual(resp.status, 200)
        data = (await resp.json())["data"]
        for key in ("pending_orders", "active_sessions", "max_sessions", "running_tasks"):
            self.assertIn(key, data)
        page = FRONTEND_HOME.read_text()
        self.assertIn("待处理订单", page)
        self.assertIn("活跃连麦", page)
        self.assertIn("生成中任务", page)
        self.assertIn("去演示连麦", page)
        self.assertNotIn("开始连麦", page)
        self.assertNotIn("开始连接", page)

    async def test_a2_pending_orders_and_link(self):
        await self.login()
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "alice", "password": "alice12"},
        )
        self.assertEqual(created.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        await self.client.post("/api/v1/me/orders", data=self.video_form())
        await self.client.post("/api/v1/auth/logout")
        await self.login()
        data = (await (await self.client.get("/api/v1/admin/home")).json())["data"]
        self.assertGreaterEqual(data["pending_orders"], 1)
        page = FRONTEND_HOME.read_text()
        self.assertIn("to=\"/admin/ops\"", page)

    async def test_a3_active_sessions(self):
        await self.login()
        empty = (await (await self.client.get("/api/v1/admin/home")).json())["data"]
        self.assertEqual(empty["active_sessions"], session_manager.active_count())
        sid = "home-ops-test-sid"
        session_manager.sessions[sid] = object()
        self._session_ids.append(sid)
        filled = (await (await self.client.get("/api/v1/admin/home")).json())["data"]
        self.assertEqual(filled["active_sessions"], session_manager.active_count())
        self.assertGreaterEqual(filled["active_sessions"], 1)

    async def test_a4_running_tasks_and_link(self):
        await self.login()
        task_manager.add_task("wav2lip", "x", {"video_path": "/tmp/x.mp4"}, run=False)
        data = (await (await self.client.get("/api/v1/admin/home")).json())["data"]
        self.assertGreaterEqual(data["running_tasks"], 1)
        page = FRONTEND_HOME.read_text()
        self.assertIn("to=\"/admin/avatar\"", page)

    async def test_a5_authz(self):
        anon = await self.client.get("/api/v1/admin/home")
        self.assertEqual(anon.status, 401)
        await self.login()
        await self.client.post(
            "/api/v1/admin/users",
            json={"username": "bob", "password": "alice12"},
        )
        await self.client.post("/api/v1/auth/logout")
        await self.login("bob", "alice12")
        forbidden = await self.client.get("/api/v1/admin/home")
        self.assertEqual(forbidden.status, 403)
        user_home = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "views" / "user" / "Home.vue").read_text()
        self.assertIn("开始连麦", user_home)


if __name__ == "__main__":
    unittest.main()
