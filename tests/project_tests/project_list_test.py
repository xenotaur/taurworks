import pathlib
import subprocess
import sys
import tempfile
import unittest

from tests.project_tests import subprocess_helpers


class ProjectListCommandTest(unittest.TestCase):
    def test_project_namespace_help_lists_read_only_commands(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "--help"]
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
        self.assertIn("where", result.stdout, msg=failure_message)
        self.assertIn("list", result.stdout, msg=failure_message)

    def test_project_list_succeeds_without_discovered_projects(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pre_entries = sorted(pathlib.Path(temp_dir).iterdir())
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "list"]
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=subprocess_helpers.subprocess_env(),
            )
            post_entries = sorted(pathlib.Path(temp_dir).iterdir())

        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("project_count: 0", result.stdout, msg=failure_message)
        self.assertIn("projects: none", result.stdout, msg=failure_message)
        self.assertEqual(pre_entries, post_entries, msg=failure_message)

    def test_project_list_discovers_project_from_current_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_root = root_path / "example-project"
            nested_dir = project_root / "repo" / "nested"
            metadata_dir = project_root / ".taurworks"
            nested_dir.mkdir(parents=True)
            metadata_dir.mkdir(parents=True)

            cmd = [sys.executable, "-m", "taurworks.cli", "project", "list"]
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
        self.assertIn("project_count: 1", result.stdout, msg=failure_message)
        self.assertIn(
            f"example-project: {project_root}",
            result.stdout,
            msg=failure_message,
        )

    def test_project_list_discovers_projects_in_current_directory_children(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            alpha_project = root_path / "alpha"
            beta_project = root_path / "beta"
            (alpha_project / ".taurworks").mkdir(parents=True)
            (beta_project / ".taurworks").mkdir(parents=True)
            (root_path / "ignored").mkdir()

            cmd = [sys.executable, "-m", "taurworks.cli", "project", "list"]
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
        self.assertIn("project_count: 2", result.stdout, msg=failure_message)
        self.assertIn(f"alpha: {alpha_project}", result.stdout, msg=failure_message)
        self.assertIn(f"beta: {beta_project}", result.stdout, msg=failure_message)


if __name__ == "__main__":
    unittest.main()
