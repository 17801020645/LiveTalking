import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application
from server.task_manager import INTERRUPTED_MSG, task_manager

WEB = Path(__file__).resolve().parents[1] / "web"
FRONTEND_TTS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "views" / "admin" / "Tts.vue"


class PlatformHardeningTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.avatars = self.root / "avatars"
        self.avatars.mkdir()
        self.db_path = str(self.root / "p.db")
        os.environ["LIVETALKING_BOOTSTRAP_ADMIN"] = "admin"
        os.environ["LIVETALKING_BOOTSTRAP_PASSWORD"] = "secret12"
        os.environ.pop("LIVETALKING_CORS_ORIGINS", None)
        os.environ.pop("LIVETALKING_TTS_UPSTREAM", None)
        self.client = None
        self.fake_tts = None

    async def asyncTearDown(self):
        if self.client:
            await self.client.close()
        if self.fake_tts:
            await self.fake_tts.close()
        os.environ.pop("LIVETALKING_CORS_ORIGINS", None)
        os.environ.pop("LIVETALKING_TTS_UPSTREAM", None)
        self.tmp.cleanup()

    async def start_app(self):
        if self.client:
            await self.client.close()
        app = create_test_application(self.db_path, str(self.avatars), web_dir=str(WEB))
        self.client = TestClient(TestServer(app))
        await self.client.start_server()
        return self.client

    async def login(self, username="admin", password="secret12"):
        return await self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    def origin_for_client(self):
        host = self.client.server.host
        port = self.client.server.port
        return f"http://{host}:{port}"

    async def test_a1_tasks_survive_restart(self):
        await self.start_app()
        task_id = task_manager.add_task(
            "wav2lip", "alice", {"video_path": "/tmp/x.mp4"}, run=False
        )
        task = task_manager.get_task(task_id)
        task.status = "completed"
        task.progress = 100
        task_manager.persist_task(task)

        await self.start_app()
        await self.login()
        listed = await self.client.get("/api/avatar/tasks")
        self.assertEqual(listed.status, 200)
        tasks = (await listed.json())["data"]["tasks"]
        found = next(t for t in tasks if t["task_id"] == task_id)
        self.assertEqual(found["status"], "completed")
        self.assertEqual(found["avatar_id"], "alice")
        self.assertEqual(found["progress"], 100)

    async def test_a2_interrupted_tasks_fail_on_boot(self):
        await self.start_app()
        await self.client.close()
        self.client = None
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO avatar_tasks (
                task_id, model_type, avatar_id, params, status, progress,
                error_msg, notify_url, start_time, end_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("t-open", "wav2lip", "bob", "{}", "running", 40, "", None, 1.0, None),
        )
        conn.commit()
        conn.close()

        await self.start_app()
        await self.login()
        listed = await self.client.get("/api/avatar/tasks")
        tasks = (await listed.json())["data"]["tasks"]
        found = next(t for t in tasks if t["task_id"] == "t-open")
        self.assertEqual(found["status"], "failed")
        self.assertIn("进程中断", found["error_msg"])
        self.assertEqual(found["error_msg"], INTERRUPTED_MSG)

    async def test_a3_healthz_public(self):
        await self.start_app()
        resp = await self.client.get("/healthz")
        self.assertEqual(resp.status, 200)
        body = await resp.json()
        self.assertTrue(body.get("ok"))
        dumped = json.dumps(body)
        self.assertNotIn("secret12", dumped)
        self.assertNotIn("LIVETALKING_BOOTSTRAP", dumped)
        self.assertNotIn("lt_session", dumped)

    async def test_a4_cors_host_and_deny_star(self):
        await self.start_app()
        origin = self.origin_for_client()
        ok = await self.client.get("/healthz", headers={"Origin": origin})
        self.assertEqual(ok.headers.get("Access-Control-Allow-Origin"), origin)
        self.assertEqual(ok.headers.get("Access-Control-Allow-Credentials"), "true")

        bad = await self.client.get("/healthz", headers={"Origin": "http://evil.example"})
        acao = bad.headers.get("Access-Control-Allow-Origin")
        self.assertNotEqual(acao, "*")
        self.assertNotEqual(acao, "http://evil.example")

        preflight = await self.client.options(
            "/api/v1/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(preflight.status, 204)
        self.assertEqual(preflight.headers.get("Access-Control-Allow-Origin"), origin)

    async def test_a5_cors_env_allowlist(self):
        os.environ["LIVETALKING_CORS_ORIGINS"] = "http://localhost:5173"
        await self.start_app()
        extra = await self.client.get(
            "/healthz",
            headers={"Origin": "http://localhost:5173"},
        )
        self.assertEqual(extra.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        self.assertEqual(extra.headers.get("Access-Control-Allow-Credentials"), "true")

    async def _start_fake_omni(self, down=False):
        app = web.Application()

        async def voices(_request):
            return web.json_response({"voices": ["vivian"], "uploaded_voices": []})

        async def speech(_request):
            return web.Response(body=b"ID3FAKEAUDIO", content_type="audio/mpeg")

        if not down:
            app.router.add_get("/v1/audio/voices", voices)
            app.router.add_post("/v1/audio/speech", speech)
        self.fake_tts = TestClient(TestServer(app))
        await self.fake_tts.start_server()
        host = self.fake_tts.server.host
        port = self.fake_tts.server.port
        os.environ["LIVETALKING_TTS_UPSTREAM"] = f"http://{host}:{port}"

    async def test_a6_admin_tts_voices_via_proxy(self):
        await self._start_fake_omni()
        await self.start_app()
        await self.login()
        resp = await self.client.get("/api/v1/admin/tts/voices")
        self.assertEqual(resp.status, 200)
        data = (await resp.json())["data"]
        self.assertIn("vivian", data["voices"])
        page = FRONTEND_TTS.read_text()
        self.assertIn("/api/v1/admin/tts/voices", page)
        self.assertNotIn("8091", page)

    async def test_a7_speech_ok_and_upstream_down(self):
        await self._start_fake_omni()
        await self.start_app()
        await self.login()
        ok = await self.client.post(
            "/api/v1/admin/tts/speech",
            json={"input": "你好", "voice": "vivian"},
        )
        self.assertEqual(ok.status, 200)
        self.assertEqual(await ok.read(), b"ID3FAKEAUDIO")

        await self.fake_tts.close()
        self.fake_tts = None
        os.environ["LIVETALKING_TTS_UPSTREAM"] = "http://127.0.0.1:1"
        down = await self.client.post(
            "/api/v1/admin/tts/speech",
            json={"input": "你好", "voice": "vivian"},
        )
        self.assertEqual(down.status, 502)
        self.assertIn("上游", (await down.json())["msg"])

    async def test_a8_tts_authz(self):
        await self.start_app()
        anon = await self.client.get("/api/v1/admin/tts/voices")
        self.assertEqual(anon.status, 401)
        await self.login()
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "alice", "password": "alice12"},
        )
        self.assertEqual(created.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        forbidden = await self.client.get("/api/v1/admin/tts/voices")
        self.assertEqual(forbidden.status, 403)


if __name__ == "__main__":
    unittest.main()
