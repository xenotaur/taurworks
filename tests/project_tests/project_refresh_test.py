import pathlib
import subprocess
import sys
import tempfile
import unittest

from tests.project_tests import subprocess_helpers


class ProjectRefreshCommandTest(unittest.TestCase):
    def test_project_refresh_creates_minimal_scaffolding(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "sample-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "refresh",
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
            self.assertIn("created:", result.stdout, msg=failure_message)

    def test_project_refresh_does_not_overwrite_existing_config(self):
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
                "refresh",
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

        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertEqual(refreshed_content, original_content, msg=failure_message)
        self.assertIn("changed: False", result.stdout, msg=failure_message)
        self.assertIn("no changes needed", result.stdout, msg=failure_message)

    def test_project_refresh_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "idempotent-project"

            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "refresh",
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

        first_message = (
            f"First command failed: {cmd}\n"
            f"return code: {first.returncode}\n"
            f"stdout:\n{first.stdout}\n"
            f"stderr:\n{first.stderr}"
        )
        second_message = (
            f"Second command failed: {cmd}\n"
            f"return code: {second.returncode}\n"
            f"stdout:\n{second.stdout}\n"
            f"stderr:\n{second.stderr}"
        )
        self.assertEqual(first.returncode, 0, msg=first_message)
        self.assertEqual(second.returncode, 0, msg=second_message)
        self.assertIn("changed: True", first.stdout, msg=first_message)
        self.assertIn("changed: False", second.stdout, msg=second_message)
        self.assertIn("no changes needed", second.stdout, msg=second_message)

    def test_project_refresh_reports_warning_for_file_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            file_target = root_path / "not-a-directory.txt"
            file_target.write_text("content", encoding="utf-8")

            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "refresh",
                str(file_target),
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
        self.assertIn("changed: False", result.stdout, msg=failure_message)
        self.assertIn("warnings:", result.stdout, msg=failure_message)
        self.assertIn("target path exists but is not a directory", result.stdout)
        self.assertIn("warnings present; review skipped items", result.stdout)
        self.assertFalse((file_target / ".taurworks").exists(), msg=failure_message)

    def test_project_refresh_warns_when_metadata_path_is_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-with-bad-metadata"
            target_dir.mkdir()
            metadata_path = target_dir / ".taurworks"
            metadata_path.write_text("file-instead-of-directory", encoding="utf-8")

            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "refresh",
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
        self.assertIn("metadata path exists but is not a directory", result.stdout)
        self.assertIn("warnings present; review skipped items", result.stdout)
        self.assertNotIn("result: no changes needed", result.stdout)

    def test_project_refresh_warns_when_config_path_is_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-with-bad-config"
            metadata_dir = target_dir / ".taurworks"
            config_dir = metadata_dir / "config.toml"
            config_dir.mkdir(parents=True)

            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "refresh",
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
        self.assertIn(
            "config path exists but is not a regular file",
            result.stdout,
            msg=failure_message,
        )
        self.assertIn("warnings present; review skipped items", result.stdout)


if __name__ == "__main__":
    unittest.main()
