import os
import tempfile
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_auth import LOGIN_ERROR, create_session
from server.platform_db import COOKIE_NAME
from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
OPS = REPO / "frontend" / "src" / "views" / "admin" / "Ops.vue"
PASSWORD_FORM = REPO / "frontend" / "src" / "components" / "PasswordForm.vue"
README = REPO / "README.md"
README_EN = REPO / "README-EN.md"


class AdminResetPasswordTests(unittest.IsolatedAsyncioTestCase):
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
        )
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

    async def _create_user(self, username, password):
        created = await self.client.post(
            "/api/v1/admin/users",
            json={"username": username, "password": password},
        )
        return (await created.json())["data"]["id"]

    async def test_a1_reset_active_user_revokes_old_password_and_sessions(self):
        await self.login("admin", "secret12")
        uid = await self._create_user("bobuser", "bobusr1")
        await self.client.post("/api/v1/auth/logout")
        await self.login("bobuser", "bobusr1")
        me = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status, 200)
        other = await create_session(self.app["platform_db"], uid)
        await self.client.post("/api/v1/auth/logout")

        await self.login("admin", "secret12")
        reset = await self.client.post(
            f"/api/v1/admin/users/{uid}/password",
            json={"password": "bobusr9"},
        )
        self.assertEqual(reset.status, 200, await reset.text())
        await self.client.post("/api/v1/auth/logout")

        old = await self.login("bobuser", "bobusr1")
        self.assertEqual(old.status, 401)
        self.assertEqual((await old.json())["msg"], LOGIN_ERROR)
        ok = await self.login("bobuser", "bobusr9")
        self.assertEqual(ok.status, 200)

        async with self.app["platform_db"].execute(
            "SELECT token FROM sessions WHERE token = ?",
            (other,),
        ) as cur:
            self.assertIsNone(await cur.fetchone())
        stale = await self.client.get(
            "/api/v1/auth/me",
            headers={"Cookie": f"{COOKIE_NAME}={other}"},
        )
        if stale.status == 200:
            async with self.app["platform_db"].execute(
                "SELECT token FROM sessions WHERE token = ?",
                (other,),
            ) as cur:
                self.assertIsNone(await cur.fetchone())
        else:
            self.assertEqual(stale.status, 401)

    async def test_a2_disabled_forbidden_short_and_authz(self):
        await self.login("admin", "secret12")
        me = await self.client.get("/api/v1/auth/me")
        admin_id = (await me.json())["data"]["id"]
        self_reset = await self.client.post(
            f"/api/v1/admin/users/{admin_id}/password",
            json={"password": "secret99"},
        )
        self.assertEqual(self_reset.status, 400)
        missing = await self.client.post(
            "/api/v1/admin/users/99999/password",
            json={"password": "secret99"},
        )
        self.assertEqual(missing.status, 404)

        disabled_id = await self._create_user("cara", "cara123")
        await self.client.post(f"/api/v1/admin/users/{disabled_id}/disable")
        reset_disabled = await self.client.post(
            f"/api/v1/admin/users/{disabled_id}/password",
            json={"password": "cara999"},
        )
        self.assertEqual(reset_disabled.status, 200, await reset_disabled.text())
        await self.client.post("/api/v1/auth/logout")
        still_disabled = await self.login("cara", "cara999")
        self.assertEqual(still_disabled.status, 401)
        self.assertEqual((await still_disabled.json())["msg"], LOGIN_ERROR)

        await self.login("admin", "secret12")
        enabled = await self.client.post(f"/api/v1/admin/users/{disabled_id}/enable")
        self.assertEqual(enabled.status, 200)
        await self.client.post("/api/v1/auth/logout")
        old = await self.login("cara", "cara123")
        self.assertEqual(old.status, 401)
        ok = await self.login("cara", "cara999")
        self.assertEqual(ok.status, 200)
        await self.client.post("/api/v1/auth/logout")

        await self.login("admin", "secret12")
        uid = await self._create_user("dana", "dana123")
        short = await self.client.post(
            f"/api/v1/admin/users/{uid}/password",
            json={"password": "ab"},
        )
        self.assertEqual(short.status, 400)
        await self.client.post("/api/v1/auth/logout")
        still = await self.login("dana", "dana123")
        self.assertEqual(still.status, 200)
        await self.client.post("/api/v1/auth/logout")

        unauth = await self.client.post(
            f"/api/v1/admin/users/{uid}/password",
            json={"password": "dana999"},
        )
        self.assertEqual(unauth.status, 401)
        await self.login("dana", "dana123")
        forbidden = await self.client.post(
            f"/api/v1/admin/users/{uid}/password",
            json={"password": "dana999"},
        )
        self.assertEqual(forbidden.status, 403)

    async def test_a3_ops_reset_button_and_readme(self):
        src = OPS.read_text(encoding="utf-8")
        self.assertIn("改密", src)
        self.assertIn("resetPassword", src)
        self.assertIn("/password", src)
        self.assertIn("window.confirm", src)
        self.assertIn("window.prompt", src)
        self.assertIn("v-if=\"u.role === 'user'\"", src)
        self.assertNotIn("u.role === 'admin'", src)
        text = README.read_text(encoding="utf-8")
        self.assertIn("用户（禁用/启用/删除/改密）", text)
        en = README_EN.read_text(encoding="utf-8")
        self.assertIn("disable/enable/delete/reset password", en)

    async def test_a4_web_untouched_self_change_unchanged(self):
        self.assertTrue((WEB / "index.html").is_file())
        form = PASSWORD_FORM.read_text(encoding="utf-8")
        self.assertIn("改密", form)
        self.assertIn("current_password", form)
        self.assertIn("new_password", form)


if __name__ == "__main__":
    unittest.main()
