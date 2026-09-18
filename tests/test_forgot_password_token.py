import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from server.platform_auth import FORGOT_ERROR, LOGIN_ERROR, RESET_TOKEN_SECS, create_session
from server.platform_db import COOKIE_NAME
from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
LOGIN = REPO / "frontend" / "src" / "views" / "Login.vue"
OPS = REPO / "frontend" / "src" / "views" / "admin" / "Ops.vue"
PASSWORD_FORM = REPO / "frontend" / "src" / "components" / "PasswordForm.vue"
README = REPO / "README.md"
README_EN = REPO / "README-EN.md"


class ForgotPasswordTokenTests(unittest.IsolatedAsyncioTestCase):
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

    async def _issue(self, user_id):
        return await self.client.post(f"/api/v1/admin/users/{user_id}/reset-token")

    async def _forgot(self, username, token, new_password):
        return await self.client.post(
            "/api/v1/auth/forgot-password",
            json={"username": username, "token": token, "new_password": new_password},
        )

    async def test_a1_valid_token_resets_password_and_revokes_sessions(self):
        await self.login("admin", "secret12")
        uid = await self._create_user("bobuser", "bobusr1")
        await self.client.post("/api/v1/auth/logout")
        await self.login("bobuser", "bobusr1")
        other = await create_session(self.app["platform_db"], uid)
        await self.client.post("/api/v1/auth/logout")

        await self.login("admin", "secret12")
        issued = await self._issue(uid)
        self.assertEqual(issued.status, 200, await issued.text())
        payload = (await issued.json())["data"]
        token = payload["token"]
        self.assertTrue(token)
        self.assertEqual(payload["expires_in"], RESET_TOKEN_SECS)
        async with self.app["platform_db"].execute(
            "SELECT token_hash FROM password_reset_tokens WHERE user_id = ?",
            (uid,),
        ) as cur:
            stored = await cur.fetchone()
        self.assertIsNotNone(stored)
        self.assertNotEqual(stored["token_hash"], token)
        self.assertTrue(stored["token_hash"].startswith("pbkdf2$"))
        await self.client.post("/api/v1/auth/logout")

        reset = await self._forgot("bobuser", token, "bobusr9")
        self.assertEqual(reset.status, 200, await reset.text())
        set_cookie = reset.headers.getall("Set-Cookie", ())
        self.assertFalse(any(COOKIE_NAME in c for c in set_cookie))
        me = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status, 401)

        old = await self.login("bobuser", "bobusr1")
        self.assertEqual(old.status, 401)
        self.assertEqual((await old.json())["msg"], LOGIN_ERROR)
        stale = await self.client.get(
            "/api/v1/auth/me",
            headers={"Cookie": f"{COOKIE_NAME}={other}"},
        )
        self.assertEqual(stale.status, 401)
        ok = await self.login("bobuser", "bobusr9")
        self.assertEqual(ok.status, 200)

        async with self.app["platform_db"].execute(
            "SELECT token_hash FROM password_reset_tokens WHERE user_id = ?",
            (uid,),
        ) as cur:
            self.assertIsNone(await cur.fetchone())

    async def test_a2_wrong_expired_reuse_unknown_same_copy(self):
        await self.login("admin", "secret12")
        uid = await self._create_user("cara", "cara123")
        issued = await self._issue(uid)
        token = (await issued.json())["data"]["token"]
        replaced = await self._issue(uid)
        token2 = (await replaced.json())["data"]["token"]
        self.assertNotEqual(token, token2)
        await self.client.post("/api/v1/auth/logout")

        wrong = await self._forgot("cara", "not-the-token", "cara999")
        self.assertEqual(wrong.status, 400)
        self.assertEqual((await wrong.json())["msg"], FORGOT_ERROR)

        stale = await self._forgot("cara", token, "cara999")
        self.assertEqual(stale.status, 400)
        self.assertEqual((await stale.json())["msg"], FORGOT_ERROR)

        await self.app["platform_db"].execute(
            "UPDATE password_reset_tokens SET expires_at = ? WHERE user_id = ?",
            (time.time() - 10, uid),
        )
        await self.app["platform_db"].commit()
        expired = await self._forgot("cara", token2, "cara999")
        self.assertEqual(expired.status, 400)
        self.assertEqual((await expired.json())["msg"], FORGOT_ERROR)

        await self.login("admin", "secret12")
        fresh = await self._issue(uid)
        live = (await fresh.json())["data"]["token"]
        await self.client.post("/api/v1/auth/logout")
        first = await self._forgot("cara", live, "cara888")
        self.assertEqual(first.status, 200)
        reuse = await self._forgot("cara", live, "cara777")
        self.assertEqual(reuse.status, 400)
        self.assertEqual((await reuse.json())["msg"], FORGOT_ERROR)

        unknown = await self._forgot("no-such-user", live, "cara777")
        self.assertEqual(unknown.status, 400)
        self.assertEqual((await unknown.json())["msg"], FORGOT_ERROR)

        admin_name = await self._forgot("admin", live, "secret99")
        self.assertEqual(admin_name.status, 400)
        self.assertEqual((await admin_name.json())["msg"], FORGOT_ERROR)

        short = await self._forgot("no-such-user", "x", "ab")
        self.assertEqual(short.status, 400)
        self.assertEqual((await short.json())["msg"], "密码至少 6 个字符")

        still = await self.login("cara", "cara888")
        self.assertEqual(still.status, 200)

    async def test_a3_issue_authz_disabled_and_ui(self):
        await self.login("admin", "secret12")
        me = await self.client.get("/api/v1/auth/me")
        admin_id = (await me.json())["data"]["id"]
        self_issue = await self._issue(admin_id)
        self.assertEqual(self_issue.status, 400)
        missing = await self.client.post("/api/v1/admin/users/99999/reset-token")
        self.assertEqual(missing.status, 404)

        disabled_id = await self._create_user("dana", "dana123")
        await self.client.post(f"/api/v1/admin/users/{disabled_id}/disable")
        issued = await self._issue(disabled_id)
        self.assertEqual(issued.status, 200, await issued.text())
        token = (await issued.json())["data"]["token"]
        await self.client.post("/api/v1/auth/logout")

        reset = await self._forgot("dana", token, "dana999")
        self.assertEqual(reset.status, 200)
        blocked = await self.login("dana", "dana999")
        self.assertEqual(blocked.status, 401)
        self.assertEqual((await blocked.json())["msg"], LOGIN_ERROR)

        await self.login("admin", "secret12")
        enabled = await self.client.post(f"/api/v1/admin/users/{disabled_id}/enable")
        self.assertEqual(enabled.status, 200)
        uid2 = await self._create_user("erin", "erin123")
        token_row = await self._issue(uid2)
        old_token = (await token_row.json())["data"]["token"]
        reset_direct = await self.client.post(
            f"/api/v1/admin/users/{uid2}/password",
            json={"password": "erin999"},
        )
        self.assertEqual(reset_direct.status, 200)
        await self.client.post("/api/v1/auth/logout")
        invalidated = await self._forgot("erin", old_token, "erin888")
        self.assertEqual(invalidated.status, 400)
        self.assertEqual((await invalidated.json())["msg"], FORGOT_ERROR)

        unauth = await self.client.post("/api/v1/admin/users/1/reset-token")
        self.assertEqual(unauth.status, 401)
        await self.login("erin", "erin999")
        forbidden = await self.client.post(
            f"/api/v1/admin/users/{disabled_id}/reset-token",
        )
        self.assertEqual(forbidden.status, 403)
        await self.client.post("/api/v1/auth/logout")
        ok = await self.login("dana", "dana999")
        self.assertEqual(ok.status, 200)

        login_src = LOGIN.read_text(encoding="utf-8")
        self.assertIn("忘记密码", login_src)
        self.assertIn("/api/v1/auth/forgot-password", login_src)
        self.assertIn("一次性令牌", login_src)
        self.assertIn("请使用新密码登录", login_src)
        ops = OPS.read_text(encoding="utf-8")
        self.assertIn("发令牌", ops)
        self.assertIn("issueResetToken", ops)
        self.assertIn("/reset-token", ops)
        self.assertIn("window.confirm", ops)
        self.assertIn("window.prompt", ops)
        self.assertIn("v-if=\"u.role === 'user'\"", ops)
        self.assertNotIn("u.role === 'admin'", ops)
        text = README.read_text(encoding="utf-8")
        self.assertIn("用户（禁用/启用/删除/改密/重置令牌）", text)
        en = README_EN.read_text(encoding="utf-8")
        self.assertIn("disable/enable/delete/reset password/reset token", en)

    async def test_a4_web_untouched_self_change_and_admin_reset_remain(self):
        diff = subprocess.run(
            ["git", "diff", "--exit-code", "--", "web/"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(diff.returncode, 0, diff.stdout + diff.stderr)
        self.assertTrue((WEB / "index.html").is_file())
        form = PASSWORD_FORM.read_text(encoding="utf-8")
        self.assertIn("改密", form)
        self.assertIn("current_password", form)
        self.assertIn("new_password", form)
        ops = OPS.read_text(encoding="utf-8")
        self.assertIn("resetPassword", ops)
        self.assertIn("/password", ops)


if __name__ == "__main__":
    unittest.main()
