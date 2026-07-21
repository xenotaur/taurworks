import importlib.resources
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

from helpers import assert_same_path

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SHELL_HELPER = (
    REPO_ROOT / "src" / "taurworks" / "resources" / "shell" / "taurworks-shell.sh"
)


def _subprocess_env() -> dict[str, str]:
    src_path = REPO_ROOT / "src"
    isolated_root = (
        pathlib.Path(tempfile.gettempdir()) / f"taurworks-shell-test-{os.getpid()}"
    )
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )
    env["HOME"] = str(isolated_root / "home")
    env["XDG_CONFIG_HOME"] = str(isolated_root / "xdg")
    env.pop("TAURWORKS_WORKSPACE", None)
    env.pop("TAURWORKS_SHELL_HELPER_PATH", None)
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

    def test_tw_dev_delegates_to_taurworks_dev(self):
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
                'source "$1" && tw dev where',
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
        self.assertIn("delegated:dev where", result.stdout)
        self.assertEqual(delegated_args, "dev where")

    def test_tw_projects_delegates_to_taurworks_projects(self):
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
                'source "$1" && tw projects',
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
        self.assertIn("delegated:projects", result.stdout)
        self.assertEqual(delegated_args, "projects")

    def test_tw_help_delegates_to_taurworks_help(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            cmd = [
                "bash",
                "-c",
                'source "$1" && tw --help > /tmp/tw-help-option.out && tw help',
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
            option_help = pathlib.Path("/tmp/tw-help-option.out").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, option_help)
        self.assertIn("usage: taurworks", result.stdout)

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
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create TestProject --local "
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
        assert_same_path(self, result.stdout.strip(), expected_dir)

    def test_tw_activate_without_working_dir_changes_to_root_with_warning(self):
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
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            env["HOME"] = str(home_dir)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create TestProject --local >/dev/null && "
                    "tw activate TestProject >/tmp/tw-activate.out 2>/tmp/tw-activate.err && "
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

        expected_root = workspace / "TestProject"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        first_stdout_line = result.stdout.splitlines()[0]
        assert_same_path(self, first_stdout_line, expected_root)
        self.assertIn("No working_dir is configured", result.stdout)
        self.assertNotIn("working_dir_configured: False", result.stdout)
        self.assertEqual(bashrc_text, "original bashrc\n")
        self.assertEqual(profile_text, "original profile\n")

    def test_tw_activate_invalid_config_default_failure_preserves_reason(self):
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
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "before=$(pwd) && "
                    "if tw activate TestProject >/tmp/tw-invalid.out 2>/tmp/tw-invalid.err; "
                    "then exit 20; fi && "
                    'test "$(pwd)" = "$before" && '
                    "pwd && cat /tmp/tw-invalid.err"
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
        assert_same_path(self, result.stdout.splitlines()[0], workspace)
        self.assertIn("activation failed for TestProject", result.stdout)
        self.assertIn("Configured working_dir is invalid", result.stdout)
        self.assertNotIn("no configured working directory", result.stdout)
        self.assertNotIn("working_dir_configured:", result.stdout)
        self.assertIn("taurworks project activate TestProject --print", result.stdout)

    def test_tw_activate_verbose_failure_reports_diagnostics_with_errexit(self):
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
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    "set -e; "
                    'source "$1"; '
                    'cd "$2"; '
                    "tw activate TestProject --verbose; "
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
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create TestProject --local "
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
        assert_same_path(self, result.stdout.splitlines()[0], workspace)
        self.assertIn("directory does not exist", result.stdout)
        self.assertNotIn("working_dir_exists: False", result.stdout)
        self.assertIn("taurworks project activate TestProject --print", result.stdout)

    def test_tw_activate_exports_variables_and_prints_message(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Alpha --local "
                    "--working-dir repo --create-working-dir >/dev/null && "
                    "cat >> Alpha/.taurworks/config.toml <<'EOF'\n"
                    "\n[activation]\n"
                    'message = "Ready for work on project Alpha"\n'
                    "\n[activation.exports]\n"
                    'NODE_OPTIONS = "--max-old-space-size=8192"\n'
                    'TAURWORKS_DOGFOOD_FLAG = "enabled"\n'
                    "QUOTED_VALUE = \"a value with 'quotes' and spaces\"\n"
                    "EOF\n"
                    "tw activate Alpha && "
                    "pwd && "
                    "printf '%s\n' \"$TAURWORKS_DOGFOOD_FLAG\" && "
                    "printf '%s\n' \"$NODE_OPTIONS\" && "
                    "printf '%s\n' \"$QUOTED_VALUE\""
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

        expected_dir = workspace / "Alpha" / "repo"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout_lines = result.stdout.splitlines()
        self.assertIn("tw activate: exported 3 variable(s)", stdout_lines)
        self.assertIn("Ready for work on project Alpha", stdout_lines)
        assert_same_path(self, stdout_lines[-4], expected_dir)
        self.assertEqual(
            stdout_lines[-3:],
            [
                "enabled",
                "--max-old-space-size=8192",
                "a value with 'quotes' and spaces",
            ],
        )
        self.assertNotIn("enabled", "\n".join(stdout_lines[:-3]))
        self.assertNotIn("--max-old-space-size=8192", "\n".join(stdout_lines[:-3]))

    def test_tw_activate_uses_configured_conda_environment_before_cd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            order_path = temp_path / "tw-conda-order.out"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            env["TAURWORKS_CONDA_ORDER_PATH"] = str(order_path)
            cmd = [
                "bash",
                "-c",
                (
                    "conda() {\n"
                    '  if [ "$1" = "activate" ] && [ "$2" = "FakeAlphaEnv" ]; then\n'
                    '    export TAURWORKS_FAKE_CONDA_ENV="$2"\n'
                    '    printf \'%s:%s\n\' "$2" "$(pwd)" > "$TAURWORKS_CONDA_ORDER_PATH"\n'
                    "    return 0\n"
                    "  fi\n"
                    "  return 1\n"
                    "}\n"
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Alpha --local "
                    "--working-dir repo --create-working-dir >/dev/null && "
                    "cat >> Alpha/.taurworks/config.toml <<'EOF'\n"
                    "\n[activation]\n"
                    'message = "Ready for work on project Alpha"\n'
                    "\n[activation.exports]\n"
                    'TAURWORKS_DOGFOOD_FLAG = "enabled"\n'
                    "\n[activation.environment]\n"
                    'type = "conda"\n'
                    'name = "FakeAlphaEnv"\n'
                    "EOF\n"
                    "tw activate Alpha && "
                    "pwd && "
                    "printf '%s\n' \"$TAURWORKS_FAKE_CONDA_ENV\" && "
                    "printf '%s\n' \"$TAURWORKS_DOGFOOD_FLAG\" && "
                    'cat "$TAURWORKS_CONDA_ORDER_PATH"'
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

        expected_dir = workspace / "Alpha" / "repo"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout_lines = result.stdout.splitlines()
        self.assertIn("tw activate: exported 1 variable(s)", stdout_lines)
        self.assertIn("Ready for work on project Alpha", stdout_lines)
        assert_same_path(self, stdout_lines[-4], expected_dir)
        self.assertEqual(stdout_lines[-3], "FakeAlphaEnv")
        self.assertEqual(stdout_lines[-2], "enabled")
        conda_name, conda_cwd = stdout_lines[-1].split(":", 1)
        self.assertEqual(conda_name, "FakeAlphaEnv")
        assert_same_path(self, conda_cwd, workspace)

    def test_fresh_user_project_create_env_flag_activates_conda_before_cd(self):
        """Fresh-user acceptance test (WI-ACTIVATION-PRODUCERS-0001): a project
        created with only shipped commands (`project create --env`) must reach
        Conda-switching `tw activate`, with no manual config.toml editing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            order_path = temp_path / "tw-conda-order.out"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            env["TAURWORKS_CONDA_ORDER_PATH"] = str(order_path)
            cmd = [
                "bash",
                "-c",
                (
                    "conda() {\n"
                    '  if [ "$1" = "activate" ] && [ "$2" = "FreshEnv" ]; then\n'
                    '    export TAURWORKS_FAKE_CONDA_ENV="$2"\n'
                    "    return 0\n"
                    "  fi\n"
                    "  return 1\n"
                    "}\n"
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Fresh --local --env FreshEnv "
                    "--working-dir fresh_repo --create-working-dir >/dev/null && "
                    "tw activate Fresh >/dev/null && "
                    "pwd && "
                    "printf '%s\n' \"$TAURWORKS_FAKE_CONDA_ENV\""
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

        expected_dir = workspace / "Fresh" / "fresh_repo"
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout_lines = result.stdout.splitlines()
        assert_same_path(self, stdout_lines[-2], expected_dir)
        self.assertEqual(stdout_lines[-1], "FreshEnv")

    def test_tw_activate_notes_missing_environment_configuration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create NoEnv --local "
                    "--working-dir repo --create-working-dir >/dev/null && "
                    "tw activate NoEnv >/tmp/tw-noenv.out 2>/tmp/tw-noenv.err && "
                    "cat /tmp/tw-noenv.err"
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
        self.assertIn("tw activate: note:", result.stdout)
        self.assertIn("taurworks project env set", result.stdout)

    def test_tw_activate_conda_failure_does_not_change_directory_or_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            stdout_path = temp_path / "tw-conda-fail.out"
            stderr_path = temp_path / "tw-conda-fail.err"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            env["GOOD_VALUE"] = "before"
            cmd = [
                "bash",
                "-c",
                (
                    "conda() { return 1; }\n"
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Alpha --local "
                    "--working-dir repo --create-working-dir >/dev/null && "
                    "cat >> Alpha/.taurworks/config.toml <<'EOF'\n"
                    "\n[activation.exports]\n"
                    'GOOD_VALUE = "after"\n'
                    "\n[activation.environment]\n"
                    'type = "conda"\n'
                    'name = "FakeAlphaEnv"\n'
                    "EOF\n"
                    "before=$(pwd) && "
                    'if tw activate Alpha >"$3" 2>"$4"; '
                    "then exit 20; fi && "
                    'test "$(pwd)" = "$before" && '
                    "pwd && "
                    "printf '%s\n' \"$GOOD_VALUE\" && "
                    'cat "$4"'
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
                str(stdout_path),
                str(stderr_path),
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
        stdout_lines = result.stdout.splitlines()
        assert_same_path(self, stdout_lines[0], workspace)
        self.assertEqual(stdout_lines[1], "before")
        self.assertIn(
            "failed to activate Conda environment: FakeAlphaEnv", result.stdout
        )
        self.assertNotIn("after", result.stdout)

    def test_tw_activate_without_environment_does_not_require_conda(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Alpha --local "
                    "--working-dir repo --create-working-dir >/dev/null && "
                    "tw activate Alpha >/dev/null && pwd"
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
        assert_same_path(self, result.stdout.strip(), workspace / "Alpha" / "repo")

    def test_tw_activate_missing_working_dir_does_not_export_variables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            env["GOOD_VALUE"] = "before"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Alpha --local "
                    "--working-dir missing_repo >/dev/null && "
                    "cat >> Alpha/.taurworks/config.toml <<'EOF'\n"
                    "\n[activation.exports]\n"
                    'GOOD_VALUE = "after"\n'
                    "EOF\n"
                    "before=$(pwd) && "
                    "if tw activate Alpha >/tmp/tw-missing-export.out 2>/tmp/tw-missing-export.err; "
                    "then exit 20; fi && "
                    'test "$(pwd)" = "$before" && '
                    "pwd && "
                    "printf '%s\n' \"$GOOD_VALUE\" && "
                    "cat /tmp/tw-missing-export.err"
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
        stdout_lines = result.stdout.splitlines()
        assert_same_path(self, stdout_lines[0], workspace)
        self.assertEqual(stdout_lines[1], "before")
        self.assertIn("directory does not exist", result.stdout)
        self.assertNotIn("after", result.stdout)

    def test_tw_activate_invalid_export_preserves_directory_and_existing_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            workspace = temp_path / "Workspace"
            bin_dir.mkdir()
            workspace.mkdir()
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            env["GOOD_VALUE"] = "before"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$2" && '
                    "taurworks project create Alpha --local "
                    "--working-dir repo --create-working-dir >/dev/null && "
                    "cat >> Alpha/.taurworks/config.toml <<'EOF'\n"
                    "\n[activation.exports]\n"
                    'GOOD_VALUE = "after"\n'
                    '"BAD-NAME" = "bad"\n'
                    "EOF\n"
                    "before=$(pwd) && "
                    "if tw activate Alpha >/tmp/tw-invalid-export.out 2>/tmp/tw-invalid-export.err; "
                    "then exit 20; fi && "
                    'test "$(pwd)" = "$before" && '
                    "pwd && "
                    "printf '%s\n' \"$GOOD_VALUE\" && "
                    "cat /tmp/tw-invalid-export.err"
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
        stdout_lines = result.stdout.splitlines()
        assert_same_path(self, stdout_lines[0], workspace)
        self.assertEqual(stdout_lines[1], "before")
        self.assertIn("activation failed for Alpha", result.stdout)
        self.assertIn("invalid activation export name", result.stdout)
        self.assertNotIn("after", result.stdout)
        self.assertNotIn("bad", result.stdout)


class ShellRefreshTest(unittest.TestCase):
    """WI-SHELL-HELPER-REFRESH-0001.

    `tw shell refresh` fixes the on-demand half of the stale-shell-helper
    problem: it re-prints the packaged helper from the currently installed
    `taurworks`, overwrites the on-disk file, and re-sources it into the
    current shell. These tests shim `taurworks shell print` with a minimal
    marker script rather than the real packaged helper, so a successful
    re-source is provable by checking whether the marker variable becomes
    visible in the same shell -- proof that genuine re-sourcing happened,
    not just a file write.
    """

    def _write_marker_shim(self, bin_dir: pathlib.Path, marker_line: str) -> None:
        taurworks = bin_dir / "taurworks"
        taurworks.write_text(
            (
                "#!/bin/sh\n"
                'if [ "$1" = "shell" ] && [ "$2" = "print" ]; then\n'
                f"  printf '%s\\n' '{marker_line}'\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n"
            ),
            encoding="utf-8",
        )
        taurworks.chmod(taurworks.stat().st_mode | stat.S_IXUSR)

    def test_tw_shell_refresh_writes_and_resources_new_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            target_path = temp_path / "config" / "taurworks-shell.sh"
            bin_dir.mkdir()
            self._write_marker_shim(bin_dir, "TW_SHELL_REFRESH_TEST_MARKER=refreshed")

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_SHELL_HELPER_PATH"] = str(target_path)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "tw shell refresh && "
                    "printf '%s\\n' \"$TW_SHELL_REFRESH_TEST_MARKER\""
                ),
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
            written_content = target_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(written_content, "TW_SHELL_REFRESH_TEST_MARKER=refreshed\n")
        stdout_lines = result.stdout.splitlines()
        self.assertIn(
            f"tw shell refresh: refreshed and re-sourced {target_path}",
            stdout_lines,
        )
        self.assertEqual(stdout_lines[-1], "refreshed")

    def test_tw_shell_refresh_failure_leaves_existing_file_untouched(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            target_path = temp_path / "config" / "taurworks-shell.sh"
            target_path.parent.mkdir(parents=True)
            target_path.write_text("original content\n", encoding="utf-8")
            bin_dir.mkdir()
            taurworks = bin_dir / "taurworks"
            taurworks.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            taurworks.chmod(taurworks.stat().st_mode | stat.S_IXUSR)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_SHELL_HELPER_PATH"] = str(target_path)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "if tw shell refresh >/tmp/tw-shell-refresh.out "
                    "2>/tmp/tw-shell-refresh.err; "
                    "then exit 20; fi && "
                    "cat /tmp/tw-shell-refresh.err"
                ),
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
            content_after = target_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(content_after, "original content\n")
        self.assertIn("taurworks shell print` failed", result.stdout)
        self.assertIn(str(target_path), result.stdout)

    def test_tw_shell_refresh_uses_default_path_when_no_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            home_dir = temp_path / "home"
            bin_dir.mkdir()
            home_dir.mkdir()
            self._write_marker_shim(bin_dir, "TW_SHELL_REFRESH_DEFAULT_MARKER=1")

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["HOME"] = str(home_dir)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tw shell refresh',
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
            default_path = home_dir / ".config" / "taurworks" / "taurworks-shell.sh"
            written = default_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(written, "TW_SHELL_REFRESH_DEFAULT_MARKER=1\n")

    def test_tw_shell_refresh_rejects_unexpected_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            target_path = temp_path / "config" / "taurworks-shell.sh"
            bin_dir.mkdir()
            self._write_marker_shim(bin_dir, "SHOULD_NOT_APPEAR=1")

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_SHELL_HELPER_PATH"] = str(target_path)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "if tw shell refresh extra-arg "
                    ">/tmp/tw-shell-refresh-arg.out "
                    "2>/tmp/tw-shell-refresh-arg.err; "
                    "then exit 20; fi && "
                    "cat /tmp/tw-shell-refresh-arg.err"
                ),
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

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("unexpected argument: extra-arg", result.stdout)
        self.assertFalse(target_path.exists())

    def test_tw_shell_refresh_preserves_symlink_and_updates_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            dotfiles_dir = temp_path / "dotfiles"
            config_dir = temp_path / "config"
            real_target = dotfiles_dir / "taurworks-shell.sh"
            symlink_path = config_dir / "taurworks-shell.sh"
            bin_dir.mkdir()
            dotfiles_dir.mkdir()
            config_dir.mkdir()
            real_target.write_text("original dotfiles content\n", encoding="utf-8")
            symlink_path.symlink_to(real_target)
            self._write_marker_shim(bin_dir, "TW_SHELL_REFRESH_SYMLINK_MARKER=1")

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_SHELL_HELPER_PATH"] = str(symlink_path)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tw shell refresh',
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
            still_symlink = symlink_path.is_symlink()
            link_destination = symlink_path.readlink() if still_symlink else None
            real_target_content = real_target.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(still_symlink, msg="refresh replaced the symlink itself")
        self.assertEqual(link_destination, real_target)
        self.assertEqual(real_target_content, "TW_SHELL_REFRESH_SYMLINK_MARKER=1\n")

    def test_tw_shell_refresh_preserves_trailing_blank_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            target_path = temp_path / "config" / "taurworks-shell.sh"
            bin_dir.mkdir()
            taurworks = bin_dir / "taurworks"
            taurworks.write_text(
                (
                    "#!/bin/sh\n"
                    'if [ "$1" = "shell" ] && [ "$2" = "print" ]; then\n'
                    "  printf '# marker line\\n\\n\\n'\n"
                    "  exit 0\n"
                    "fi\n"
                    "exit 1\n"
                ),
                encoding="utf-8",
            )
            taurworks.chmod(taurworks.stat().st_mode | stat.S_IXUSR)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_SHELL_HELPER_PATH"] = str(target_path)
            cmd = [
                "bash",
                "-c",
                'source "$1" && tw shell refresh',
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
            written_content = target_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(written_content, "# marker line\n\n\n")

    def test_tw_shell_bare_subcommand_does_not_crash_under_nounset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            bin_dir = temp_path / "bin"
            log_path = temp_path / "delegated.txt"
            bin_dir.mkdir()
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
                'set -u; source "$1" && tw shell',
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
        self.assertNotIn("unbound variable", result.stderr)
        self.assertIn("delegated:shell", result.stdout)
        self.assertEqual(delegated_args, "shell")


class LegacyTrustSourcingShellTest(unittest.TestCase):
    """WI-TRUSTED-LEGACY-SOURCING-0001.

    The interactive prompt itself (_tw_offer_legacy_trust reading from a
    real TTY) cannot be driven from a subprocess test — there is no TTY in
    this environment. _tw_legacy_prompt_choice and _tw_offer_legacy_trust
    are tested directly with piped stdin instead, which exercises the full
    prompt-and-dispatch logic (including the `taurworks legacy inspect` call
    and the trust/source decision) without needing the outer `[ -t 0 ]`
    gate in _tw_activate to pass. That outer TTY gate itself, and the live
    end-to-end conda/cd/export proof, were verified manually in a real
    shell during this work item's implementation; see the execution record.
    """

    def _write_legacy_script(self, admin_dir: pathlib.Path, sentinel: pathlib.Path):
        admin_dir.mkdir(parents=True, exist_ok=True)
        (admin_dir / "project-setup.source").write_text(
            f'#!/bin/bash\ntouch "{sentinel}"\n', encoding="utf-8"
        )

    def test_legacy_prompt_choice_maps_input_to_normalized_letter(self):
        cases = {
            "s": "s",
            "source": "s",
            "S": "s",
            "t": "t",
            "trust": "t",
            "n": "n",
            "never": "n",
            "x": "k",
            "": "k",
        }
        for raw_input, expected in cases.items():
            cmd = [
                "bash",
                "-c",
                'source "$1" && printf "%s\\n" "$2" | _tw_legacy_prompt_choice',
                "bash",
                str(SHELL_HELPER),
                raw_input,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                result.stdout.strip(), expected, msg=f"input={raw_input!r}"
            )

    def test_offer_legacy_trust_source_choice_sources_without_writing_trust(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            script_path = admin_dir / "project-setup.source"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "printf 's\\n' | "
                    '_tw_offer_legacy_trust "$2" "Proj" "$3" "False"'
                ),
                "bash",
                str(SHELL_HELPER),
                str(script_path),
                str(workspace / "Proj"),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(sentinel_exists)

    def test_offer_legacy_trust_trust_choice_writes_record_and_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            script_path = admin_dir / "project-setup.source"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "printf 't\\n' | "
                    '_tw_offer_legacy_trust "$2" "Proj" "$3" "False"'
                ),
                "bash",
                str(SHELL_HELPER),
                str(script_path),
                str(workspace / "Proj"),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            trust_config = (
                pathlib.Path(env["XDG_CONFIG_HOME"]) / "taurworks" / "config.toml"
            )
            trust_text = trust_config.read_text(encoding="utf-8")
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(sentinel_exists)
        self.assertIn("[trust.Proj]", trust_text)

    def test_offer_legacy_trust_skip_choice_does_not_source_or_trust(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            script_path = admin_dir / "project-setup.source"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "printf 'n\\n' | "
                    '_tw_offer_legacy_trust "$2" "Proj" "$3" "False"'
                ),
                "bash",
                str(SHELL_HELPER),
                str(script_path),
                str(workspace / "Proj"),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(sentinel_exists)

    def test_offer_legacy_trust_skip_message_does_not_claim_persistence(self):
        # Regression test: the prompt used to offer "[n]ever ask again" but
        # the skip branch never persisted anything, so the user would be
        # prompted again next time despite the wording. The message must not
        # claim persistence it doesn't provide.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            script_path = admin_dir / "project-setup.source"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "printf 'n\\n' | "
                    '_tw_offer_legacy_trust "$2" "Proj" "$3" "False"'
                ),
                "bash",
                str(SHELL_HELPER),
                str(script_path),
                str(workspace / "Proj"),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("again", result.stderr)
        self.assertNotIn("never", result.stderr.lower())
        self.assertIn("skip", result.stderr.lower())

    def test_offer_legacy_trust_resolves_unregistered_nonworkspace_project_by_root(
        self,
    ):
        # Regression test for a resolution bug: the prompt used to pass the
        # bare project name (not the resolved project root) to
        # `taurworks legacy inspect`/`taurworks project trust set`. For a
        # project that is neither registered nor a workspace child, that name
        # re-resolves from the project's own directory (where _tw_activate
        # has already cd'd) via find_current_project, which only recognizes
        # .taurworks-having roots -- not legacy-admin ones -- so it fell
        # through to treating the name as a child path of cwd, producing a
        # nonexistent target and silently failing to trust.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            unregistered_root = temp_path / "Elsewhere" / "Legacy"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = unregistered_root / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            script_path = admin_dir / "project-setup.source"
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    'cd "$3" && '
                    "printf 't\\n' | "
                    '_tw_offer_legacy_trust "$2" "Legacy" "$3" "False"'
                ),
                "bash",
                str(SHELL_HELPER),
                str(script_path),
                str(unregistered_root),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            trust_config = (
                pathlib.Path(env["XDG_CONFIG_HOME"]) / "taurworks" / "config.toml"
            )
            trust_text = (
                trust_config.read_text(encoding="utf-8")
                if trust_config.exists()
                else ""
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(sentinel_exists, msg=result.stderr)
        self.assertIn("[trust.Legacy]", trust_text)

    def test_tier1_disabled_produces_no_legacy_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing disable >/dev/null && "
                    'cd "$2" && '
                    "tw activate Proj"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(sentinel_exists)
        # The pre-existing legacy-admin cd-only warning is expected and
        # legitimately mentions "legacy"/"taurworks legacy migrate"; what
        # must be absent with Tier 1 off is any trace of the new
        # trust-gating feature itself.
        self.assertNotIn("untrusted legacy setup script", result.stderr)
        self.assertNotIn("[s]ource once", result.stderr)

    def test_tier1_enabled_untrusted_noninteractive_fails_open(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing enable >/dev/null && "
                    'cd "$2" && '
                    "tw activate Proj </dev/null"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(sentinel_exists)
        self.assertIn("untrusted legacy setup script", result.stderr)
        self.assertIn("--legacy", result.stderr)

    def test_tier1_enabled_trusted_sources_silently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing enable >/dev/null && "
                    "taurworks project trust set Proj >/dev/null && "
                    'cd "$2" && '
                    "tw activate Proj </dev/null"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(sentinel_exists)
        self.assertNotIn("[s]ource once", result.stderr)
        self.assertNotIn("untrusted", result.stderr)

    def test_legacy_flag_sources_once_despite_untrusted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing enable >/dev/null && "
                    'cd "$2" && '
                    "tw activate Proj --legacy </dev/null"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            trust_config = (
                pathlib.Path(env["XDG_CONFIG_HOME"]) / "taurworks" / "config.toml"
            )
            trust_text = (
                trust_config.read_text(encoding="utf-8")
                if trust_config.is_file()
                else ""
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(sentinel_exists)
        self.assertNotIn("[trust.Proj]", trust_text)

    def test_no_legacy_flag_skips_despite_trusted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing enable >/dev/null && "
                    "taurworks project trust set Proj >/dev/null && "
                    'cd "$2" && '
                    "tw activate Proj --no-legacy </dev/null"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(sentinel_exists)

    def test_legacy_flag_without_tier1_reports_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            admin_dir = workspace / "Proj" / "Admin"
            bin_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing disable >/dev/null && "
                    'cd "$2" && '
                    "tw activate Proj --legacy </dev/null"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(sentinel_exists)
        self.assertIn("--legacy requires legacy sourcing to be enabled", result.stderr)

    def test_legacy_sourcing_fires_after_declarative_activation(self):
        # WI scope extension: trust-gated sourcing must also fire for an
        # already-initialized project (config.toml present) that still has
        # a leftover legacy script, running after the config-driven cd —
        # matching the real 11-project post-migration state.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            bin_dir = temp_path / "bin"
            sentinel = temp_path / "sentinel.out"
            project_dir = workspace / "Migrated"
            repo_dir = project_dir / "repo"
            admin_dir = project_dir / "Admin"
            repo_dir.mkdir(parents=True)
            self._write_legacy_script(admin_dir, sentinel)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "Migrated"\n\n'
                '[paths]\nworking_dir = "repo"\n',
                encoding="utf-8",
            )
            bin_dir.mkdir(parents=True)
            _write_taurworks_module_shim(bin_dir)

            env = _subprocess_env()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                "bash",
                "-c",
                (
                    'source "$1" && '
                    "taurworks config legacy-sourcing enable >/dev/null && "
                    "taurworks project trust set Migrated >/dev/null && "
                    'cd "$2" && '
                    "tw activate Migrated </dev/null && pwd"
                ),
                "bash",
                str(SHELL_HELPER),
                str(workspace),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10, env=env
            )
            sentinel_exists = sentinel.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(sentinel_exists)
        assert_same_path(self, result.stdout.strip().splitlines()[-1], repo_dir)


if __name__ == "__main__":
    unittest.main()
