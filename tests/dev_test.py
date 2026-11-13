import os
import pathlib
import stat
import tempfile
import unittest
from unittest import mock

from taurworks import dev
from taurworks import project_internals


def _write_project_config(project_root: pathlib.Path, body: str) -> None:
    admin_dir = project_root / ".taurworks"
    admin_dir.mkdir(parents=True, exist_ok=True)
    (admin_dir / "config.toml").write_text(body, encoding="utf-8")


def _write_executable_script(path: pathlib.Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class ResolveDevCommandTest(unittest.TestCase):
    def _chdir(self, target: pathlib.Path):
        original_cwd = pathlib.Path.cwd()
        os.chdir(target)
        self.addCleanup(os.chdir, original_cwd)

    def test_tier1_resolution_from_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            _write_project_config(
                project_root,
                'schema_version = 1\n\n[dev.commands]\ntest = "pytest -x"\n',
            )
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertTrue(resolution.resolved)
        self.assertEqual(resolution.tier, "config")
        self.assertEqual(resolution.argv, ["pytest", "-x"])

    def test_tier2_resolution_from_project_local_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            (project_root / ".taurworks").mkdir()
            script_path = project_root / "scripts" / "test"
            _write_executable_script(script_path, "#!/bin/sh\nexit 0\n")
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertTrue(resolution.resolved)
        self.assertEqual(resolution.tier, "script")
        self.assertEqual(resolution.argv, [str(script_path.resolve())])

    def test_tier1_takes_precedence_over_tier2(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            _write_project_config(
                project_root,
                'schema_version = 1\n\n[dev.commands]\ntest = "pytest -x"\n',
            )
            _write_executable_script(
                project_root / "scripts" / "test", "#!/bin/sh\nexit 0\n"
            )
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertEqual(resolution.tier, "config")
        self.assertEqual(resolution.argv, ["pytest", "-x"])

    def test_neither_tier_resolves_fails_clearly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            (project_root / ".taurworks").mkdir()
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertFalse(resolution.resolved)
        self.assertIsNone(resolution.argv)
        self.assertIn("test", resolution.detail)
        self.assertIn("[dev.commands].test", resolution.detail)
        self.assertIn("scripts", resolution.detail)

    def test_unexecutable_tier2_script_fails_clearly_not_silently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            (project_root / ".taurworks").mkdir()
            script_path = project_root / "scripts" / "test"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            # Deliberately not made executable.
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertFalse(resolution.resolved)
        self.assertIn("not executable", resolution.detail)

    def test_malformed_config_fails_clearly_instead_of_falling_through_to_tier2(
        self,
    ):
        # Regression test (review): a malformed [dev.commands] table must
        # stop resolution with a clear error, not silently fall through to
        # Tier 2 -- a config typo could otherwise run a different,
        # unintended script without ever surfacing the typo.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            _write_project_config(
                project_root,
                'schema_version = 1\n\n[dev]\ncommands = "not-a-table"\n',
            )
            _write_executable_script(
                project_root / "scripts" / "test", "#!/bin/sh\nexit 0\n"
            )
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertFalse(resolution.resolved)
        self.assertIsNone(resolution.argv)
        self.assertIn("could not be read", resolution.detail)

    def test_unparseable_configured_command_fails_clearly(self):
        # Regression test (review): shlex.split can raise ValueError on
        # malformed shell quoting; this must produce a clear resolution
        # failure, not an unhandled traceback.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            _write_project_config(
                project_root,
                'schema_version = 1\n\n[dev.commands]\ntest = "pytest \\"unterminated"\n',
            )
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertFalse(resolution.resolved)
        self.assertIsNone(resolution.argv)
        self.assertIn("could not be parsed", resolution.detail)

    def test_tier1_config_resolves_from_project_root_with_nested_working_dir(self):
        # Regression test (WI-DEV-WORKFLOW-AUTOMATION-0001 review): Tier 1
        # config must be read from project_root, not work_directory_guess,
        # since .taurworks/config.toml is metadata owned by project_root
        # and a nested working_dir would otherwise hide it entirely.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            repo_dir = project_root / "repo"
            repo_dir.mkdir(parents=True)
            _write_project_config(
                project_root,
                'schema_version = 1\n\n[paths]\nworking_dir = "repo"\n\n'
                '[dev.commands]\ntest = "pytest -x"\n',
            )
            self._chdir(repo_dir)

            resolution = dev.resolve_dev_command("test")

        self.assertTrue(resolution.resolved)
        self.assertEqual(resolution.tier, "config")
        self.assertEqual(resolution.argv, ["pytest", "-x"])
        self.assertEqual(pathlib.Path(resolution.cwd), repo_dir.resolve())

    def test_tier2_script_and_cwd_resolve_from_work_directory_guess(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            repo_dir = project_root / "repo"
            _write_project_config(
                project_root,
                'schema_version = 1\n\n[paths]\nworking_dir = "repo"\n',
            )
            _write_executable_script(
                repo_dir / "scripts" / "test", "#!/bin/sh\nexit 0\n"
            )
            self._chdir(project_root)

            resolution = dev.resolve_dev_command("test")

        self.assertTrue(resolution.resolved)
        self.assertEqual(resolution.tier, "script")
        self.assertEqual(pathlib.Path(resolution.cwd), repo_dir.resolve())


class AmbiguousDiscoveryDevTest(unittest.TestCase):
    """An ambiguous working_dir reverse lookup never yields a guessed work dir."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.cwd = pathlib.Path(self._temp.name).resolve()
        original_cwd = pathlib.Path.cwd()
        os.chdir(self.cwd)
        self.addCleanup(os.chdir, original_cwd)
        (self.cwd / ".git").mkdir()
        _write_executable_script(self.cwd / "scripts" / "test", "#!/bin/sh\n")
        self.candidates = (self.cwd.parent / "A", self.cwd.parent / "B")
        ambiguous = project_internals.PathDiscovery(
            root=None,
            source=project_internals.DiscoverySource.WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS,
            candidates=self.candidates,
        )
        patcher = mock.patch.object(
            dev.manager, "find_project_root_for_path", return_value=ambiguous
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_dev_where_reports_ambiguity_without_guessing(self):
        diagnostics = dev.gather_dev_where_diagnostics()
        self.assertFalse(diagnostics["ok"])
        self.assertEqual("unresolved", diagnostics["work_directory_guess"])
        self.assertEqual("unresolved", diagnostics["git_root_guess"])
        self.assertEqual(
            "working_dir_reverse_lookup_ambiguous", diagnostics["resolved_by"]
        )
        self.assertIn(str(self.candidates[0]), diagnostics["working_dir_message"])

    def test_resolve_dev_command_refuses_script_fallback(self):
        resolution = dev.resolve_dev_command("test")
        self.assertFalse(resolution.resolved)
        self.assertIsNone(resolution.argv)
        self.assertIn("rerun from the chosen project_root", resolution.detail)


class LinkedWorktreeDetectionTest(unittest.TestCase):
    """`_is_linked_worktree` reads the `.git` file without running git."""

    def check(self, git_entry: str | None, expected: bool, as_dir: bool = False):
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout = pathlib.Path(temp_dir)
            if as_dir:
                (checkout / ".git").mkdir()
            elif git_entry is not None:
                (checkout / ".git").write_text(git_entry, encoding="utf-8")
            self.assertIs(expected, dev._is_linked_worktree(checkout))

    def test_absolute_worktree_gitdir(self):
        self.check("gitdir: /repo/.git/worktrees/feature\n", True)

    def test_relative_worktree_gitdir_with_trailing_slash(self):
        self.check("gitdir: ../.git/worktrees/feature/\n", True)

    def test_worktree_of_a_submodule(self):
        self.check("gitdir: /repo/.git/modules/lib/worktrees/x\n", True)

    def test_submodule_is_not_a_worktree(self):
        self.check("gitdir: ../../.git/modules/lib\n", False)

    def test_git_directory_is_not_a_worktree(self):
        self.check(None, False, as_dir=True)

    def test_missing_empty_or_malformed_git_file(self):
        self.check(None, False)
        self.check("", False)
        self.check("worktrees/feature\n", False)


class ExecuteDevCommandTest(unittest.TestCase):
    def test_exit_code_passthrough(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            script_path = project_root / "scripts" / "test"
            _write_executable_script(script_path, "#!/bin/sh\nexit 7\n")

            resolution = dev.DevCommandResolution(
                resolved=True,
                argv=[str(script_path)],
                cwd=str(project_root),
                tier="script",
                detail=str(script_path),
            )
            exit_code = dev.execute_dev_command(resolution)

        self.assertEqual(exit_code, 7)

    def test_subprocess_runs_with_resolved_cwd(self):
        # Regression test (WI-DEV-WORKFLOW-AUTOMATION-0001 review): the
        # delegated subprocess must run with cwd set to the resolved base
        # directory, not whatever directory the invoking process happens
        # to be in.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            work_dir = project_root / "work"
            work_dir.mkdir()
            cwd_report_path = project_root / "cwd_report.txt"
            script_path = project_root / "scripts" / "test"
            _write_executable_script(
                script_path,
                "#!/bin/sh\n" f'pwd > "{cwd_report_path}"\n' "exit 0\n",
            )

            resolution = dev.DevCommandResolution(
                resolved=True,
                argv=[str(script_path)],
                cwd=str(work_dir),
                tier="script",
                detail=str(script_path),
            )
            original_cwd = pathlib.Path.cwd()
            os.chdir(project_root)
            try:
                exit_code = dev.execute_dev_command(resolution)
            finally:
                os.chdir(original_cwd)

            reported_cwd = cwd_report_path.read_text(encoding="utf-8").strip()

        self.assertEqual(exit_code, 0)
        self.assertEqual(pathlib.Path(reported_cwd), work_dir.resolve())

    def test_missing_executable_raises_oserror_not_silently_swallowed(self):
        # Regression test (review): a resolved argv whose executable
        # cannot actually be launched (missing binary, bad interpreter,
        # permission error, vanished cwd) must raise OSError so the CLI
        # layer can report a clean failure -- execute_dev_command itself
        # must not swallow or convert it.
        with tempfile.TemporaryDirectory() as temp_dir:
            resolution = dev.DevCommandResolution(
                resolved=True,
                argv=[str(pathlib.Path(temp_dir) / "does-not-exist")],
                cwd=temp_dir,
                tier="script",
                detail="does-not-exist",
            )
            with self.assertRaises(OSError):
                dev.execute_dev_command(resolution)


class DevCommandFromConfigTest(unittest.TestCase):
    def test_returns_none_when_no_dev_table(self):
        self.assertIsNone(project_internals.dev_command_from_config({}, "test"))

    def test_returns_none_when_command_not_configured(self):
        config = {"dev": {"commands": {"lint": "ruff check"}}}
        self.assertIsNone(project_internals.dev_command_from_config(config, "test"))

    def test_returns_configured_command(self):
        config = {"dev": {"commands": {"test": "pytest -x"}}}
        self.assertEqual(
            project_internals.dev_command_from_config(config, "test"), "pytest -x"
        )

    def test_rejects_non_table_dev_value(self):
        with self.assertRaises(project_internals.ProjectConfigError):
            project_internals.dev_command_from_config({"dev": "nope"}, "test")

    def test_rejects_non_table_commands_value(self):
        with self.assertRaises(project_internals.ProjectConfigError):
            project_internals.dev_command_from_config(
                {"dev": {"commands": "nope"}}, "test"
            )

    def test_rejects_non_string_command_value(self):
        with self.assertRaises(project_internals.ProjectConfigError):
            project_internals.dev_command_from_config(
                {"dev": {"commands": {"test": 123}}}, "test"
            )
