import os
import pathlib
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ALIASES_SOURCE = REPO_ROOT / "sourceme" / "aliases.source"


def _run(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env=env,
    )


class AliasesSourceTest(unittest.TestCase):
    def test_defines_tl_function(self):
        cmd = ["bash", "-c", 'source "$1" && type tl', "bash", str(ALIASES_SOURCE)]
        result = _run(cmd, dict(os.environ))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("tl is a function", result.stdout)

    def test_tl_name_sources_admin_legacy_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir) / "Workspace"
            project_dir = workspace / "Project"
            admin_dir = project_dir / "Admin"
            admin_dir.mkdir(parents=True)
            sentinel = pathlib.Path(temp_dir) / "sourced.txt"
            (admin_dir / "project-setup.source").write_text(
                f'touch "{sentinel}"\n', encoding="utf-8"
            )

            env = dict(os.environ)
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tl Project',
                "bash",
                str(ALIASES_SOURCE),
            ]
            result = _run(cmd, env)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("tl: sourcing", result.stdout)
            self.assertTrue(sentinel.exists())

    def test_tl_name_falls_back_to_taurworks_legacy_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir) / "Workspace"
            project_dir = workspace / "Project"
            config_dir = project_dir / ".taurworks"
            config_dir.mkdir(parents=True)
            sentinel = pathlib.Path(temp_dir) / "sourced.txt"
            (config_dir / "project-setup.source").write_text(
                f'touch "{sentinel}"\n', encoding="utf-8"
            )

            env = dict(os.environ)
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tl Project',
                "bash",
                str(ALIASES_SOURCE),
            ]
            result = _run(cmd, env)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(sentinel.exists())

    def test_tl_reports_missing_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir) / "Workspace"
            workspace.mkdir()

            env = dict(os.environ)
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tl NoSuchProject',
                "bash",
                str(ALIASES_SOURCE),
            ]
            result = _run(cmd, env)

        self.assertEqual(result.returncode, 1)
        self.assertIn("no setup script found for project", result.stderr)

    def test_tl_with_no_argument_prints_usage_and_fails(self):
        cmd = ["bash", "-c", 'source "$1" && tl', "bash", str(ALIASES_SOURCE)]
        result = _run(cmd, dict(os.environ))
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: tl PROJECT_NAME", result.stderr)

    def test_tl_rejects_old_two_argument_activate_syntax(self):
        # `tl activate NAME` was the pre-WI-TL-BREAKGLASS-0001 syntax; the
        # simplified `tl NAME` form deliberately rejects a second argument
        # rather than silently reinterpreting it.
        cmd = [
            "bash",
            "-c",
            'source "$1" && tl activate SomeProject',
            "bash",
            str(ALIASES_SOURCE),
        ]
        result = _run(cmd, dict(os.environ))
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: tl PROJECT_NAME", result.stderr)


if __name__ == "__main__":
    unittest.main()
