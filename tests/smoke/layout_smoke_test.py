import importlib
import pathlib
import subprocess
import sys
import unittest


class SrcLayoutSmokeTest(unittest.TestCase):
    def test_import_taurworks(self):
        module = importlib.import_module("taurworks")
        self.assertIsNotNone(module)
        self.assertIsNotNone(module.__file__)

        module_path = pathlib.Path(module.__file__).resolve()
        expected_package_dir = (
            pathlib.Path(__file__).resolve().parents[1] / "src" / "taurworks"
        ).resolve()

        self.assertTrue(
            expected_package_dir == module_path.parent
            or expected_package_dir in module_path.parents,
            f"Expected taurworks to be imported from {expected_package_dir}, got {module_path}",
        )

    def test_module_cli_help(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "--help"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                "CLI help command timed out after "
                f"{exc.timeout} seconds: {cmd}\n"
                f"stdout:\n{exc.stdout or ''}\n"
                f"stderr:\n{exc.stderr or ''}"
            )

        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("Manage taurworks projects.", result.stdout, msg=failure_message)

    def test_module_cli_project_help(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "--help"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                "CLI help command timed out after "
                f"{exc.timeout} seconds: {cmd}\n"
                f"stdout:\n{exc.stdout or ''}\n"
                f"stderr:\n{exc.stderr or ''}"
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

    def test_module_cli_project_where(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "where"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                "CLI project where command timed out after "
                f"{exc.timeout} seconds: {cmd}\n"
                f"stdout:\n{exc.stdout or ''}\n"
                f"stderr:\n{exc.stderr or ''}"
            )
        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn(
            "Taurworks project resolution diagnostics",
            result.stdout,
            msg=failure_message,
        )
        self.assertIn("project_root_candidate:", result.stdout, msg=failure_message)
        self.assertIn("config_path_candidate:", result.stdout, msg=failure_message)
        self.assertEqual(result.stderr.strip(), "", msg=failure_message)


if __name__ == "__main__":
    unittest.main()
