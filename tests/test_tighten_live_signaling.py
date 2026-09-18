import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
ADMIN_LIVE = REPO / "frontend" / "src" / "views" / "admin" / "Live.vue"
PRODUCT = REPO / "PRODUCT.md"


class TightenLiveSignalingTests(unittest.IsolatedAsyncioTestCase):
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

    async def publish_stock(self, uid, name="alice"):
        await self.login("admin", "secret12")
        await self.client.post(
            f"/api/v1/admin/users/{uid}/subscriptions",
            json={"avatar_id": "stock"},
        )
        await self.client.post("/api/v1/auth/logout")
        await self.login(name, "alice12")
        await self.client.post("/api/v1/me/avatars/stock/publish")

    def drive(self, sid, text="你好"):
        return {
            "text": text,
            "type": "echo",
            "interrupt": True,
            "sessionid": sid,
        }

    async def test_a1_anonymous_offer_and_web(self):
        offer = await self.client.post("/offer", json={"sdp": "x", "type": "offer", "avatar": "stock"})
        self.assertEqual(offer.status, 200)
        sid = (await offer.json())["sessionid"]
        human = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(human.status, 200)
        self.assertTrue((WEB / "index.html").is_file())
        result = subprocess.run(
            ["git", "diff", "--exit-code", "--", "web/"],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    async def test_a2_admin_offer_authz(self):
        anon = await self.client.post(
            "/api/v1/admin/offer",
            json={"sdp": "x", "type": "offer", "avatar": "stock"},
        )
        self.assertEqual(anon.status, 401)
        uid = await self.make_user()
        await self.publish_stock(uid)
        forbidden = await self.client.post(
            "/api/v1/admin/offer",
            json={"sdp": "x", "type": "offer", "avatar": "stock"},
        )
        self.assertEqual(forbidden.status, 403)
        src = ADMIN_LIVE.read_text(encoding="utf-8")
        self.assertIn("/api/v1/admin/offer", src)
        self.assertNotIn("fetch('/offer'", src)
        self.assertIn("/api/v1/admin/hangup", src)
        self.assertIn("匿名", PRODUCT.read_text(encoding="utf-8"))
        self.assertIn("/api/v1/admin/offer", PRODUCT.read_text(encoding="utf-8"))

    async def test_a3_user_bound_session_requires_owner(self):
        uid = await self.make_user()
        await self.publish_stock(uid)
        offered = await self.client.post("/api/v1/me/offer", json={"sdp": "x", "type": "offer"})
        self.assertEqual(offered.status, 200)
        sid = (await offered.json())["data"]["sessionid"]
        ok = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(ok.status, 200)
        await self.client.post("/api/v1/auth/logout")
        anon = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(anon.status, 401)
        interrupt = await self.client.post("/interrupt_talk", json={"sessionid": sid})
        self.assertEqual(interrupt.status, 401)
        rec = await self.client.post("/record", json={"type": "start_record", "sessionid": sid})
        self.assertEqual(rec.status, 401)
        switched = await self.client.post("/set_audiotype", json={"audiotype": 2, "sessionid": sid})
        self.assertEqual(switched.status, 401)
        form = FormData()
        form.add_field("sessionid", sid)
        form.add_field("file", b"RIFF", filename="clip.wav", content_type="audio/wav")
        uploaded = await self.client.post("/humanaudio", data=form)
        self.assertEqual(uploaded.status, 401)
        download = await self.client.get(f"/record/{sid}")
        self.assertEqual(download.status, 401)
        await self.make_user("bob")
        await self.login("bob", "alice12")
        other = await self.client.post("/human", json=self.drive(sid, "偷说"))
        self.assertEqual(other.status, 403)

    async def test_a4_admin_bound_session_requires_owner(self):
        await self.login("admin", "secret12")
        offered = await self.client.post(
            "/api/v1/admin/offer",
            json={"sdp": "x", "type": "offer", "avatar": "stock", "refaudio": "vivian"},
        )
        self.assertEqual(offered.status, 200)
        self.assertEqual(self.app["last_admin_offer"]["avatar"], "stock")
        sid = (await offered.json())["data"]["sessionid"]
        ok = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(ok.status, 200)
        await self.client.post("/api/v1/auth/logout")
        anon = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(anon.status, 401)
        uid = await self.make_user()
        await self.login("alice", "alice12")
        other = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(other.status, 403)
        await self.client.post("/api/v1/auth/logout")
        await self.login("admin", "secret12")
        again = await self.client.post("/human", json=self.drive(sid))
        self.assertEqual(again.status, 200)
        await self.client.post("/api/v1/admin/hangup")
        # after hangup the session is unbound; anonymous drive of that sid is allowed
        # (stub does not keep a live engine session)


if __name__ == "__main__":
    unittest.main()
