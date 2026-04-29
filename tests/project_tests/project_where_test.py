import pathlib
import subprocess
import sys
import tempfile
import unittest

from tests.project_tests import subprocess_helpers


class ProjectWhereCommandTest(unittest.TestCase):
    def test_project_where_help_mentions_read_only_behavior(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "where", "--help"]
        result = subprocess.run(
            cmd,
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
        self.assertIn("read-only", result.stdout, msg=failure_message)

    def test_project_where_succeeds_without_project_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "where"]
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
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
            "project_metadata_found: False", result.stdout, msg=failure_message
        )
        self.assertIn(
            "project_root_candidate: unresolved", result.stdout, msg=failure_message
        )

    def test_project_where_detects_project_root_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_root = root_path / "example-project"
            nested_dir = project_root / "repo" / "nested"
            metadata_dir = project_root / ".taurworks"
            nested_dir.mkdir(parents=True)
            metadata_dir.mkdir(parents=True)

            cmd = [sys.executable, "-m", "taurworks.cli", "project", "where"]
            result = subprocess.run(
                cmd,
                cwd=nested_dir,
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
            "project_metadata_found: True", result.stdout, msg=failure_message
        )
        self.assertIn(
            f"project_root_candidate: {project_root}",
            result.stdout,
            msg=failure_message,
        )

    def test_project_where_ignores_relative_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = subprocess_helpers.subprocess_env()
            env["XDG_CONFIG_HOME"] = ".config"
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "where"]
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        fallback = pathlib.Path.home() / ".config" / "taurworks" / "config.toml"
        self.assertIn(
            f"config_path_candidate: {fallback}", result.stdout, msg=failure_message
        )

    def test_project_where_uses_xdg_config_home_when_set(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = subprocess_helpers.subprocess_env()
            env["XDG_CONFIG_HOME"] = temp_dir
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "where"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        expected = pathlib.Path(temp_dir) / "taurworks" / "config.toml"
        self.assertIn(
            f"config_path_candidate: {expected}", result.stdout, msg=failure_message
        )


if __name__ == "__main__":
    unittest.main()
