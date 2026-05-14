import importlib.resources
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SHELL_HELPER = (
    REPO_ROOT / "src" / "taurworks" / "resources" / "shell" / "taurworks-shell.sh"
)


def _subprocess_env() -> dict[str, str]:
    src_path = REPO_ROOT / "src"
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )
    return env


def _write_taurworks_module_shim(bin_dir: pathlib.Path) -> None:
    taurworks = bin_dir / "taurworks"
    taurworks.write_text(
        '#!/bin/sh\nexec python -m taurworks.cli "$@"\n',
        encoding="utf-8",
    )
    taurworks.chmod(taurworks.stat().st_mode | stat.S_IXUSR)


class ShellHelperTest(unittest.TestCase):
    def test_packaged_shell_helper_resource_is_readable(self):
        resource = importlib.resources.files("taurworks").joinpath(
            "resources/shell/taurworks-shell.sh"
        )
        helper_text = resource.read_text(encoding="utf-8")

        self.assertIn("tw()", helper_text)
        self.assertIn("_tw_activate()", helper_text)

    def test_shell_print_outputs_sourceable_helper(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "shell", "print"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env=_subprocess_env(),
        )
        failure_message = (
            f"Command failed: {cmd}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("tw()", result.stdout, msg=failure_message)
        self.assertIn("_tw_activate()", result.stdout, msg=failure_message)

    def test_shell_helper_defines_tw_function(self):
        cmd = ["bash", "-c", 'source "$1" && type tw', "bash", str(SHELL_HELPER)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env=_subprocess_env(),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("tw is a function", result.stdout)

    def test_tw_delegates_non_activation_commands_to_taurworks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            log_path = temp_path / "delegated.txt"
            taurworks = bin_dir / "taurworks"
            taurworks.write_text(
                (
                    "#!/bin/sh\n"
                    'printf \'%s\\n\' "$*" > "$TAURWORKS_DELEGATION_LOG"\n'
                    "printf 'delegated:%s\\n' \"$*\"\n"
                ),
                encoding="utf-8",
            )
            taurworks.chmod(taurworks.stat().st_mode | stat.S_IXUSR)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_DELEGATION_LOG"] = str(log_path)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tw project list',
                "bash",
                str(SHELL_HELPER),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )
            delegated_args = log_path.read_text(encoding="utf-8").strip()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("delegated:project list", result.stdout)
        self.assertEqual(delegated_args, "project list")

    def test_tw_activate_changes_directory_to_configured_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create TestProject "
                    "--working-dir test_repo --create-working-dir >/dev/null && "
                    "tw activate TestProject >/dev/null && "
                    "pwd"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        expected_dir = workspace / "TestProject" / "test_repo"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), str(expected_dir))

    def test_tw_activate_failure_does_not_change_directory_or_startup_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            home_dir = temp_path / "home"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            home_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)
            bashrc = home_dir / ".bashrc"
            profile = home_dir / ".profile"
            bashrc.write_text("original bashrc\n", encoding="utf-8")
            profile.write_text("original profile\n", encoding="utf-8")

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["HOME"] = str(home_dir)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create TestProject >/dev/null && "
                    "before=$(pwd) && "
                    "if tw activate TestProject >/tmp/tw-activate.out 2>/tmp/tw-activate.err; "
                    "then exit 20; fi && "
                    'test "$(pwd)" = "$before" && '
                    "pwd && cat /tmp/tw-activate.err"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )
            bashrc_text = bashrc.read_text(encoding="utf-8")
            profile_text = profile.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(result.stdout.startswith(str(workspace)))
        self.assertIn("no configured working directory", result.stdout)
        self.assertIn("working_dir_configured: False", result.stdout)
        self.assertEqual(bashrc_text, "original bashrc\n")
        self.assertEqual(profile_text, "original profile\n")

    def test_tw_activate_cli_failure_reports_diagnostics_with_errexit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            project_dir = workspace / "TestProject"
            config_dir = project_dir / ".taurworks"
            config_dir.mkdir(parents=True)
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "TestProject"\n\n'
                    '[paths]\nworking_dir = "../outside"\n'
                ),
                encoding="utf-8",
            )

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            cmd = [
                "bash",
                "-c",
                (
                    "set -e; "
                    'source "$1"; '
                    'cd "$2"; '
                    "tw activate TestProject; "
                    "echo unreachable"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Configured working_dir is invalid", result.stderr)
        self.assertIn("working_dir is invalid", result.stderr)
        self.assertNotIn("unreachable", result.stdout)

    def test_tw_activate_missing_working_dir_fails_without_changing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create TestProject "
                    "--working-dir missing_repo >/dev/null && "
                    "before=$(pwd) && "
                    "if tw activate TestProject >/tmp/tw-activate.out 2>/tmp/tw-activate.err; "
                    "then exit 20; fi && "
                    'test "$(pwd)" = "$before" && '
                    "pwd && cat /tmp/tw-activate.err"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(result.stdout.startswith(str(workspace)))
        self.assertIn("resolved working directory does not exist", result.stdout)
        self.assertIn("working_dir_exists: False", result.stdout)


if __name__ == "__main__":
    unittest.main()
