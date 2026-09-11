import os
import tempfile
import unittest
from pathlib import Path

from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer

from server.platform_catalog import ensure_avatar_media
from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
FRONTEND_SRC = REPO / "frontend" / "src"


def write_frame(path: Path, color=80):
    import cv2
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), np.full((64, 64, 3), color, dtype=np.uint8))


class AvatarPreviewMediaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        self.avatars.mkdir()
        existing = self.avatars / "legacy"
        existing.mkdir()
        write_frame(existing / "full_imgs" / "00000000.png", 40)
        write_frame(existing / "full_imgs" / "00000001.png", 90)
        self.kept_cover = b"KEEP-COVER-BYTES"
        (existing / "cover.jpg").write_bytes(self.kept_cover)
        missing = self.avatars / "needsfill"
        missing.mkdir()
        write_frame(missing / "full_imgs" / "00000000.png", 120)
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

    def video_form(self):
        data = FormData()
        data.add_field("material_type", "video")
        data.add_field("script_text", "hi")
        data.add_field("video", b"\x00\x00mp4", filename="clip.mp4", content_type="video/mp4")
        return data

    async def test_a1_generate_writes_cover_and_preview(self):
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
        dest = self.avatars / "alice_custom"
        self.assertTrue((dest / "cover.jpg").is_file())
        self.assertTrue((dest / "preview.mp4").is_file())
        cover = await self.client.get("/api/v1/media/avatars/alice_custom/cover")
        preview = await self.client.get("/api/v1/media/avatars/alice_custom/preview")
        self.assertEqual(cover.status, 200)
        self.assertEqual(preview.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("alice", "alice12")
        assets = await self.client.get("/api/v1/me/avatars")
        row = (await assets.json())["data"]["avatars"][0]
        self.assertTrue(row["cover_url"])
        self.assertTrue(row["preview_url"])

    async def test_a2_assets_prefer_preview(self):
        page = (FRONTEND_SRC / "views" / "user" / "Assets.vue").read_text()
        self.assertIn("v-if=\"a.preview_url\"", page)
        self.assertIn(":poster=", page)
        self.assertIn("muted", page)
        self.assertIn("loop", page)

    async def test_a3_home_preview_before_live(self):
        page = (FRONTEND_SRC / "views" / "user" / "Home.vue").read_text()
        self.assertIn("!connected && published.preview_url", page)
        self.assertIn("!connected && !published.preview_url && published.cover_url", page)
        self.assertIn("开始连麦", page)

    async def test_a4_scan_fills_without_overwrite(self):
        legacy = self.avatars / "legacy"
        self.assertEqual((legacy / "cover.jpg").read_bytes(), self.kept_cover)
        self.assertTrue((legacy / "preview.mp4").is_file())
        needs = self.avatars / "needsfill"
        self.assertTrue((needs / "cover.jpg").is_file())
        self.assertTrue((needs / "preview.mp4").is_file())

    async def test_a5_failed_or_empty_does_not_invent_and_auth(self):
        empty = self.avatars / "emptyone"
        empty.mkdir()
        ensure_avatar_media(empty)
        self.assertFalse((empty / "cover.jpg").is_file())
        self.assertFalse((empty / "preview.mp4").is_file())
        anon = await self.client.get("/api/v1/media/avatars/needsfill/cover")
        self.assertEqual(anon.status, 401)
        await self.login("admin", "secret12")
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": "eve", "password": "alice12"},
        )
        self.assertEqual(created.status, 200)
        await self.client.post("/api/v1/auth/logout")
        await self.login("eve", "alice12")
        denied = await self.client.get("/api/v1/media/avatars/needsfill/cover")
        self.assertEqual(denied.status, 404)
        page = (WEB / "avatar.html").read_text()
        self.assertTrue(page)


if __name__ == "__main__":
    unittest.main()
