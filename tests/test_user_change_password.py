import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_auth import create_session
from server.platform_db import COOKIE_NAME
from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
FRONTEND_SRC = REPO / "frontend" / "src"


class UserChangePasswordTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        self.avatars.mkdir()
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

    async def test_a1_change_password_keeps_current_session(self):
        await self.make_user()
        await self.login("alice", "alice12")
        changed = await self.client.post(
            "/api/v1/auth/password",
            json={"current_password": "alice12", "new_password": "alice99"},
        )
        self.assertEqual(changed.status, 200, await changed.text())
        me = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status, 200)
        await self.client.post("/api/v1/auth/logout")
        old = await self.login("alice", "alice12")
        self.assertEqual(old.status, 401)
        ok = await self.login("alice", "alice99")
        self.assertEqual(ok.status, 200)

    async def test_a2_wrong_current_and_short_new(self):
        await self.make_user()
        await self.login("alice", "alice12")
        bad = await self.client.post(
            "/api/v1/auth/password",
            json={"current_password": "nope123", "new_password": "alice99"},
        )
        self.assertEqual(bad.status, 400)
        short = await self.client.post(
            "/api/v1/auth/password",
            json={"current_password": "alice12", "new_password": "ab"},
        )
        self.assertEqual(short.status, 400)
        await self.client.post("/api/v1/auth/logout")
        still = await self.login("alice", "alice12")
        self.assertEqual(still.status, 200)

    async def test_a3_anon_forbidden(self):
        anon = await self.client.post(
            "/api/v1/auth/password",
            json={"current_password": "secret12", "new_password": "secret99"},
        )
        self.assertEqual(anon.status, 401)

    async def test_a4_both_shells_and_no_admin_reset_others(self):
        admin_layout = (FRONTEND_SRC / "layouts" / "AdminLayout.vue").read_text()
        user_layout = (FRONTEND_SRC / "layouts" / "UserLayout.vue").read_text()
        form = (FRONTEND_SRC / "components" / "PasswordForm.vue").read_text()
        ops = (FRONTEND_SRC / "views" / "admin" / "Ops.vue").read_text()
        self.assertIn("PasswordForm", admin_layout)
        self.assertIn("PasswordForm", user_layout)
        self.assertIn("改密", form)
        self.assertIn("初始密码", ops)
        self.assertNotIn("改密", ops)
        await self.login("admin", "secret12")
        changed = await self.client.post(
            "/api/v1/auth/password",
            json={"current_password": "secret12", "new_password": "secret99"},
        )
        self.assertEqual(changed.status, 200)

    async def test_a5_other_sessions_revoked(self):
        uid = await self.make_user()
        db = self.app["platform_db"]
        other = await create_session(db, uid)
        await self.login("alice", "alice12")
        changed = await self.client.post(
            "/api/v1/auth/password",
            json={"current_password": "alice12", "new_password": "alice99"},
        )
        self.assertEqual(changed.status, 200)
        stale = await self.client.get(
            "/api/v1/auth/me",
            headers={"Cookie": f"{COOKIE_NAME}={other}"},
        )
        # TestClient may still send the live cookie; call with a fresh client cookie override
        # by using the same jar is unreliable, so query DB instead if header is ignored.
        if stale.status == 200:
            async with db.execute("SELECT token FROM sessions WHERE token = ?", (other,)) as cur:
                row = await cur.fetchone()
            self.assertIsNone(row)
        else:
            self.assertEqual(stale.status, 401)
        page = (WEB / "avatar.html").read_text()
        self.assertTrue(page)


if __name__ == "__main__":
    unittest.main()
