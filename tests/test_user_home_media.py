import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
USER_HOME = REPO / "frontend" / "src" / "views" / "user" / "Home.vue"
README = REPO / "README.md"
README_EN = REPO / "README-EN.md"
WEB = REPO / "web"


class UserHomeMediaTests(unittest.TestCase):
    def test_a1_upload_audio_when_connected(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("uploadAudio", src)
        self.assertIn("fetch('/humanaudio'", src)
        self.assertIn("form.append('sessionid'", src)
        self.assertIn(":disabled=\"!connected || uploading\"", src)
        self.assertIn("accept=\"audio/*\"", src)
        self.assertIn("user-live-panel", src)
        self.assertEqual(src.count("monitor-panel"), 1)

    def test_a2_record_when_connected(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("开始录制", src)
        self.assertIn("停止录制", src)
        self.assertIn("downloadRecord", src)
        self.assertIn("toggleRecord", src)
        self.assertIn("'/record'", src)
        self.assertIn("start_record", src)
        self.assertIn("end_record", src)
        self.assertIn("sessionid: sessionid.value", src)
        self.assertIn(":disabled=\"!connected\"", src)
        self.assertIn("'/record/' + sessionid.value", src)

    def test_a3_audiotype_when_connected(self):
        src = USER_HOME.read_text(encoding="utf-8")
        self.assertIn("setAudiotype", src)
        self.assertIn("'/set_audiotype'", src)
        self.assertIn("audiotype: Number(audiotype.value)", src)
        self.assertIn("sessionid: sessionid.value", src)
        self.assertIn("v-model.number=\"audiotype\"", src)
        self.assertIn(":disabled=\"!connected\"", src)

    def test_a4_readme_en_and_web(self):
        en = README_EN.read_text(encoding="utf-8")
        self.assertIn("/app/", en)
        self.assertIn("./start.sh", en)
        self.assertIn("./start-omni.sh", en)
        self.assertIn("OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base", en)
        self.assertIn("audio upload", en)
        self.assertNotIn(
            'Open `http://serverip:8010/index.html`, click "Start Connection" to play the digital human video',
            en,
        )
        zh = README.read_text(encoding="utf-8")
        self.assertIn("音频上传、录制与动作", zh)
        self.assertTrue((WEB / "index.html").is_file())
        result = subprocess.run(
            ["git", "diff", "--exit-code", "--", "web/"],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
