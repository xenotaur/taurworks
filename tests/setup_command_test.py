import os
import pathlib
import shlex
import tempfile
import unittest
from unittest import mock

from helpers import assert_same_path

from taurworks import setup_command


class ResolveShellHelperPathTest(unittest.TestCase):

    def test_prefers_taurworks_shell_helper_path_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            override = pathlib.Path(temp_dir) / "custom" / "helper.sh"
            env = {
                "TAURWORKS_SHELL_HELPER_PATH": str(override),
                "XDG_CONFIG_HOME": str(pathlib.Path(temp_dir) / "xdg"),
                "HOME": str(pathlib.Path(temp_dir) / "home"),
            }
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = setup_command.resolve_shell_helper_path()
        assert_same_path(self, resolved.path, override)
        self.assertEqual("TAURWORKS_SHELL_HELPER_PATH", resolved.source)

    def test_uses_valid_absolute_xdg_config_home_when_no_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xdg = pathlib.Path(temp_dir) / "xdg"
            env = {
                "XDG_CONFIG_HOME": str(xdg),
                "HOME": str(pathlib.Path(temp_dir) / "home"),
            }
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = setup_command.resolve_shell_helper_path()
        assert_same_path(self, resolved.path, xdg / "taurworks" / "taurworks-shell.sh")
        self.assertEqual("XDG_CONFIG_HOME", resolved.source)

    def test_ignores_relative_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"XDG_CONFIG_HOME": "relative/xdg", "HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = setup_command.resolve_shell_helper_path()
        assert_same_path(
            self,
            resolved.path,
            pathlib.Path(temp_dir) / ".config" / "taurworks" / "taurworks-shell.sh",
        )
        self.assertEqual("default fallback", resolved.source)

    def test_rejects_tilde_prefixed_xdg_config_home(self):
        # A tilde-prefixed value is relative from the shell's perspective
        # (bash's `case "$XDG_CONFIG_HOME" in /*)` never expands it), so
        # Python must reject it the same way -- expanding it here first
        # would silently disagree with `_tw_shell_refresh`'s resolution.
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"XDG_CONFIG_HOME": "~/.xdg", "HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = setup_command.resolve_shell_helper_path()
        assert_same_path(
            self,
            resolved.path,
            pathlib.Path(temp_dir) / ".config" / "taurworks" / "taurworks-shell.sh",
        )
        self.assertEqual("default fallback", resolved.source)

    def test_canonicalizes_relative_taurworks_shell_helper_path_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = pathlib.Path(temp_dir) / "cwd"
            cwd.mkdir()
            env = {"TAURWORKS_SHELL_HELPER_PATH": "custom/helper.sh"}
            old_cwd = pathlib.Path.cwd()
            os.chdir(cwd)
            try:
                with mock.patch.dict(os.environ, env, clear=True):
                    resolved = setup_command.resolve_shell_helper_path()
            finally:
                os.chdir(old_cwd)
        assert_same_path(self, resolved.path, cwd / "custom" / "helper.sh")
        self.assertEqual("TAURWORKS_SHELL_HELPER_PATH", resolved.source)

    def test_falls_back_to_home_config_when_nothing_set(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = setup_command.resolve_shell_helper_path()
        assert_same_path(
            self,
            resolved.path,
            pathlib.Path(temp_dir) / ".config" / "taurworks" / "taurworks-shell.sh",
        )
        self.assertEqual("default fallback", resolved.source)


class ResolveTlSourcePathTest(unittest.TestCase):

    def test_tl_source_lives_alongside_shell_helper(self):
        shell_helper_path = pathlib.Path("/some/config/dir/taurworks-shell.sh")
        tl_source_path = setup_command.resolve_tl_source_path(shell_helper_path)
        self.assertEqual(tl_source_path, pathlib.Path("/some/config/dir/tl.source"))


class GatherSetupDiagnosticsTest(unittest.TestCase):

    def test_first_run_creates_both_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                diagnostics = setup_command.gather_setup_diagnostics()

            shell_helper_exists = pathlib.Path(
                diagnostics["shell_helper_path"]
            ).exists()
            tl_source_exists = pathlib.Path(diagnostics["tl_source_path"]).exists()

        self.assertTrue(diagnostics["changed"])
        self.assertEqual(len(diagnostics["created"]), 2)
        self.assertEqual(diagnostics["updated"], [])
        self.assertEqual(diagnostics["unchanged"], [])
        self.assertTrue(shell_helper_exists)
        self.assertTrue(tl_source_exists)

    def test_second_run_is_idempotent_and_reports_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                first = setup_command.gather_setup_diagnostics()
                second = setup_command.gather_setup_diagnostics()

        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(second["created"], [])
        self.assertEqual(second["updated"], [])
        self.assertEqual(len(second["unchanged"]), 2)

    def test_source_lines_reference_resolved_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                diagnostics = setup_command.gather_setup_diagnostics()

        self.assertEqual(
            diagnostics["source_lines"],
            [
                f"source {shlex.quote(diagnostics['shell_helper_path'])}",
                f"source {shlex.quote(diagnostics['tl_source_path'])}",
            ],
        )

    def test_source_lines_are_shell_quoted_for_paths_with_spaces(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = pathlib.Path(temp_dir) / "My Home"
            home.mkdir()
            env = {"HOME": str(home)}
            with mock.patch.dict(os.environ, env, clear=True):
                diagnostics = setup_command.gather_setup_diagnostics()

        for line in diagnostics["source_lines"]:
            self.assertNotIn(
                " .config", line, msg=f"unquoted space-containing path in: {line!r}"
            )
        shell_helper_path = diagnostics["shell_helper_path"]
        expected_line = f"source {shlex.quote(shell_helper_path)}"
        self.assertIn(expected_line, diagnostics["source_lines"])
        # A quoted path is re-parseable as a single shell word even though
        # it contains a space.
        (parsed,) = shlex.split(expected_line)[1:]
        self.assertEqual(parsed, shell_helper_path)

    def test_written_content_matches_packaged_resources(self):
        from taurworks import shell_resources

        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                diagnostics = setup_command.gather_setup_diagnostics()

            shell_helper_content = pathlib.Path(
                diagnostics["shell_helper_path"]
            ).read_text(encoding="utf-8")
            tl_source_content = pathlib.Path(diagnostics["tl_source_path"]).read_text(
                encoding="utf-8"
            )

        self.assertEqual(shell_helper_content, shell_resources.read_shell_helper_text())
        self.assertEqual(tl_source_content, shell_resources.read_tl_source_text())


class FormatSetupOutputTest(unittest.TestCase):

    def test_no_changes_needed_result_line(self):
        diagnostics = {
            "shell_helper_path": "/x/taurworks-shell.sh",
            "shell_helper_path_source": "default fallback",
            "tl_source_path": "/x/tl.source",
            "created": [],
            "updated": [],
            "unchanged": [
                "shell helper: /x/taurworks-shell.sh",
                "tl source: /x/tl.source",
            ],
            "warnings": [],
            "changed": False,
            "source_lines": ["source /x/taurworks-shell.sh", "source /x/tl.source"],
        }
        output = setup_command.format_setup_output(diagnostics)
        self.assertIn("- result: no changes needed", output)
        self.assertIn("source /x/taurworks-shell.sh", output)
        self.assertIn("source /x/tl.source", output)

    def test_created_entries_listed(self):
        diagnostics = {
            "shell_helper_path": "/x/taurworks-shell.sh",
            "shell_helper_path_source": "default fallback",
            "tl_source_path": "/x/tl.source",
            "created": [
                "shell helper: /x/taurworks-shell.sh",
                "tl source: /x/tl.source",
            ],
            "updated": [],
            "unchanged": [],
            "warnings": [],
            "changed": True,
            "source_lines": ["source /x/taurworks-shell.sh", "source /x/tl.source"],
        }
        output = setup_command.format_setup_output(diagnostics)
        self.assertIn("- created:", output)
        self.assertIn("  - shell helper: /x/taurworks-shell.sh", output)
        self.assertNotIn("- result: no changes needed", output)


if __name__ == "__main__":
    unittest.main()
