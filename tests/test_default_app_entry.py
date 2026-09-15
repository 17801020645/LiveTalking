import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from aiohttp.test_utils import TestClient, TestServer

from server.platform_routes import create_test_application

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web"
LIVE = REPO / "frontend" / "src" / "views" / "admin" / "Live.vue"


class DefaultAppEntryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        avatars = root / "avatars"
        avatars.mkdir()
        os.environ["LIVETALKING_BOOTSTRAP_ADMIN"] = "admin"
        os.environ["LIVETALKING_BOOTSTRAP_PASSWORD"] = "secret12"
        self.app = create_test_application(str(root / "p.db"), str(avatars), web_dir=str(WEB))
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.tmp.cleanup()

    def _location(self, response):
        return response.headers.get("Location", "")

    async def test_a1_webrtc_root_redirects_to_app(self):
        root = await self.client.get("/", allow_redirects=False)
        self.assertIn(root.status, (301, 302))
        loc = self._location(root)
        self.assertTrue(loc.endswith("/app/") or loc.endswith("/app"), loc)

    async def test_a2_index_html_is_legacy_console(self):
        page = await self.client.get("/index.html")
        self.assertEqual(page.status, 200)
        body = await page.text()
        self.assertIn("LiveTalking - 数字人实时驱动", body)
        self.assertNotIn('id="app"', body)

    async def test_a3_live_asr_link_points_to_index_html(self):
        src = LIVE.read_text(encoding="utf-8")
        self.assertNotIn('href="/"', src)
        self.assertNotIn("打开 /index.html", src)
        self.assertIn("开始说话", src)

    async def _root_for_transport(self, transport):
        tmp = tempfile.TemporaryDirectory()
        try:
            root = Path(tmp.name)
            avatars = root / "avatars"
            avatars.mkdir()
            app = create_test_application(str(root / "p.db"), str(avatars), web_dir=str(WEB))
            app["opt"] = SimpleNamespace(transport=transport)
            client = TestClient(TestServer(app))
            await client.start_server()
            try:
                resp = await client.get("/", allow_redirects=False)
                return resp.status, self._location(resp)
            finally:
                await client.close()
        finally:
            tmp.cleanup()

    async def test_a4_rtmp_rtcpush_root_and_web_untouched(self):
        self.assertTrue((WEB / "index.html").is_file())
        self.assertTrue((WEB / "rtmpapi.html").is_file())
        self.assertTrue((WEB / "rtcpushapi.html").is_file())

        rtmp_status, rtmp_loc = await self._root_for_transport("rtmp")
        self.assertIn(rtmp_status, (301, 302))
        self.assertIn("rtmpapi.html", rtmp_loc)

        rtc_status, rtc_loc = await self._root_for_transport("rtcpush")
        self.assertIn(rtc_status, (301, 302))
        self.assertIn("rtcpushapi.html", rtc_loc)


if __name__ == "__main__":
    unittest.main()
