import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from server.platform_orders import still_image_to_silent_video

REPO = Path(__file__).resolve().parents[1]
AVATAR = REPO / "frontend" / "src" / "views" / "admin" / "Avatar.vue"
ORDERS = REPO / "server" / "platform_orders.py"
WEB = REPO / "web"


class ImageAudioAvatarTests(unittest.TestCase):
    def test_a4_admin_page_allows_image_audio(self):
        src = AVATAR.read_text(encoding="utf-8")
        self.assertIn("视频与图+音频订单均可生成", src)
        self.assertNotIn("无法走现有抽帧管线", src)
        orders = ORDERS.read_text(encoding="utf-8")
        self.assertIn("still_image_to_silent_video", orders)
        self.assertIn('material == "image_audio"', orders)
        self.assertTrue((WEB / "index.html").is_file())

    def test_still_loop_writes_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "face.png"
            out_path = Path(tmp) / "still_loop.mp4"
            cv2.imwrite(str(img_path), np.zeros((32, 32, 3), dtype=np.uint8))
            written = still_image_to_silent_video(img_path, out_path, frames=8, fps=8)
            self.assertTrue(Path(written).is_file())
            self.assertGreater(Path(written).stat().st_size, 0)
            cap = cv2.VideoCapture(written)
            ok, frame = cap.read()
            cap.release()
            self.assertTrue(ok)
            self.assertIsNotNone(frame)


if __name__ == "__main__":
    unittest.main()
