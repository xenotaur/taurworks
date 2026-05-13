import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest


def _subprocess_env() -> dict[str, str]:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
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
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
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
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        failure_message = f"Command failed: {cmd}\nreturn code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=failure_message)
        self.assertEqual("created-with-working-dir", config["project"]["name"])
        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertFalse((target_dir / "repo").exists(), msg=failure_message)
        self.assertIn("working_dir: repo", result.stdout, msg=failure_message)
        self.assertIn("working_dir_exists: False", result.stdout, msg=failure_message)
        self.assertIn("working_dir_created: False", result.stdout, msg=failure_message)

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
            file_text = existing_file.read_text(encoding="utf-8")
            config = tomllib.loads(
                (target_dir / ".taurworks" / "config.toml").read_text(encoding="utf-8")
            )
        first_message = f"First command failed: {cmd}\nreturn code: {first.returncode}\nstdout:\n{first.stdout}\nstderr:\n{first.stderr}"
        second_message = f"Second command failed: {cmd}\nreturn code: {second.returncode}\nstdout:\n{second.stdout}\nstderr:\n{second.stderr}"
        self.assertEqual(first.returncode, 0, msg=first_message)
        self.assertEqual(second.returncode, 0, msg=second_message)
        self.assertEqual("keep me", file_text)
        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertIn("changed: True", first.stdout, msg=first_message)
        self.assertIn("changed: False", second.stdout, msg=second_message)
        self.assertFalse((target_dir / "repo").exists(), msg=second_message)

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

    def test_project_activate_print_reports_read_only_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = pathlib.Path(temp_dir)
            target_dir = root_path / "project-a"
            (target_dir / ".taurworks").mkdir(parents=True)
            (target_dir / ".taurworks" / "config.toml").write_text(
                '[project]\nname = "project-a"\n', encoding="utf-8"
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
        self.assertIn(
            "shell_mutation: not performed", result.stdout, msg=failure_message
        )
        self.assertIn("activation_command:", result.stdout, msg=failure_message)
        self.assertEqual(files_before, files_after, msg=failure_message)

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
            cmd = [
                sys.executable,
                "-m",
                "taurworks.cli",
                "project",
                "activate",
                "child-project",
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
        resolved_project_prefix = "- resolved_project: "
        resolved_project_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith(resolved_project_prefix)
        ]
        self.assertEqual(len(resolved_project_lines), 1, msg=failure_message)

        resolved_project = pathlib.Path(
            resolved_project_lines[0].removeprefix(resolved_project_prefix)
        )
        self.assertEqual(
            (parent_project / "child-project").resolve(),
            resolved_project.resolve(),
            msg=failure_message,
        )
        self.assertEqual("child-project", resolved_project.name, msg=failure_message)
        self.assertIn("activation_command: none", result.stdout, msg=failure_message)


if __name__ == "__main__":
    unittest.main()
