import pathlib
import subprocess
import sys
import tempfile
import unittest


def _subprocess_env() -> dict[str, str]:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    env = dict(__import__("os").environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{__import__('os').pathsep}{existing}" if existing else str(src_path)
    )
    return env


class CliCommandTest(unittest.TestCase):
    def test_project_namespace_help_lists_read_only_commands(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "--help"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env=_subprocess_env(),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("where", result.stdout)
        self.assertIn("list", result.stdout)
        self.assertIn("read-only", result.stdout)

    def test_project_where_help_mentions_read_only_behavior(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "where", "--help"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env=_subprocess_env(),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("read-only", result.stdout)

    def test_project_list_succeeds_without_discovered_projects(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xdg_home = pathlib.Path(temp_dir) / "xdg-config"
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "list"]
            env = _subprocess_env()
            env["XDG_CONFIG_HOME"] = str(xdg_home)
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("project_count: 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
