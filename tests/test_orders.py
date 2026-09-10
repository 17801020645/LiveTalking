import os
import tempfile
import unittest
from pathlib import Path

from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

WEB = Path(__file__).resolve().parents[1] / "web"


class OrderFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        self.avatars.mkdir()
        (self.avatars / "stock").mkdir()
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
        return await self.client.post("/api/v1/auth/login", json={"username": username, "password": password})

    async def make_user(self, name="alice"):
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": name, "password": "alice12"},
        )
        uid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")
        return uid

    def video_form(self, text="hi"):
        data = FormData()
        data.add_field("material_type", "video")
        data.add_field("script_text", text)
        data.add_field("video", b"\x00\x00mp4", filename="clip.mp4", content_type="video/mp4")
        return data

    def image_audio_form(self):
        data = FormData()
        data.add_field("material_type", "image_audio")
        data.add_field("script_text", "clone")
        data.add_field("image", b"\xff\xd8\xff", filename="face.jpg", content_type="image/jpeg")
        data.add_field("audio", b"RIFF", filename="voice.wav", content_type="audio/wav")
        return data

    async def test_a1_user_submit_admin_forbidden(self):
        await self.make_user()
        await self.login("admin", "secret12")
        denied = await self.client.post("/api/v1/me/orders", data=self.video_form())
        self.assertEqual(denied.status, 403)
        await self.client.post("/api/v1/auth/logout")
        anon = await self.client.post("/api/v1/me/orders", data=self.video_form())
        self.assertEqual(anon.status, 401)
        await self.login("alice", "alice12")
        ok = await self.client.post("/api/v1/me/orders", data=self.video_form())
        self.assertEqual(ok.status, 200)
        self.assertEqual((await ok.json())["data"]["status"], "submitted")

    async def test_a2_isolation_and_avatar_task_forbidden(self):
        await self.make_user("alice")
        await self.make_user("bob")
        await self.login("alice", "alice12")
        await self.client.post("/api/v1/me/orders", data=self.video_form("a"))
        mine = await self.client.get("/api/v1/me/orders")
        self.assertEqual(len((await mine.json())["data"]["orders"]), 1)
        task = await self.client.post("/api/avatar/task", json={"model": "wav2lip", "avatar_id": "x"})
        self.assertEqual(task.status, 403)
        await self.client.post("/api/v1/auth/logout")
        await self.login("bob", "alice12")
        other = await self.client.get("/api/v1/me/orders")
        self.assertEqual((await other.json())["data"]["orders"], [])

    async def test_a3_accept_reject(self):
        await self.make_user()
        await self.login("alice", "alice12")
        created = await self.client.post("/api/v1/me/orders", data=self.video_form())
        oid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")
        await self.login("admin", "secret12")
        acc = await self.client.post(f"/api/v1/admin/orders/{oid}/accept")
        self.assertEqual(acc.status, 200)
        await self.login("alice", "alice12")
        await self.client.post("/api/v1/me/orders", data=self.video_form("two"))
        await self.client.post("/api/v1/auth/logout")
        await self.login("admin", "secret12")
        listed = await self.client.get("/api/v1/admin/orders")
        second = [o for o in (await listed.json())["data"]["orders"] if o["status"] == "submitted"][0]
        rej = await self.client.post(
            f"/api/v1/admin/orders/{second['id']}/reject",
            json={"reason": "素材不清"},
        )
        self.assertEqual(rej.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        mine = await self.client.get("/api/v1/me/orders")
        reasons = {o["id"]: o.get("reject_reason") for o in (await mine.json())["data"]["orders"]}
        self.assertEqual(reasons[second["id"]], "素材不清")

    async def test_a4_generate_binds_unpublished(self):
        await self.make_user()
        await self.login("alice", "alice12")
        created = await self.client.post("/api/v1/me/orders", data=self.video_form())
        oid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")
        await self.login("admin", "secret12")
        await self.client.post(f"/api/v1/admin/orders/{oid}/accept")
        gen = await self.client.post(
            f"/api/v1/admin/orders/{oid}/generate",
            json={"avatar_id": "alice_custom", "model": "wav2lip"},
        )
        self.assertEqual(gen.status, 200, await gen.text())
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        assets = await self.client.get("/api/v1/me/avatars")
        avatars = (await assets.json())["data"]["avatars"]
        self.assertEqual([a["avatar_id"] for a in avatars], ["alice_custom"])
        self.assertFalse(avatars[0]["is_published"])
        home = await self.client.get("/api/v1/me/home")
        self.assertIsNone((await home.json())["data"]["published"])

    async def test_a5_image_audio_cannot_generate(self):
        await self.make_user()
        await self.login("alice", "alice12")
        created = await self.client.post("/api/v1/me/orders", data=self.image_audio_form())
        self.assertEqual(created.status, 200, await created.text())
        oid = (await created.json())["data"]["id"]
        await self.client.post("/api/v1/auth/logout")
        await self.login("admin", "secret12")
        acc = await self.client.post(f"/api/v1/admin/orders/{oid}/accept")
        self.assertEqual(acc.status, 200)
        gen = await self.client.post(
            f"/api/v1/admin/orders/{oid}/generate",
            json={"avatar_id": "nope", "model": "wav2lip"},
        )
        self.assertEqual(gen.status, 400)
        self.assertIn("视频", (await gen.json())["msg"])

    async def test_a6_legacy_and_assets_still_work(self):
        page = await self.client.get("/avatar.html")
        self.assertEqual(page.status, 200)
        offer = await self.client.post("/offer", json={})
        self.assertEqual(offer.status, 200)
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "cara", "password": "cara123"},
        )
        uid = (await created.json())["data"]["id"]
        await self.client.post(f"/api/v1/admin/users/{uid}/subscriptions", json={"avatar_id": "stock"})
        await self.client.post("/api/v1/auth/logout")
        await self.login("cara", "cara123")
        pub = await self.client.post("/api/v1/me/avatars/stock/publish")
        self.assertEqual(pub.status, 200)
        home = await self.client.get("/api/v1/me/home")
        self.assertEqual((await home.json())["data"]["published"]["avatar_id"], "stock")


if __name__ == "__main__":
    unittest.main()
