import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

from helpers import assert_same_path, parse_cli_fields


def _subprocess_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    isolated_root = (
        pathlib.Path(tempfile.gettempdir()) / f"taurworks-test-env-{os.getpid()}"
    )
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )
    env["HOME"] = str(isolated_root / "home")
    env["XDG_CONFIG_HOME"] = str(isolated_root / "xdg")
    env.pop("TAURWORKS_WORKSPACE", None)
    if overrides is not None:
        env.update(overrides)
    return env


def _run_cli(
    args: list[str],
    cwd: pathlib.Path,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "taurworks.cli", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env=_subprocess_env(env_overrides),
    )


def _failure_message(args: list[str], result: subprocess.CompletedProcess[str]) -> str:
    cmd = [sys.executable, "-m", "taurworks.cli", *args]
    return (
        f"Command failed: {cmd}\n"
        f"return code: {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def _single_output_path(output: str, key: str) -> pathlib.Path:
    fields = parse_cli_fields(output)
    if key not in fields:
        raise AssertionError(f"Expected {key!r} in output:\n{output}")
    return pathlib.Path(fields[key])


def _activation_command_path(output: str) -> pathlib.Path:
    fields = parse_cli_fields(output)
    command = fields.get("activation_command", "")
    prefix = "cd "
    if not command.startswith(prefix):
        raise AssertionError(
            f"Expected activation_command to start with {prefix!r}: {command!r}"
        )
    return pathlib.Path(command.removeprefix(prefix))


def _project_detail_path(output: str, label: str) -> pathlib.Path:
    prefix = f"├── {label}: "
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith(prefix):
            return pathlib.Path(line.removeprefix(prefix))
    raise AssertionError(
        f"Expected project detail label {label!r} in output:\n{output}"
    )


class CliCommandTest(unittest.TestCase):

    def test_config_where_reports_xdg_path_read_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            config_home = root_path / "xdg"
            result = _run_cli(
                ["config", "where"],
                root_path,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root_path)},
            )
        failure_message = _failure_message(["config", "where"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        fields = parse_cli_fields(result.stdout)
        assert_same_path(
            self,
            fields["config_path"],
            config_home / "taurworks" / "config.toml",
            msg=failure_message,
        )
        self.assertIn("exists: False", result.stdout, msg=failure_message)
        self.assertIn("xdg_source: XDG_CONFIG_HOME", result.stdout, msg=failure_message)
        self.assertIn("read_only: True", result.stdout, msg=failure_message)
        self.assertIn("mutation_performed: False", result.stdout, msg=failure_message)

    def test_workspace_show_without_config_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            result = _run_cli(
                ["workspace", "show"],
                root_path,
                {"HOME": str(root_path), "XDG_CONFIG_HOME": str(root_path / "xdg")},
            )
            config_path = root_path / "xdg" / "taurworks" / "config.toml"
            self.assertFalse(config_path.exists())
        failure_message = _failure_message(["workspace", "show"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("workspace_root: none", result.stdout, msg=failure_message)
        self.assertIn("workspace_root_source: unconfigured", result.stdout)
        self.assertIn("mutation_performed: False", result.stdout, msg=failure_message)

    def test_workspace_set_and_show_use_configured_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            config_home = root_path / "xdg"
            workspace = root_path / "workspace"
            workspace.mkdir()
            env = {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root_path)}
            set_result = _run_cli(["workspace", "set", str(workspace)], root_path, env)
            show_result = _run_cli(["workspace", "show"], root_path, env)
            config_data = tomllib.loads(
                (config_home / "taurworks" / "config.toml").read_text(encoding="utf-8")
            )

        set_message = _failure_message(["workspace", "set", str(workspace)], set_result)
        show_message = _failure_message(["workspace", "show"], show_result)
        self.assertEqual(set_result.returncode, 0, msg=set_message)
        set_fields = parse_cli_fields(set_result.stdout)
        assert_same_path(self, set_fields["workspace_root"], workspace, msg=set_message)
        self.assertIn("mutation_performed: True", set_result.stdout)
        self.assertEqual(show_result.returncode, 0, msg=show_message)
        show_fields = parse_cli_fields(show_result.stdout)
        self.assertEqual("configured", show_fields["workspace_root_source"])
        assert_same_path(
            self, show_fields["workspace_root"], workspace, msg=show_message
        )
        assert_same_path(self, config_data["workspace"]["root"], workspace)

    def test_dev_namespace_help_lists_read_only_diagnostics(self):
        result = _run_cli(["dev", "--help"], pathlib.Path.cwd())
        failure_message = _failure_message(["dev", "--help"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("repository/developer workflow", result.stdout.lower())
        self.assertIn("where", result.stdout, msg=failure_message)
        self.assertIn("status", result.stdout, msg=failure_message)
        self.assertIn("read-only", result.stdout, msg=failure_message)

    def test_dev_where_outside_project_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            before_entries = sorted(path.name for path in root_path.iterdir())
            result = _run_cli(["dev", "where"], root_path)
            after_entries = sorted(path.name for path in root_path.iterdir())
        failure_message = _failure_message(["dev", "where"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertEqual(before_entries, after_entries)
        self.assertIn("Taurworks dev workspace diagnostics", result.stdout)
        self.assertIn("project_root: unresolved", result.stdout)
        self.assertIn("working_dir: none", result.stdout)
        self.assertIn("inside_working_dir: False", result.stdout)
        self.assertIn("mutation_performed: False", result.stdout)

    def test_dev_where_inside_configured_working_dir_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            project_dir = workspace / "TestProject"
            repo_dir = project_dir / "repo"
            create_result = _run_cli(
                [
                    "project",
                    "create",
                    "TestProject",
                    "--local",
                    "--working-dir",
                    "repo",
                    "--create-working-dir",
                ],
                workspace,
            )
            create_message = _failure_message(
                [
                    "project",
                    "create",
                    "TestProject",
                    "--local",
                    "--working-dir",
                    "repo",
                    "--create-working-dir",
                ],
                create_result,
            )
            self.assertEqual(create_result.returncode, 0, msg=create_message)
            before_config = (project_dir / ".taurworks" / "config.toml").read_text(
                encoding="utf-8"
            )
            result = _run_cli(["dev", "where"], repo_dir)
            after_config = (project_dir / ".taurworks" / "config.toml").read_text(
                encoding="utf-8"
            )
        failure_message = _failure_message(["dev", "where"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertEqual(before_config, after_config)
        fields = parse_cli_fields(result.stdout)
        assert_same_path(self, fields["project_root"], project_dir, msg=failure_message)
        self.assertIn("working_dir_configured: True", result.stdout)
        self.assertIn("working_dir: repo", result.stdout)
        assert_same_path(
            self, fields["resolved_working_dir"], repo_dir, msg=failure_message
        )
        self.assertIn("inside_working_dir: True", result.stdout)
        self.assertIn("mutation_performed: False", result.stdout)

    def test_dev_status_reports_future_vcs_work_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            before_entries = sorted(path.name for path in root_path.iterdir())
            result = _run_cli(["dev", "status"], root_path)
            after_entries = sorted(path.name for path in root_path.iterdir())
        failure_message = _failure_message(["dev", "status"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertEqual(before_entries, after_entries)
        self.assertIn("Taurworks dev status", result.stdout)
        self.assertIn("detailed_vcs_status: not implemented", result.stdout)
        self.assertIn("no git commands were run", result.stdout)
        self.assertIn("mutation_performed: False", result.stdout)

    def test_project_list_ignores_real_home_when_env_is_isolated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            real_home = root_path / "real-home"
            real_workspace = root_path / "real-workspace"
            real_project = real_workspace / "RealProject"
            isolated_home = root_path / "isolated-home"
            isolated_xdg = root_path / "isolated-xdg"
            real_project_config = real_project / ".taurworks" / "config.toml"
            real_project_config.parent.mkdir(parents=True)
            real_project_config.write_text(
                'schema_version = 1\n\n[project]\nname = "RealProject"\n',
                encoding="utf-8",
            )
            real_config = real_home / ".config" / "taurworks" / "config.toml"
            real_config.parent.mkdir(parents=True)
            real_config.write_text(
                f'schema_version = 1\n\n[workspace]\nroot = "{real_workspace}"\n',
                encoding="utf-8",
            )

            unisolated_env = _subprocess_env({"HOME": str(real_home)})
            unisolated_env.pop("XDG_CONFIG_HOME", None)
            unisolated = subprocess.run(
                [sys.executable, "-m", "taurworks.cli", "project", "list"],
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=unisolated_env,
            )
            isolated = _run_cli(
                ["project", "list"],
                root_path,
                {"HOME": str(isolated_home), "XDG_CONFIG_HOME": str(isolated_xdg)},
            )

        unisolated_message = _failure_message(["project", "list"], unisolated)
        self.assertEqual(unisolated.returncode, 0, msg=unisolated_message)
        self.assertIn("project_count: 1", unisolated.stdout, msg=unisolated_message)
        self.assertIn("RealProject", unisolated.stdout, msg=unisolated_message)
        isolated_message = _failure_message(["project", "list"], isolated)
        self.assertEqual(isolated.returncode, 0, msg=isolated_message)
        self.assertIn("project_count: 0", isolated.stdout, msg=isolated_message)
        self.assertNotIn("RealProject", isolated.stdout, msg=isolated_message)

    def test_project_list_ignores_caller_taurworks_workspace_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            caller_workspace = root_path / "caller-workspace"
            caller_project_config = (
                caller_workspace / "CallerProject" / ".taurworks" / "config.toml"
            )
            caller_project_config.parent.mkdir(parents=True)
            caller_project_config.write_text(
                'schema_version = 1\n\n[project]\nname = "CallerProject"\n',
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ, {"TAURWORKS_WORKSPACE": str(caller_workspace)}
            ):
                result = _run_cli(["project", "list"], root_path)

        failure_message = _failure_message(["project", "list"], result)
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("project_count: 0", result.stdout, msg=failure_message)
        self.assertNotIn("CallerProject", result.stdout, msg=failure_message)

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
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("where", result.stdout, msg=failure_message)
        self.assertIn("list", result.stdout, msg=failure_message)
        self.assertIn("working-dir", result.stdout, msg=failure_message)
        self.assertIn("read-only", result.stdout, msg=failure_message)

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
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("read-only", result.stdout, msg=failure_message)

    def test_project_init_and_create_help_distinguish_existing_and_new_roots(self):
        init_args = ["project", "init", "--help"]
        create_args = ["project", "create", "--help"]
        init_result = _run_cli(init_args, pathlib.Path.cwd())
        create_result = _run_cli(create_args, pathlib.Path.cwd())
        init_message = _failure_message(init_args, init_result)
        create_message = _failure_message(create_args, create_result)

        self.assertEqual(init_result.returncode, 0, msg=init_message)
        self.assertEqual(create_result.returncode, 0, msg=create_message)
        self.assertIn(
            "existing/current directory", init_result.stdout, msg=init_message
        )
        self.assertIn("use project create", init_result.stdout, msg=init_message)
        self.assertIn("new", init_result.stdout, msg=init_message)
        self.assertIn("roots", init_result.stdout, msg=init_message)
        self.assertIn("new project root", create_result.stdout, msg=create_message)
        self.assertIn("project init for", create_result.stdout, msg=create_message)
        self.assertIn(
            "existing/current roots", create_result.stdout, msg=create_message
        )
        self.assertIn("--create-working-dir", create_result.stdout, msg=create_message)
        self.assertIn("--nested", create_result.stdout, msg=create_message)

    def test_dogfood_create_from_parent_and_target_aware_activation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            project_dir = workspace / "TestProject"
            repo_dir = project_dir / "test_repo"

            create_args = [
                "project",
                "create",
                "TestProject",
                "--local",
                "--working-dir",
                "test_repo",
                "--create-working-dir",
            ]
            create_result = _run_cli(create_args, workspace)
            create_message = _failure_message(create_args, create_result)
            self.assertEqual(create_result.returncode, 0, msg=create_message)
            self.assertTrue(
                (project_dir / ".taurworks" / "config.toml").is_file(),
                msg=create_message,
            )
            self.assertTrue(repo_dir.is_dir(), msg=create_message)
            self.assertIn("working_dir_created: True", create_result.stdout)

            show_args = ["project", "working-dir", "show", "TestProject"]
            show_result = _run_cli(show_args, workspace)
            show_message = _failure_message(show_args, show_result)
            self.assertEqual(show_result.returncode, 0, msg=show_message)
            self.assertEqual(
                project_dir.resolve(),
                _single_output_path(show_result.stdout, "project_root").resolve(),
                msg=show_message,
            )
            self.assertIn("working_dir: test_repo", show_result.stdout)

            activate_args = ["project", "activate", "TestProject", "--print"]
            activate_result = _run_cli(
                activate_args, workspace, {"TAURWORKS_WORKSPACE": str(workspace)}
            )
            activate_message = _failure_message(activate_args, activate_result)
            self.assertEqual(activate_result.returncode, 0, msg=activate_message)
            self.assertEqual(
                project_dir.resolve(),
                _single_output_path(activate_result.stdout, "project_root").resolve(),
                msg=activate_message,
            )
            self.assertEqual(
                repo_dir.resolve(),
                _single_output_path(
                    activate_result.stdout, "resolved_working_dir"
                ).resolve(),
                msg=activate_message,
            )
            self.assertIn("shell_mutation: not performed", activate_result.stdout)

            inside_activate_result = _run_cli(activate_args, project_dir)
            inside_message = _failure_message(activate_args, inside_activate_result)
            self.assertEqual(inside_activate_result.returncode, 0, msg=inside_message)
            self.assertEqual(
                project_dir.resolve(),
                _single_output_path(
                    inside_activate_result.stdout, "project_root"
                ).resolve(),
                msg=inside_message,
            )
            self.assertIn(
                "resolved_by: current_project_name", inside_activate_result.stdout
            )
            self.assertNotIn(
                str(project_dir / "TestProject"), inside_activate_result.stdout
            )

    def test_dogfood_init_existing_directory_and_set_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            project_dir = workspace / "TestProject"
            repo_dir = project_dir / "test_repo"
            other_repo = project_dir / "other_repo"
            repo_dir.mkdir(parents=True)

            init_args = ["project", "init", "--working-dir", "test_repo"]
            init_result = _run_cli(init_args, project_dir)
            init_message = _failure_message(init_args, init_result)
            self.assertEqual(init_result.returncode, 0, msg=init_message)
            self.assertTrue((project_dir / ".taurworks" / "config.toml").is_file())
            self.assertIn("working_dir: test_repo", init_result.stdout)
            self.assertIn("working_dir_created: False", init_result.stdout)

            activate_args = ["project", "activate", "--print"]
            activate_result = _run_cli(activate_args, project_dir)
            activate_message = _failure_message(activate_args, activate_result)
            self.assertEqual(activate_result.returncode, 0, msg=activate_message)
            self.assertEqual(
                repo_dir.resolve(),
                _single_output_path(
                    activate_result.stdout, "resolved_working_dir"
                ).resolve(),
                msg=activate_message,
            )

            other_repo.mkdir()
            set_args = ["project", "working-dir", "set", "other_repo"]
            set_result = _run_cli(set_args, project_dir)
            set_message = _failure_message(set_args, set_result)
            self.assertEqual(set_result.returncode, 0, msg=set_message)
            self.assertIn("working_dir: other_repo", set_result.stdout)

            show_args = ["project", "working-dir", "show"]
            show_result = _run_cli(show_args, project_dir)
            show_message = _failure_message(show_args, show_result)
            self.assertEqual(show_result.returncode, 0, msg=show_message)
            self.assertIn("working_dir: other_repo", show_result.stdout)

            changed_activate_result = _run_cli(activate_args, project_dir)
            changed_message = _failure_message(activate_args, changed_activate_result)
            self.assertEqual(changed_activate_result.returncode, 0, msg=changed_message)
            self.assertEqual(
                other_repo.resolve(),
                _single_output_path(
                    changed_activate_result.stdout, "resolved_working_dir"
                ).resolve(),
                msg=changed_message,
            )

    def test_project_list_succeeds_without_discovered_projects(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "list"]
            env = _subprocess_env()
            env["XDG_CONFIG_HOME"] = str(pathlib.Path(temp_dir) / "xdg-config")
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("project_count: 0", result.stdout, msg=failure_message)

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
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue((target_dir / ".taurworks").is_dir(), msg=failure_message)
            self.assertTrue(
                (target_dir / ".taurworks" / "config.toml").is_file(),
                msg=failure_message,
            )
            self.assertIn(
                "delegated_command: project refresh", result.stdout, msg=failure_message
            )

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
                env=_subprocess_env(),
            )
            second = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        first_message = f"First command failed: {cmd}\nreturn code: {first.returncode}\nstdout:\n{first.stdout}\nstderr:\n{first.stderr}"
        second_message = f"Second command failed: {cmd}\nreturn code: {second.returncode}\nstdout:\n{second.stdout}\nstderr:\n{second.stderr}"
        self.assertEqual(first.returncode, 0, msg=first_message)
        self.assertEqual(second.returncode, 0, msg=second_message)
        self.assertIn("changed: True", first.stdout, msg=first_message)
        self.assertIn("changed: False", second.stdout, msg=second_message)

    def test_project_create_without_working_dir_does_not_invent_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "no-working-dir-project"
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
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        self.assertEqual("no-working-dir-project", config["project"]["name"])
        self.assertNotIn("paths", config)
        self.assertIn(
            "working_dir_requested: False", result.stdout, msg=failure_message
        )

    def test_project_create_records_working_dir_without_creating_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "created-with-working-dir"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
                "--working-dir",
                "repo",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        self.assertEqual("created-with-working-dir", config["project"]["name"])
        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertFalse((target_dir / "repo").exists(), msg=failure_message)
        self.assertIn("working_dir: repo", result.stdout, msg=failure_message)
        self.assertIn("working_dir_exists: False", result.stdout, msg=failure_message)
        self.assertIn("working_dir_created: False", result.stdout, msg=failure_message)

    def test_project_create_with_create_working_dir_creates_and_records_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "created-workdir-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                "created-workdir-project",
                "--local",
                "--working-dir",
                "repo",
                "--create-working-dir",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
            self.assertEqual("repo", config["paths"]["working_dir"])
            self.assertTrue((target_dir / "repo").is_dir(), msg=failure_message)
            self.assertIn(
                "working_dir_created: True", result.stdout, msg=failure_message
            )

    def test_project_create_bare_name_defaults_to_configured_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            workspace = root_path / "workspace"
            local = root_path / "local"
            workspace.mkdir()
            local.mkdir()
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            set_result = _run_cli(["workspace", "set", str(workspace)], root_path, env)
            result = _run_cli(["project", "create", "Alpha"], local, env)
            list_result = _run_cli(["projects"], local, env)
            activate_result = _run_cli(
                ["project", "activate", "Alpha", "--print"], local, env
            )
            failure_message = _failure_message(["project", "create", "Alpha"], result)
            self.assertEqual(set_result.returncode, 0, msg=set_result.stderr)
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue(
                (workspace / "Alpha" / ".taurworks" / "config.toml").is_file()
            )
            self.assertFalse((local / "Alpha").exists())
            self.assertIn(f"project_root: {workspace / 'Alpha'}", result.stdout)
            self.assertIn("target_selection: configured_workspace", result.stdout)
            self.assertIn(f"workspace_root: {workspace}", result.stdout)
            self.assertEqual(list_result.returncode, 0, msg=list_result.stderr)
            self.assertIn("- Alpha    initialized    workspace", list_result.stdout)
            self.assertEqual(activate_result.returncode, 0, msg=activate_result.stderr)
            self.assertIn(
                f"project_root: {workspace / 'Alpha'}", activate_result.stdout
            )

    def test_project_create_dot_prefixed_name_is_explicit_local_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            workspace = root_path / "workspace"
            local = root_path / "local"
            workspace.mkdir()
            local.mkdir()
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            _run_cli(["workspace", "set", str(workspace)], root_path, env)
            result = _run_cli(["project", "create", "./Alpha"], local, env)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue((local / "Alpha" / ".taurworks" / "config.toml").is_file())
            self.assertFalse((workspace / "Alpha").exists())
            self.assertIn("target_selection: positional_path", result.stdout)
            self.assertIn("path_argument: ./Alpha", result.stdout)

    def test_project_create_dotdot_is_explicit_path_not_workspace_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            workspace = root_path / "workspace"
            local = root_path / "local"
            inner = local / "inner"
            workspace.mkdir()
            inner.mkdir(parents=True)
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            _run_cli(["workspace", "set", str(workspace)], root_path, env)
            result = _run_cli(["project", "create", ".."], inner, env)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue((local / ".taurworks" / "config.toml").is_file())
            self.assertFalse((root_path / ".taurworks").exists())
            self.assertIn(f"project_root: {local}", result.stdout)
            self.assertIn("target_selection: positional_path", result.stdout)
            self.assertIn("path_argument: ..", result.stdout)

    def test_project_create_workspace_default_creates_working_dir_under_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            workspace = root_path / "workspace"
            local = root_path / "local"
            workspace.mkdir()
            local.mkdir()
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            _run_cli(["workspace", "set", str(workspace)], root_path, env)
            result = _run_cli(
                [
                    "project",
                    "create",
                    "Alpha",
                    "--working-dir",
                    "repo",
                    "--create-working-dir",
                ],
                local,
                env,
            )
            failure_message = _failure_message(
                ["project", "create", "Alpha", "--working-dir", "repo"], result
            )
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue((workspace / "Alpha" / "repo").is_dir())
            self.assertFalse((local / "Alpha").exists())
            self.assertIn("working_dir_created: True", result.stdout)

    def test_project_create_local_creates_under_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            workspace = root_path / "workspace"
            local = root_path / "local"
            workspace.mkdir()
            local.mkdir()
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            _run_cli(["workspace", "set", str(workspace)], root_path, env)
            result = _run_cli(
                [
                    "project",
                    "create",
                    "LocalAlpha",
                    "--local",
                    "--working-dir",
                    "repo",
                    "--create-working-dir",
                ],
                local,
                env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue((local / "LocalAlpha" / "repo").is_dir())
            self.assertFalse((workspace / "LocalAlpha").exists())
            self.assertIn("target_selection: local", result.stdout)
            self.assertIn("local_requested: True", result.stdout)

    def test_project_create_explicit_path_creates_at_path_and_warns_outside_workspace(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            workspace = root_path / "workspace"
            custom_parent = root_path / "custom"
            workspace.mkdir()
            custom_parent.mkdir()
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            _run_cli(["workspace", "set", str(workspace)], root_path, env)
            custom = custom_parent / "CustomAlpha"
            result = _run_cli(
                [
                    "project",
                    "create",
                    "CustomAlpha",
                    "--path",
                    str(custom),
                    "--working-dir",
                    "repo",
                    "--create-working-dir",
                ],
                root_path,
                env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue((custom / "repo").is_dir())
            self.assertFalse((workspace / "CustomAlpha").exists())
            self.assertIn("target_selection: explicit_path", result.stdout)
            self.assertIn("outside the configured workspace root", result.stdout)

    def test_project_create_local_and_path_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            result = _run_cli(
                [
                    "project",
                    "create",
                    "Alpha",
                    "--local",
                    "--path",
                    str(root_path / "Alpha"),
                ],
                root_path,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed with argument", result.stderr)

    def test_project_create_no_configured_workspace_requires_explicit_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            env = {"XDG_CONFIG_HOME": str(root_path / "xdg"), "HOME": str(root_path)}
            result = _run_cli(["project", "create", "Alpha"], root_path, env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root_path / "Alpha").exists())
        self.assertIn("no configured workspace root", result.stdout)
        self.assertIn("taurworks workspace set PATH", result.stdout)
        self.assertIn("--local", result.stdout)

    def test_project_create_path_does_not_ignore_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            result = _run_cli(
                ["project", "create", "Alpha", "--path", str(root_path / "Beta")],
                root_path,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root_path / "Beta").exists())
        self.assertIn("does not match NAME", result.stdout)

    def test_project_create_refuses_same_name_nested_from_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            (project_dir / ".taurworks").mkdir(parents=True)
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "TestProject"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                "TestProject",
                "--local",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((project_dir / "TestProject").exists())
        self.assertIn("refusing to create a nested same-name project", result.stdout)
        self.assertIn("taurworks project init", result.stdout)
        self.assertIn("--nested", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_create_refuses_same_name_nested_with_trailing_separator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            project_dir.mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                "TestProject/",
                "--local",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((project_dir / "TestProject").exists())
        self.assertIn("refusing to create a nested same-name project", result.stdout)
        self.assertIn("--nested", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_create_handles_unreadable_current_config_probe(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "CurrentProject"
            (project_dir / ".taurworks" / "config.toml").mkdir(parents=True)
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                "ChildProject",
                "--local",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue(
                (project_dir / "ChildProject" / ".taurworks" / "config.toml").is_file(),
                msg=failure_message,
            )
            self.assertNotIn("Traceback", result.stderr)

    def test_project_create_refuses_same_name_nested_from_basename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            project_dir.mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                "TestProject",
                "--local",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((project_dir / "TestProject").exists())
        self.assertIn("refusing to create a nested same-name project", result.stdout)
        self.assertIn("--nested", result.stdout)

    def test_project_create_nested_allows_same_name_child(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            project_dir.mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                "TestProject",
                "--local",
                "--nested",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            nested_project = project_dir / "TestProject"
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue((nested_project / ".taurworks" / "config.toml").is_file())
            fields = parse_cli_fields(result.stdout)
            assert_same_path(
                self, fields["project_root"], nested_project, msg=failure_message
            )

    def test_project_create_without_name_is_init_compatibility_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "create"]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue((root_path / ".taurworks" / "config.toml").is_file())
            self.assertIn("compatibility_alias: True", result.stdout)
            self.assertIn("prefer `taurworks project init`", result.stdout)

    def test_project_create_with_working_dir_is_idempotent_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "safe-project"
            target_dir.mkdir()
            existing_file = target_dir / "notes.txt"
            existing_file.write_text("keep me", encoding="utf-8")
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
                "--working-dir",
                "repo",
            ]
            first = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            second = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            first_message = f"First command failed: {cmd}\nreturn code: {first.returncode}\nstdout:\n{first.stdout}\nstderr:\n{first.stderr}"
            second_message = f"Second command failed: {cmd}\nreturn code: {second.returncode}\nstdout:\n{second.stdout}\nstderr:\n{second.stderr}"
            self.assertEqual(first.returncode, 0, msg=first_message)
            self.assertEqual(second.returncode, 0, msg=second_message)
            file_text = existing_file.read_text(encoding="utf-8")
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        self.assertEqual("keep me", file_text)
        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertIn("changed: True", first.stdout, msg=first_message)
        self.assertIn("changed: False", second.stdout, msg=second_message)
        self.assertFalse((target_dir / "repo").exists(), msg=second_message)

    def test_project_create_working_dir_reports_config_change_after_refresh(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "refreshed-project"
            refresh_cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "refresh",
                str(target_dir),
            ]
            refresh = subprocess.run(
                refresh_cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            refresh_message = f"Refresh command failed: {refresh_cmd}\nreturn code: {refresh.returncode}\nstdout:\n{refresh.stdout}\nstderr:\n{refresh.stderr}"
            self.assertEqual(refresh.returncode, 0, msg=refresh_message)

            create_cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
                "--working-dir",
                "repo",
            ]
            create = subprocess.run(
                create_cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            create_message = f"Create command failed: {create_cmd}\nreturn code: {create.returncode}\nstdout:\n{create.stdout}\nstderr:\n{create.stderr}"
            self.assertEqual(create.returncode, 0, msg=create_message)
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertIn("changed: True", create.stdout, msg=create_message)
        self.assertIn(
            "config updated: paths.working_dir set to repo",
            create.stdout,
            msg=create_message,
        )
        self.assertIn("working_dir_changed: True", create.stdout, msg=create_message)
        self.assertNotIn("result: no changes needed", create.stdout, msg=create_message)

    def test_project_create_rejects_escaping_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "escape-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
                "--working-dir",
                "../outside",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target_dir.exists())
        self.assertIn("may not escape", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_init_initializes_current_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            existing_file = root_path / "notes.txt"
            existing_file.write_text("keep me", encoding="utf-8")
            cmd = [sys.executable, "-m", "taurworks.cli", "project", "init"]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            config = tomllib.loads(
                (root_path / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
            file_text = existing_file.read_text(encoding="utf-8")
            self.assertEqual(root_path.name, config["project"]["name"])
            self.assertEqual("keep me", file_text)
            fields = parse_cli_fields(result.stdout)
            assert_same_path(
                self, fields["project_root"], root_path, msg=failure_message
            )
            self.assertIn("root_exists: True", result.stdout, msg=failure_message)
            self.assertIn("root_created: False", result.stdout, msg=failure_message)

    def test_project_init_initializes_existing_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "ExistingProject"
            target_dir.mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertTrue((target_dir / ".taurworks" / "config.toml").is_file())
            fields = parse_cli_fields(result.stdout)
            assert_same_path(
                self, fields["project_root"], target_dir, msg=failure_message
            )
            self.assertIn(
                "working_dir_requested: False", result.stdout, msg=failure_message
            )

    def test_project_init_rejects_missing_project_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "missing-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target_dir.exists())
            self.assertIn("target must be an existing directory", result.stdout)
            self.assertIn("root_exists: False", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_project_init_is_idempotent_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "idempotent-init"
            target_dir.mkdir()
            existing_file = target_dir / "notes.txt"
            existing_file.write_text("keep me", encoding="utf-8")
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
            ]
            first = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            second = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            first_message = f"First command failed: {cmd}\nreturn code: {first.returncode}\nstdout:\n{first.stdout}\nstderr:\n{first.stderr}"
            second_message = f"Second command failed: {cmd}\nreturn code: {second.returncode}\nstdout:\n{second.stdout}\nstderr:\n{second.stderr}"
            self.assertEqual(first.returncode, 0, msg=first_message)
            self.assertEqual(second.returncode, 0, msg=second_message)
            file_text = existing_file.read_text(encoding="utf-8")
            self.assertEqual("keep me", file_text)
            self.assertIn("changed: True", first.stdout, msg=first_message)
            self.assertIn("changed: False", second.stdout, msg=second_message)
            self.assertIn(
                "result: no changes needed", second.stdout, msg=second_message
            )

    def test_project_init_records_existing_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "with-existing-workdir"
            repo_dir = target_dir / "repo"
            repo_dir.mkdir(parents=True)
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
                "--working-dir",
                "repo",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
            self.assertEqual("repo", config["paths"]["working_dir"])
            self.assertIn("working_dir: repo", result.stdout, msg=failure_message)
            self.assertIn(
                "working_dir_exists: True", result.stdout, msg=failure_message
            )
            self.assertIn(
                "working_dir_created: False", result.stdout, msg=failure_message
            )

    def test_project_init_missing_working_dir_requires_create_flag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "missing-workdir"
            target_dir.mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
                "--working-dir",
                "repo",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((target_dir / "repo").exists())
            self.assertFalse((target_dir / ".taurworks").exists())
            self.assertIn("unless --create-working-dir is supplied", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_project_init_create_working_dir_creates_and_records_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "create-workdir"
            target_dir.mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
                "--working-dir",
                "repo",
                "--create-working-dir",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
            self.assertTrue((target_dir / "repo").is_dir())
            self.assertEqual("repo", config["paths"]["working_dir"])
            self.assertIn(
                "working_dir_created: True", result.stdout, msg=failure_message
            )
            self.assertIn("changed: True", result.stdout, msg=failure_message)

    def test_project_init_rejects_escaping_and_absolute_working_dirs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "bad-workdir"
            target_dir.mkdir()
            escaping_cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
                "--working-dir",
                "../outside",
                "--create-working-dir",
            ]
            escaping = subprocess.run(
                escaping_cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            absolute_cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
                "--working-dir",
                str(target_dir / "repo"),
                "--create-working-dir",
            ]
            absolute = subprocess.run(
                absolute_cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            self.assertNotEqual(escaping.returncode, 0)
            self.assertNotEqual(absolute.returncode, 0)
            self.assertFalse((target_dir / ".taurworks").exists())
            self.assertFalse((root_path / "outside").exists())
            self.assertIn("may not escape", escaping.stdout)
            self.assertIn("absolute paths are not supported", absolute.stdout)
            self.assertNotIn("Traceback", escaping.stderr)
            self.assertNotIn("Traceback", absolute.stderr)

    def test_project_init_resolves_current_project_name_before_child_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            nested_same_name_dir = project_dir / "TestProject"
            nested_same_name_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "TestProject"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                "TestProject",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            fields = parse_cli_fields(result.stdout)
            assert_same_path(
                self, fields["project_root"], project_dir, msg=failure_message
            )
            self.assertIn(
                "resolved_by: current_project_name",
                result.stdout,
                msg=failure_message,
            )
            self.assertFalse(
                (nested_same_name_dir / ".taurworks").exists(), msg=failure_message
            )

    def test_project_init_resolves_current_basename_before_child_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            nested_same_name_dir = project_dir / "TestProject"
            nested_same_name_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "ConfiguredName"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                "TestProject",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            fields = parse_cli_fields(result.stdout)
            assert_same_path(
                self, fields["project_root"], project_dir, msg=failure_message
            )
            self.assertIn(
                "resolved_by: current_directory_basename",
                result.stdout,
                msg=failure_message,
            )
            self.assertFalse(
                (nested_same_name_dir / ".taurworks").exists(), msg=failure_message
            )

    def test_project_init_treats_refresh_warnings_as_nonfatal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "warning-project"
            project_dir.mkdir()
            linked_metadata_dir = root_path / "linked-metadata"
            linked_metadata_dir.mkdir()
            (project_dir / ".taurworks").symlink_to(
                linked_metadata_dir, target_is_directory=True
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(project_dir),
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=failure_message)
            self.assertIn("ok: True", result.stdout, msg=failure_message)
            self.assertIn("warnings:", result.stdout, msg=failure_message)
            self.assertIn("metadata path is a symlink", result.stdout)

    def test_project_init_create_working_dir_requires_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                "--create-working-dir",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root_path / ".taurworks").exists())
        self.assertIn("--create-working-dir requires --working-dir", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_init_create_working_dir_rejects_existing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "file-workdir"
            target_dir.mkdir()
            (target_dir / "repo").write_text("not a directory", encoding="utf-8")
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "init",
                str(target_dir),
                "--working-dir",
                "repo",
                "--create-working-dir",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((target_dir / ".taurworks").exists())
            self.assertIn(
                "working_dir target exists but is not a directory", result.stdout
            )
            self.assertNotIn("FileExistsError", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_project_create_rejects_absolute_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "absolute-project"
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "create",
                str(target_dir),
                "--working-dir",
                str(target_dir / "repo"),
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target_dir.exists())
        self.assertIn("absolute paths are not supported", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_refresh_warns_when_metadata_path_is_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-with-bad-metadata"
            target_dir.mkdir()
            (target_dir / ".taurworks").write_text("file", encoding="utf-8")
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
                env=_subprocess_env(),
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn(
            "metadata path exists but is not a directory",
            result.stdout,
            msg=failure_message,
        )
        self.assertIn(
            "warnings present; review skipped items", result.stdout, msg=failure_message
        )

    def test_project_working_dir_show_reports_unconfigured_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "project-a"
            (project_dir / ".taurworks").mkdir(parents=True)
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "project-a"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "show",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn(
            "working_dir_configured: False", result.stdout, msg=failure_message
        )
        self.assertIn(
            "No working_dir is configured", result.stdout, msg=failure_message
        )
        self.assertEqual("", result.stderr, msg=failure_message)

    def test_project_working_dir_show_accepts_project_name_from_parent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "TestProject"
            repo_dir = project_dir / "test_repo"
            repo_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "TestProject"\n\n'
                    '[paths]\nworking_dir = "test_repo"\n'
                ),
                encoding="utf-8",
            )
            files_before = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "show",
                "TestProject",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            files_after = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("input: TestProject", result.stdout, msg=failure_message)
        fields = parse_cli_fields(result.stdout)
        assert_same_path(self, fields["project_root"], project_dir, msg=failure_message)
        self.assertIn(
            "resolved_by: existing_path_project_root",
            result.stdout,
            msg=failure_message,
        )
        self.assertIn("working_dir: test_repo", result.stdout, msg=failure_message)
        self.assertEqual(files_before, files_after, msg=failure_message)

    def test_project_working_dir_show_unknown_name_is_safe(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            files_before = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "show",
                "MissingProject",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            files_after = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("resolved_by: child_path", result.stdout)
        self.assertIn("No Taurworks project metadata found", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(files_before, files_after)

    def test_project_working_dir_set_writes_relative_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "project-a"
            repo_dir = project_dir / "repo"
            repo_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "project-a"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "set",
                "repo",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            config_text = (project_dir / ".taurworks" / "config.toml").read_text(
                encoding="utf-8"
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("working_dir: repo", result.stdout, msg=failure_message)
        self.assertIn('[paths]\nworking_dir = "repo"', config_text)

    def test_project_working_dir_set_without_argument_uses_current_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "project-a"
            repo_dir = project_dir / "repo"
            repo_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                '[project]\nname = ""\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "set",
            ]
            result = subprocess.run(
                cmd,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            config_text = (project_dir / ".taurworks" / "config.toml").read_text(
                encoding="utf-8"
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("working_dir: repo", result.stdout, msg=failure_message)
        self.assertIn(
            "project.name set to project-a", result.stdout, msg=failure_message
        )
        self.assertIn("schema_version = 1", config_text)
        self.assertIn('name = "project-a"', config_text)
        self.assertIn('working_dir = "repo"', config_text)

    def test_project_working_dir_set_rejects_absolute_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "project-a"
            repo_dir = project_dir / "repo"
            repo_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "project-a"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "set",
                str(repo_dir),
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("absolute paths are not supported", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_working_dir_set_rejects_escape_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "project-a"
            project_dir.mkdir()
            outside_dir = root_path / "outside"
            outside_dir.mkdir()
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "project-a"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "set",
                "../outside",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("may not escape", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_project_working_dir_set_rejects_symlinked_metadata_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            project_dir = root_path / "project-a"
            project_dir.mkdir()
            repo_dir = project_dir / "repo"
            repo_dir.mkdir()
            linked_metadata_dir = root_path / "linked-metadata"
            linked_metadata_dir.mkdir()
            config_path = linked_metadata_dir / "config.toml"
            original_config = 'schema_version = 1\n\n[project]\nname = "project-a"\n'
            config_path.write_text(original_config, encoding="utf-8")
            (project_dir / ".taurworks").symlink_to(
                linked_metadata_dir, target_is_directory=True
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "working-dir",
                "set",
                "repo",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            config_text = config_path.read_text(encoding="utf-8")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("metadata path is a symlink", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original_config, config_text)

    def test_project_activate_print_reports_configured_working_dir_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-a"
            repo_dir = target_dir / "repo"
            repo_dir.mkdir(parents=True)
            (target_dir / ".taurworks").mkdir()
            (target_dir / ".taurworks" / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "project-a"\n\n'
                    '[paths]\nworking_dir = "repo"\n'
                ),
                encoding="utf-8",
            )
            files_before = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                str(target_dir),
                "--print",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            files_after = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn(
            "activation guidance (read-only)", result.stdout, msg=failure_message
        )
        fields = parse_cli_fields(result.stdout)
        assert_same_path(self, fields["project_root"], target_dir, msg=failure_message)
        self.assertIn(
            "working_dir_configured: True", result.stdout, msg=failure_message
        )
        self.assertIn("working_dir: repo", result.stdout, msg=failure_message)
        assert_same_path(
            self, fields["resolved_working_dir"], repo_dir, msg=failure_message
        )
        self.assertIn("working_dir_exists: True", result.stdout, msg=failure_message)
        assert_same_path(
            self, _activation_command_path(result.stdout), repo_dir, msg=failure_message
        )
        self.assertIn(
            "shell_mutation: not performed", result.stdout, msg=failure_message
        )
        self.assertIn("was not executed", result.stdout, msg=failure_message)
        self.assertEqual(files_before, files_after, msg=failure_message)

    def test_project_activate_project_name_from_inside_resolves_current_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "TestProject"
            repo_dir = target_dir / "test_repo"
            repo_dir.mkdir(parents=True)
            (target_dir / "TestProject").mkdir()
            (target_dir / ".taurworks").mkdir()
            (target_dir / ".taurworks" / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "TestProject"\n\n'
                    '[paths]\nworking_dir = "test_repo"\n'
                ),
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                "TestProject",
                "--print",
            ]
            result = subprocess.run(
                cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        fields = parse_cli_fields(result.stdout)
        assert_same_path(self, fields["project_root"], target_dir, msg=failure_message)
        self.assertIn(
            "resolved_by: current_project_name", result.stdout, msg=failure_message
        )
        assert_same_path(
            self, fields["resolved_working_dir"], repo_dir, msg=failure_message
        )
        self.assertNotIn(str(target_dir / "TestProject"), result.stdout)

    def test_project_activate_print_reports_unconfigured_working_dir_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-a"
            (target_dir / ".taurworks").mkdir(parents=True)
            (target_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "project-a"\n',
                encoding="utf-8",
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                str(target_dir),
                "--print",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn(
            "working_dir_configured: False", result.stdout, msg=failure_message
        )
        self.assertIn("working_dir: none", result.stdout, msg=failure_message)
        assert_same_path(
            self,
            _activation_command_path(result.stdout),
            target_dir,
            msg=failure_message,
        )
        self.assertIn(
            "No working_dir is configured",
            result.stdout,
            msg=failure_message,
        )
        self.assertIn(
            "shell_mutation: not performed", result.stdout, msg=failure_message
        )

    def test_project_activate_print_reports_missing_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-a"
            missing_dir = target_dir / "missing-repo"
            (target_dir / ".taurworks").mkdir(parents=True)
            (target_dir / ".taurworks" / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "project-a"\n\n'
                    '[paths]\nworking_dir = "missing-repo"\n'
                ),
                encoding="utf-8",
            )
            files_before = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                str(target_dir),
                "--print",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            files_after = sorted(
                str(path.relative_to(root_path)) for path in root_path.rglob("*")
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("working_dir: missing-repo", result.stdout, msg=failure_message)
        fields = parse_cli_fields(result.stdout)
        assert_same_path(
            self, fields["resolved_working_dir"], missing_dir, msg=failure_message
        )
        self.assertIn("working_dir_exists: False", result.stdout, msg=failure_message)
        assert_same_path(
            self,
            _activation_command_path(result.stdout),
            missing_dir,
            msg=failure_message,
        )
        self.assertIn("directory does not exist", result.stdout, msg=failure_message)
        self.assertFalse(missing_dir.exists(), msg=failure_message)
        self.assertEqual(files_before, files_after, msg=failure_message)

    def test_project_activate_print_rejects_escaping_working_dir_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-a"
            (target_dir / ".taurworks").mkdir(parents=True)
            (target_dir / ".taurworks" / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "project-a"\n\n'
                    '[paths]\nworking_dir = "../outside"\n'
                ),
                encoding="utf-8",
            )
            original_config = (target_dir / ".taurworks" / "config.toml").read_text(
                encoding="utf-8"
            )
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                str(target_dir),
                "--print",
            ]
            result = subprocess.run(
                cmd,
                cwd=root_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
            current_config = (target_dir / ".taurworks" / "config.toml").read_text(
                encoding="utf-8"
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("working_dir is invalid", result.stdout)
        self.assertIn("may not escape", result.stdout)
        self.assertIn("shell_mutation: not performed", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original_config, current_config)

    def test_project_activate_requires_print_flag(self):
        cmd = [sys.executable, "-m", "taurworks.cli", "project", "activate"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env=_subprocess_env(),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires --print", result.stderr)

    def test_project_activate_explicit_path_does_not_collapse_to_parent_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            parent_project = root_path / "parent-project"
            (parent_project / ".taurworks").mkdir(parents=True)
            (parent_project / ".taurworks" / "config.toml").write_text(
                '[project]\nname = "parent-project"\n', encoding="utf-8"
            )
            (parent_project / "child-project").mkdir()
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                "./child-project",
                "--print",
            ]
            result = subprocess.run(
                cmd,
                cwd=parent_project,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_subprocess_env(),
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        fields = parse_cli_fields(result.stdout)
        project_root = pathlib.Path(fields["project_root"])
        self.assertEqual(
            (parent_project / "child-project").resolve(),
            project_root.resolve(),
            msg=failure_message,
        )
        self.assertEqual("child-project", project_root.name, msg=failure_message)
        assert_same_path(
            self,
            _activation_command_path(result.stdout),
            parent_project / "child-project",
            msg=failure_message,
        )

    def test_projects_lists_workspace_entries_with_status_classification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            initialized = workspace / "Initialized"
            initialized_repo = initialized / "repo"
            initialized_config = initialized / ".taurworks" / "config.toml"
            workspace_only = workspace / "WorkspaceOnly"
            legacy_admin = workspace / "LegacyAdmin"
            legacy_setup = legacy_admin / "Admin" / "project-setup.source"

            initialized_repo.mkdir(parents=True)
            initialized_config.parent.mkdir(parents=True, exist_ok=True)
            initialized_config.write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Initialized"\n\n'
                    '[paths]\nworking_dir = "repo"\n'
                ),
                encoding="utf-8",
            )
            workspace_only.mkdir()
            legacy_setup.parent.mkdir(parents=True)
            legacy_setup.write_text("echo should-not-run\n", encoding="utf-8")

            env = _subprocess_env()
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [sys.executable, "-m", "taurworks.cli", "projects"]
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("- Initialized      initialized", result.stdout)
        self.assertIn("- WorkspaceOnly    workspace-only", result.stdout)
        self.assertIn("- LegacyAdmin      legacy-admin", result.stdout)

    def test_projects_details_include_activation_paths_and_legacy_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            initialized = workspace / "Initialized"
            initialized_repo = initialized / "repo"
            initialized_config = initialized / ".taurworks" / "config.toml"
            legacy_admin = workspace / "LegacyAdmin"
            legacy_setup = legacy_admin / "Admin" / "project-setup.source"

            initialized_repo.mkdir(parents=True)
            initialized_config.parent.mkdir(parents=True, exist_ok=True)
            initialized_config.write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Initialized"\n\n'
                    '[paths]\nworking_dir = "repo"\n'
                ),
                encoding="utf-8",
            )
            legacy_setup.parent.mkdir(parents=True)
            legacy_setup.write_text("echo should-not-run\n", encoding="utf-8")

            env = _subprocess_env()
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [sys.executable, "-m", "taurworks.cli", "projects", "--details"]
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("Status: initialized", result.stdout)
        assert_same_path(self, _project_detail_path(result.stdout, "Path"), initialized)
        assert_same_path(
            self, _project_detail_path(result.stdout, "Config"), initialized_config
        )
        self.assertIn("Activation Eligible: ✔", result.stdout)
        self.assertIn("Working Dir: repo", result.stdout)
        assert_same_path(
            self,
            _project_detail_path(result.stdout, "Resolved Working Dir"),
            initialized_repo,
        )
        self.assertIn("Status: legacy-admin", result.stdout)
        self.assertIn("not sourced by `tw activate`", result.stdout)

    def test_projects_details_reports_missing_working_dir_as_not_eligible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            project_dir = workspace / "MissingWorkdir"
            config_path = project_dir / ".taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "MissingWorkdir"\n\n'
                    '[paths]\nworking_dir = "missing"\n'
                ),
                encoding="utf-8",
            )

            env = _subprocess_env()
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [sys.executable, "-m", "taurworks.cli", "projects", "--details"]
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertIn("Status: initialized", result.stdout)
        self.assertIn("Activation Eligible: ✘", result.stdout)
        self.assertIn("Working Dir: missing", result.stdout)
        self.assertIn("Working Dir Exists: False", result.stdout)
        self.assertIn("missing on disk", result.stdout)

    def test_compat_activate_explains_non_initialized_project_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            (workspace / "WorkspaceOnly").mkdir()

            env = _subprocess_env()
            env["TAURWORKS_WORKSPACE"] = str(workspace)
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "activate",
                "WorkspaceOnly",
            ]
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=env,
            )

        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 1, msg=failure_message)
        self.assertIn("listed as workspace-only", result.stdout)
        self.assertIn("taurworks project init", result.stdout)
        self.assertNotIn("migrate the legacy setup", result.stdout)


class ProjectRegistryCliTest(unittest.TestCase):

    def test_project_register_list_and_unregister_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            config_home = root_path / "xdg"
            project_root = root_path / "hidden-project"
            project_root.mkdir()
            env = {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root_path)}
            register = _run_cli(
                ["project", "register", "HiddenProject", str(project_root)],
                root_path,
                env,
            )
            list_before = _run_cli(["project", "registry", "list"], root_path, env)
            unregister = _run_cli(
                ["project", "unregister", "HiddenProject"],
                root_path,
                env,
            )
            list_after = _run_cli(["project", "registry", "list"], root_path, env)
            config = tomllib.loads(
                (config_home / "taurworks" / "config.toml").read_text(encoding="utf-8")
            )

        register_message = _failure_message(
            ["project", "register", "HiddenProject", str(project_root)], register
        )
        self.assertEqual(register.returncode, 0, msg=register_message)
        self.assertIn("Taurworks project register", register.stdout)
        self.assertIn("name: HiddenProject", register.stdout)
        register_fields = parse_cli_fields(register.stdout)
        assert_same_path(
            self, register_fields["project_root"], project_root, msg=register_message
        )
        self.assertIn("project_config_exists: False", register.stdout)
        self.assertIn("project-local config not found", register.stdout)

        list_before_message = _failure_message(
            ["project", "registry", "list"], list_before
        )
        self.assertEqual(list_before.returncode, 0, msg=list_before_message)
        self.assertIn("Taurworks project registry", list_before.stdout)
        self.assertIn("project_count: 1", list_before.stdout)
        self.assertIn("name: HiddenProject", list_before.stdout)
        list_before_fields = parse_cli_fields(list_before.stdout)
        assert_same_path(
            self, list_before_fields["root"], project_root, msg=list_before_message
        )
        self.assertIn("path_exists: True", list_before.stdout)
        self.assertIn("project_config_exists: False", list_before.stdout)
        self.assertNotIn("collision_policy", list_before.stdout)
        self.assertIn("mutation_performed: False", list_before.stdout)

        unregister_message = _failure_message(
            ["project", "unregister", "HiddenProject"], unregister
        )
        self.assertEqual(unregister.returncode, 0, msg=unregister_message)
        self.assertIn("Taurworks project unregister", unregister.stdout)
        self.assertIn("project_files_deleted: False", unregister.stdout)
        self.assertNotIn("projects", config)

        list_after_message = _failure_message(
            ["project", "registry", "list"], list_after
        )
        self.assertEqual(list_after.returncode, 0, msg=list_after_message)
        self.assertIn("project_count: 0", list_after.stdout)
        self.assertIn("projects: none", list_after.stdout)

    def test_project_register_duplicate_name_fails_without_force(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            config_home = root_path / "xdg"
            first_project = root_path / "first"
            second_project = root_path / "second"
            first_project.mkdir()
            second_project.mkdir()
            env = {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root_path)}
            first = _run_cli(
                ["project", "register", "HiddenProject", str(first_project)],
                root_path,
                env,
            )
            duplicate = _run_cli(
                ["project", "register", "HiddenProject", str(second_project)],
                root_path,
                env,
            )
            forced = _run_cli(
                [
                    "project",
                    "register",
                    "HiddenProject",
                    str(second_project),
                    "--force",
                ],
                root_path,
                env,
            )

        first_message = _failure_message(
            ["project", "register", "HiddenProject", str(first_project)], first
        )
        self.assertEqual(first.returncode, 0, msg=first_message)
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("already registered", duplicate.stdout)
        self.assertIn("--force", duplicate.stdout)
        duplicate_fields = parse_cli_fields(duplicate.stdout)
        assert_same_path(
            self,
            duplicate_fields["config_path"],
            config_home / "taurworks" / "config.toml",
        )
        forced_message = _failure_message(
            ["project", "register", "HiddenProject", str(second_project), "--force"],
            forced,
        )
        self.assertEqual(forced.returncode, 0, msg=forced_message)
        self.assertIn("overwrote_existing: True", forced.stdout)

    def test_project_register_missing_path_requires_allow_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            config_home = root_path / "xdg"
            missing_project = root_path / "missing"
            env = {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root_path)}
            rejected = _run_cli(
                ["project", "register", "MissingProject", str(missing_project)],
                root_path,
                env,
            )
            allowed = _run_cli(
                [
                    "project",
                    "register",
                    "MissingProject",
                    str(missing_project),
                    "--allow-missing",
                ],
                root_path,
                env,
            )

        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("--allow-missing", rejected.stdout)
        allowed_message = _failure_message(
            [
                "project",
                "register",
                "MissingProject",
                str(missing_project),
                "--allow-missing",
            ],
            allowed,
        )
        self.assertEqual(allowed.returncode, 0, msg=allowed_message)
        self.assertIn("path_exists: False", allowed.stdout)
        self.assertIn("registered path does not currently exist", allowed.stdout)
        self.assertNotIn("project-local config not found", allowed.stdout)


if __name__ == "__main__":
    unittest.main()
