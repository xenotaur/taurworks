import pathlib
import subprocess
import sys
import tempfile
import unittest

from tests.project_tests import subprocess_helpers


class ProjectCreateCommandTest(unittest.TestCase):
    def test_project_create_creates_directory_and_scaffolding(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "created-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=subprocess_helpers.subprocess_env(),
            )

            failure_message = (
                f"Command failed: {cmd}\n"
                f"return code: {result.returncode}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue((target_dir / ".taurworks").is_dir(), msg=failure_message)
            self.assertTrue(
                (target_dir / ".taurworks" / "config.toml").is_file(),
                msg=failure_message,
            )
            self.assertIn("delegated_command: project refresh", result.stdout)

    def test_project_create_does_not_overwrite_existing_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "existing-project"
            metadata_dir = target_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            config_path = metadata_dir / "config.toml"
            original_content = '[project]\nname = "kept"\n'
            config_path.write_text(original_content, encoding="utf-8")

            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=subprocess_helpers.subprocess_env(),
            )

            refreshed_content = config_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(refreshed_content, original_content)
        self.assertIn("changed: False", result.stdout)
        self.assertIn("config file retained without changes", result.stdout)

    def test_project_create_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "idempotent-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
            ]
            first = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=subprocess_helpers.subprocess_env(),
            )
            second = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=subprocess_helpers.subprocess_env(),
            )

        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertIn("changed: True", first.stdout)
        self.assertIn("changed: False", second.stdout)
        self.assertIn("no changes needed", second.stdout)


if __name__ == "__main__":
    unittest.main()
