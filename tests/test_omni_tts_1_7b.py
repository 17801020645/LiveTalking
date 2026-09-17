import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
START_OMNI = REPO / "start-omni.sh"
YAML_06 = REPO / "deploy" / "qwen3_tts_0.6b.yaml"
YAML_17 = REPO / "deploy" / "qwen3_tts_1.7b.yaml"
DOCS_OMNI = REPO / "docs" / "omni_tts.md"
README = REPO / "README.md"


def _stage_utils(text: str) -> list[str]:
    return re.findall(r"(?m)^    gpu_memory_utilization: ([0-9.]+)$", text)


class OmniTts17bTests(unittest.TestCase):
    def test_a1_default_still_0_6b_customvoice_and_yaml(self):
        src = START_OMNI.read_text(encoding="utf-8")
        self.assertIn('MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}"', src)
        self.assertNotIn('MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice}"', src)
        self.assertIn('DEPLOY_CONFIG="$ROOT/deploy/qwen3_tts_0.6b.yaml"', src)
        self.assertEqual(_stage_utils(YAML_06.read_text(encoding="utf-8")), ["0.15", "0.15"])

    def test_a2_1_7b_model_selects_dedicated_yaml(self):
        src = START_OMNI.read_text(encoding="utf-8")
        self.assertIn('elif [[ "$MODEL" == *1.7B* ]]; then', src)
        self.assertIn('DEPLOY_CONFIG="$ROOT/deploy/qwen3_tts_1.7b.yaml"', src)
        self.assertIn('if [[ -n "${OMNI_DEPLOY_CONFIG:-}" ]]; then', src)
        self.assertTrue(YAML_17.is_file())
        self.assertEqual(_stage_utils(YAML_17.read_text(encoding="utf-8")), ["0.25", "0.25"])

    def test_a3_docs_and_readme_cover_start_and_download(self):
        docs = DOCS_OMNI.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        cmd = "OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
        for text in (docs, readme):
            self.assertIn(cmd, text)
            self.assertIn("HF_HUB_OFFLINE=0", text)
            self.assertIn("同卡更容易 OOM", text)
            self.assertNotIn("本规格不部署 1.7B", text)
        self.assertIn("qwen3_tts_1.7b.yaml", docs)

    def test_a4_web_untouched(self):
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
