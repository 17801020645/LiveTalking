import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
START_SH = REPO / "start.sh"
START_OMNI = REPO / "start-omni.sh"
README = REPO / "README.md"
README_EN = REPO / "README-EN.md"
DOCS_OMNI = REPO / "docs" / "omni_tts.md"
WEB = REPO / "web"


class OmniInStartShTests(unittest.TestCase):
    def _run(self, env, tmp: Path, start_omni: Path | None = None, python: Path | None = None):
        env = dict(os.environ, **env)
        env["START_SH_PYTHON"] = str(python or (tmp / "fake-python"))
        if start_omni is not None:
            env["START_OMNI"] = str(start_omni)
        env["OMNI_START_LOG"] = str(tmp / "omni.log")
        env["OMNI_WAIT_SECS"] = env.get("OMNI_WAIT_SECS", "2")
        env["OMNI_VOICES_URL"] = env.get("OMNI_VOICES_URL", "http://127.0.0.1:8091/v1/audio/voices")
        return subprocess.run(
            ["bash", str(START_SH), "--avatar_id", "test_avatar"],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def _write_exec(self, path: Path, body: str):
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def test_a1_calls_start_omni_unless_ready_or_skipped(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            called = tmp / "omni-called"
            app_called = tmp / "app-called"
            self._write_exec(
                tmp / "fake-python",
                "#!/usr/bin/env bash\necho app > \"%s\"\n" % app_called,
            )
            self._write_exec(
                tmp / "start-omni.sh",
                "#!/usr/bin/env bash\necho omni > \"%s\"\nexit 1\n" % called,
            )
            result = self._run({}, tmp, start_omni=tmp / "start-omni.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(called.is_file(), result.stderr)
            self.assertTrue(app_called.is_file(), result.stderr)
            self.assertIn("start-omni.sh", START_SH.read_text(encoding="utf-8"))
            self.assertIn("SKIP_OMNI", START_SH.read_text(encoding="utf-8"))

            called.unlink()
            app_called.unlink()
            result = self._run({"SKIP_OMNI": "1"}, tmp, start_omni=tmp / "start-omni.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(called.is_file())
            self.assertTrue(app_called.is_file())
            self.assertIn("跳过拉起 Omni", result.stderr)

            called.unlink(missing_ok=True)
            app_called.unlink()
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            self._write_exec(
                bin_dir / "curl",
                "#!/usr/bin/env bash\nexit 0\n",
            )
            env = {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")}
            result = self._run(env, tmp, start_omni=tmp / "start-omni.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(called.is_file())
            self.assertTrue(app_called.is_file())
            self.assertIn("跳过拉起", result.stderr)

    def test_a2_omni_failure_still_starts_app_no_edgetts(self):
        src = START_SH.read_text(encoding="utf-8")
        self.assertNotIn("edgetts", src)
        self.assertNotIn("--tts", src)
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            app_called = tmp / "app-called"
            self._write_exec(
                tmp / "fake-python",
                "#!/usr/bin/env bash\necho \"$@\" > \"%s\"\n" % app_called,
            )
            result = self._run({}, tmp, start_omni=tmp / "missing-omni.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(app_called.is_file())
            args = app_called.read_text(encoding="utf-8")
            self.assertIn("app.py", args)
            self.assertNotIn("edgetts", args)
            self.assertIn("仍启动 8010", result.stderr)

    def test_a3_docs_say_start_sh_starts_omni(self):
        for path in (README, README_EN, DOCS_OMNI):
            text = path.read_text(encoding="utf-8")
            self.assertIn("./start.sh", text)
            self.assertIn("./start-omni.sh", text)
            self.assertIn("SKIP_OMNI", text)
        zh = README.read_text(encoding="utf-8")
        self.assertIn("先起 Omni TTS（8091），再起数字人（8010）", zh)
        en = README_EN.read_text(encoding="utf-8")
        self.assertIn("starts Omni TTS (8091) first, then the digital human (8010)", en)
        docs = DOCS_OMNI.read_text(encoding="utf-8")
        self.assertIn("会先拉起 Omni 再起数字人", docs)
        self.assertIn("换模型或单独起 8091 仍用 `./start-omni.sh`", docs)

    def test_a4_web_untouched_omni_script_unchanged_default(self):
        src = START_OMNI.read_text(encoding="utf-8")
        self.assertIn('MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}"', src)
        self.assertIn('exec "$VLLM" serve', src)
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
