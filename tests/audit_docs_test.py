import os
import pathlib
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT_DOC = REPO_ROOT / "project" / "audits" / "side_effects.md"
AUDIT_INDEX = REPO_ROOT / "project" / "audits" / "README.md"
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit-side-effects"
README = REPO_ROOT / "README.md"


class SideEffectAuditDocsTest(unittest.TestCase):

    def test_side_effect_audit_is_discoverable(self):
        audit_text = AUDIT_DOC.read_text(encoding="utf-8")
        index_text = AUDIT_INDEX.read_text(encoding="utf-8")
        readme_text = README.read_text(encoding="utf-8")

        self.assertIn("Side-effect taxonomy", audit_text)
        self.assertIn("Conda creation", audit_text)
        self.assertIn("Conda activation", audit_text)
        self.assertIn("Environment variables", audit_text)
        self.assertIn("Scripts and shell commands", audit_text)
        self.assertIn("side_effects.md", index_text)
        self.assertIn("project/audits/side_effects.md", readme_text)

    def test_audit_side_effects_script_runs(self):
        result = subprocess.run(
            [str(AUDIT_SCRIPT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        failure_message = (
            f"Command failed: {AUDIT_SCRIPT}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertEqual(result.stderr, "", msg=failure_message)
        self.assertIn("Taurworks side-effect pattern audit", result.stdout)
        self.assertIn("subprocess", result.stdout)
        self.assertIn("conda", result.stdout)
        self.assertIn("src/taurworks/manager.py", result.stdout)

    def test_audit_side_effects_script_fails_when_rg_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bin_dir = pathlib.Path(temp_dir) / "bin"
            bin_dir.mkdir()
            (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
            env = dict(os.environ)
            env["PATH"] = str(bin_dir)

            result = subprocess.run(
                [str(AUDIT_SCRIPT)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        self.assertEqual(result.returncode, 127)
        self.assertIn("required command not found: rg", result.stderr)


if __name__ == "__main__":
    unittest.main()
