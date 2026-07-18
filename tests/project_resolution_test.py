import hashlib
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from helpers import assert_same_path

from taurworks import global_config
from taurworks import project_resolution


class ProjectResolutionModuleTest(unittest.TestCase):
    def test_gather_project_where_diagnostics_structure(self):
        diagnostics = project_resolution.gather_project_where_diagnostics()
        self.assertIn("cwd", diagnostics)
        self.assertIn("project_root_candidate", diagnostics)
        self.assertIn("config_path", diagnostics)

    def test_format_project_list_output_includes_project_count(self):
        diagnostics = {
            "cwd": "/tmp",
            "discovery_source": "none",
            "project_count": 0,
            "projects": [],
            "limitations": "test",
        }
        rendered = project_resolution.format_project_list_output(diagnostics)
        self.assertIn("project_count: 0", rendered)
        self.assertIn("projects: none", rendered)

    def test_resolve_project_refresh_target_keeps_name_as_child_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = pathlib.Path(temp_dir)
            project_dir = root_dir / "TestProject"
            (project_dir / ".taurworks").mkdir(parents=True)
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "TestProject"\n',
                encoding="utf-8",
            )
            original = pathlib.Path.cwd()
            try:
                __import__("os").chdir(project_dir)
                resolved = project_resolution.resolve_project_refresh_target(
                    "TestProject"
                )
            finally:
                __import__("os").chdir(original)
        assert_same_path(self, resolved, project_dir / "TestProject")

    def test_resolve_project_refresh_target_defaults_to_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = pathlib.Path(temp_dir)
            original = pathlib.Path.cwd()
            try:
                __import__("os").chdir(cwd)
                resolved = project_resolution.resolve_project_refresh_target(None)
            finally:
                __import__("os").chdir(original)
        assert_same_path(self, resolved, cwd)


class GlobalActivationResolutionTest(unittest.TestCase):
    def _write_project_config(
        self,
        project_root: pathlib.Path,
        name: str,
        working_dir: str | None = None,
    ) -> None:
        config_dir = project_root / ".taurworks"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_text = f'schema_version = 1\n\n[project]\nname = "{name}"\n'
        if working_dir is not None:
            config_text += f'\n[paths]\nworking_dir = "{working_dir}"\n'
        (config_dir / "config.toml").write_text(config_text, encoding="utf-8")

    def _with_global_config(
        self, temp_path: pathlib.Path, workspace: pathlib.Path
    ) -> pathlib.Path:
        xdg_home = temp_path / "xdg"
        config_path = xdg_home / "taurworks" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
            encoding="utf-8",
        )
        return xdg_home

    def test_current_project_fallback_uses_configured_project_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "folder-name"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            self._write_project_config(project_root, "ConfiguredName", "repo")

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "ConfiguredName"
                    )
                )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"])
        assert_same_path(self, diagnostics["project_root"], project_root)
        assert_same_path(self, diagnostics["resolved_working_dir"], repo)
        self.assertEqual(diagnostics["resolved_by"], "current_project_name")

    def test_activate_workspace_project_from_outside_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            outside = temp_path / "outside"
            project_root = workspace / "WorkspaceProject"
            working_dir = project_root / "repo"
            working_dir.mkdir(parents=True)
            outside.mkdir()
            self._write_project_config(project_root, "WorkspaceProject", "repo")
            xdg_home = self._with_global_config(temp_path, workspace)

            original_cwd = pathlib.Path.cwd()
            try:
                with mock.patch.dict(
                    os.environ,
                    {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
                ):
                    os.chdir(outside)
                    diagnostics = (
                        project_resolution.gather_project_activate_print_diagnostics(
                            "WorkspaceProject"
                        )
                    )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"])
        assert_same_path(self, diagnostics["resolved_working_dir"], working_dir)
        self.assertEqual(diagnostics["resolved_by"], "workspace_initialized_project")

    def test_activate_workspace_project_after_other_project_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            first_root = workspace / "FirstProject"
            first_repo = first_root / "repo"
            second_root = workspace / "SecondProject"
            second_repo = second_root / "repo"
            first_repo.mkdir(parents=True)
            second_repo.mkdir(parents=True)
            self._write_project_config(first_root, "FirstProject", "repo")
            self._write_project_config(second_root, "SecondProject", "repo")
            xdg_home = self._with_global_config(temp_path, workspace)

            original_cwd = pathlib.Path.cwd()
            try:
                with mock.patch.dict(
                    os.environ,
                    {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
                ):
                    os.chdir(first_repo)
                    diagnostics = (
                        project_resolution.gather_project_activate_print_diagnostics(
                            "SecondProject"
                        )
                    )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"])
        assert_same_path(self, diagnostics["resolved_working_dir"], second_repo)
        assert_same_path(self, diagnostics["project_root"], second_root)

    def test_activation_message_and_exports_are_reported_without_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            config_dir = project_root / ".taurworks"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Project"\n\n'
                    '[paths]\nworking_dir = "repo"\n\n'
                    '[activation]\nmessage = "Ready for work"\n\n'
                    "[activation.exports]\n"
                    'NODE_OPTIONS = "--max-old-space-size=8192"\n'
                    'SECRET_TOKEN = "do-not-print"\n'
                ),
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
                rendered = project_resolution.format_project_activate_print_output(
                    diagnostics
                )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"])
        self.assertTrue(diagnostics["activation_message_configured"])
        self.assertTrue(diagnostics["activation_exports_configured"])
        self.assertEqual(diagnostics["activation_export_count"], 2)
        self.assertIn("activation_export_names: NODE_OPTIONS,SECRET_TOKEN", rendered)
        self.assertIn("activation_export_values: hidden", rendered)
        self.assertNotIn("do-not-print", rendered)
        self.assertNotIn("--max-old-space-size=8192", rendered)

    def test_invalid_activation_export_name_fails_before_shell_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            config_dir = project_root / ".taurworks"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Project"\n\n'
                    '[paths]\nworking_dir = "repo"\n\n'
                    "[activation.exports]\n"
                    '"BAD-NAME" = "value"\n'
                ),
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
                rendered = project_resolution.format_project_activate_shell_output(
                    diagnostics
                )
            finally:
                os.chdir(original_cwd)

        self.assertFalse(diagnostics["ok"])
        self.assertIn("invalid activation export name", diagnostics["guidance"])
        self.assertNotIn("export BAD-NAME", rendered)

    def test_activation_environment_conda_is_reported_read_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            config_dir = project_root / ".taurworks"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Project"\n\n'
                    '[paths]\nworking_dir = "repo"\n\n'
                    "[activation.environment]\n"
                    'type = "conda"\n'
                    'name = "LCATS"\n'
                ),
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
                rendered = project_resolution.format_project_activate_print_output(
                    diagnostics
                )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"])
        self.assertTrue(diagnostics["environment_configured"])
        self.assertEqual(diagnostics["environment_type"], "conda")
        self.assertEqual(diagnostics["environment_name"], "LCATS")
        self.assertIn("environment_configured: True", rendered)
        self.assertIn("environment_type: conda", rendered)
        self.assertIn("environment_name: LCATS", rendered)
        self.assertIn("environment_activation: not performed", rendered)

    def test_unsupported_activation_environment_type_fails_clearly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            config_dir = project_root / ".taurworks"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Project"\n\n'
                    '[paths]\nworking_dir = "repo"\n\n'
                    "[activation.environment]\n"
                    'type = "venv"\n'
                    'name = "Env"\n'
                ),
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
            finally:
                os.chdir(original_cwd)

        self.assertFalse(diagnostics["ok"])
        self.assertIn(
            "unsupported activation environment type", diagnostics["guidance"]
        )
        self.assertIn("only 'conda' is supported", diagnostics["guidance"])

    def test_conda_activation_environment_requires_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            config_dir = project_root / ".taurworks"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Project"\n\n'
                    '[paths]\nworking_dir = "repo"\n\n'
                    "[activation.environment]\n"
                    'type = "conda"\n'
                ),
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
            finally:
                os.chdir(original_cwd)

        self.assertFalse(diagnostics["ok"])
        self.assertIn("activation.environment.name", diagnostics["guidance"])
        self.assertIn("required for Conda activation", diagnostics["guidance"])

    def test_conda_activation_environment_name_is_validated_conservatively(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            config_dir = project_root / ".taurworks"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Project"\n\n'
                    '[paths]\nworking_dir = "repo"\n\n'
                    "[activation.environment]\n"
                    'type = "conda"\n'
                    'name = "../unsafe"\n'
                ),
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
            finally:
                os.chdir(original_cwd)

        self.assertFalse(diagnostics["ok"])
        self.assertIn(
            "invalid Conda activation environment name", diagnostics["guidance"]
        )

    def test_workspace_only_and_legacy_admin_activate_to_root_with_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            workspace_only = workspace / "WorkspaceOnly"
            legacy = workspace / "Legacy"
            sentinel = legacy / "sourced.txt"
            workspace_only.mkdir(parents=True)
            legacy_setup = legacy / "Admin" / "project-setup.source"
            legacy_setup.parent.mkdir(parents=True)
            legacy_setup.write_text(f"touch {sentinel}\n", encoding="utf-8")
            xdg_home = self._with_global_config(temp_path, workspace)

            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
            ):
                workspace_diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "WorkspaceOnly"
                    )
                )
                legacy_diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Legacy"
                    )
                )

        self.assertTrue(workspace_diagnostics["ok"])
        assert_same_path(
            self, workspace_diagnostics["resolved_working_dir"], workspace_only
        )
        self.assertIn("not initialized", str(workspace_diagnostics["guidance"]))
        self.assertIn(
            "taurworks project init WorkspaceOnly",
            str(workspace_diagnostics["guidance"]),
        )
        self.assertTrue(legacy_diagnostics["ok"])
        assert_same_path(self, legacy_diagnostics["resolved_working_dir"], legacy)
        self.assertIn("was not sourced", str(legacy_diagnostics["guidance"]))
        self.assertIn(
            "taurworks legacy migrate Legacy --apply",
            str(legacy_diagnostics["guidance"]),
        )
        self.assertFalse(sentinel.exists())

    def test_activate_without_environment_names_env_set_in_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            project_root = temp_path / "Project"
            repo = project_root / "repo"
            repo.mkdir(parents=True)
            self._write_project_config(project_root, "Project", "repo")

            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(project_root)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Project"
                    )
                )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"])
        self.assertFalse(diagnostics["environment_configured"])
        self.assertIn("taurworks project env set", str(diagnostics["guidance"]))
        self.assertIn("--project Project", str(diagnostics["guidance"]))

    def test_registered_hidden_project_lists_and_activates_without_workspace_duplicate(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            duplicate = workspace / "Duplicate"
            hidden = temp_path / "HiddenProject"
            duplicate_repo = duplicate / "repo"
            hidden_repo = hidden / "repo"
            duplicate_repo.mkdir(parents=True)
            hidden_repo.mkdir(parents=True)
            self._write_project_config(duplicate, "Duplicate", "repo")
            self._write_project_config(hidden, "Hidden", "repo")
            xdg_home = self._with_global_config(temp_path, workspace)
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8")
                + f'\n[projects.Hidden]\nroot = "{hidden}"\n'
                + f'\n[projects.Duplicate]\nroot = "{duplicate}"\n',
                encoding="utf-8",
            )

            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
            ):
                listing = project_resolution.gather_project_list_diagnostics()
                hidden_diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Hidden"
                    )
                )

        names = [project["name"] for project in listing["projects"]]
        self.assertIn("Hidden", names)
        self.assertEqual(names.count("Duplicate"), 1)
        self.assertTrue(hidden_diagnostics["ok"])
        assert_same_path(self, hidden_diagnostics["resolved_working_dir"], hidden_repo)
        self.assertEqual(hidden_diagnostics["resolved_by"], "registered_project")

    def test_workspace_listing_does_not_scan_recursively_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            nested = workspace / "Parent" / "Nested"
            nested_repo = nested / "repo"
            nested_repo.mkdir(parents=True)
            self._write_project_config(nested, "Nested", "repo")
            xdg_home = self._with_global_config(temp_path, workspace)

            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
            ):
                listing = project_resolution.gather_project_list_diagnostics()

        names = [project["name"] for project in listing["projects"]]
        self.assertIn("Parent", names)
        self.assertNotIn("Nested", names)


class ProjectEnvDiagnosticsTest(unittest.TestCase):
    def test_env_set_resolves_registered_project_outside_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            registered_root = temp_path / "Elsewhere" / "RegisteredProject"
            outside_cwd = temp_path / "outside"
            registered_root.mkdir(parents=True)
            outside_cwd.mkdir()
            (registered_root / ".taurworks").mkdir()
            (registered_root / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "RegisteredProject"\n',
                encoding="utf-8",
            )

            xdg_home = temp_path / "xdg"
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "schema_version = 1\n\n"
                "[projects.RegisteredProject]\n"
                f'root = "{registered_root}"\n',
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                with mock.patch.dict(
                    os.environ,
                    {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
                ):
                    os.chdir(outside_cwd)
                    set_diagnostics = (
                        project_resolution.gather_project_env_set_diagnostics(
                            "RegEnv", "RegisteredProject"
                        )
                    )
                    show_diagnostics = (
                        project_resolution.gather_project_env_show_diagnostics(
                            "RegisteredProject"
                        )
                    )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(
            set_diagnostics["ok"],
            msg=f"expected registered project to resolve: {set_diagnostics}",
        )
        self.assertEqual("RegEnv", set_diagnostics["environment_name"])
        self.assertTrue(show_diagnostics["ok"])
        self.assertEqual("RegEnv", show_diagnostics["environment_name"])

    def test_env_show_reports_no_environment_configured(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            (project_dir / ".taurworks").mkdir(parents=True)
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "proj"\n',
                encoding="utf-8",
            )

            diagnostics = project_resolution.gather_project_env_show_diagnostics(
                str(project_dir)
            )

        self.assertTrue(diagnostics["ok"])
        self.assertFalse(diagnostics["environment_configured"])

    def test_env_set_then_show_round_trips_environment_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            (project_dir / ".taurworks").mkdir(parents=True)
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "proj"\n',
                encoding="utf-8",
            )

            set_diagnostics = project_resolution.gather_project_env_set_diagnostics(
                "MyEnv", str(project_dir)
            )
            show_diagnostics = project_resolution.gather_project_env_show_diagnostics(
                str(project_dir)
            )

        self.assertTrue(set_diagnostics["ok"])
        self.assertEqual("none", set_diagnostics["previous_environment"])
        self.assertEqual("MyEnv", set_diagnostics["environment_name"])
        self.assertTrue(show_diagnostics["ok"])
        self.assertTrue(show_diagnostics["environment_configured"])
        self.assertEqual("MyEnv", show_diagnostics["environment_name"])
        self.assertEqual("conda", show_diagnostics["environment_type"])

    def test_env_set_rejects_invalid_name_before_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            (project_dir / ".taurworks").mkdir(parents=True)
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "proj"\n',
                encoding="utf-8",
            )

            diagnostics = project_resolution.gather_project_env_set_diagnostics(
                "../unsafe", str(project_dir)
            )
            show_diagnostics = project_resolution.gather_project_env_show_diagnostics(
                str(project_dir)
            )

        self.assertFalse(diagnostics["ok"])
        self.assertIn(
            "invalid Conda activation environment name", diagnostics["message"]
        )
        self.assertFalse(show_diagnostics["environment_configured"])

    def test_env_set_fails_for_uninitialized_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            project_dir.mkdir(parents=True)

            diagnostics = project_resolution.gather_project_env_set_diagnostics(
                "MyEnv", str(project_dir)
            )

        self.assertFalse(diagnostics["ok"])
        self.assertIn("No Taurworks project metadata found", diagnostics["message"])


class ProjectTrustDiagnosticsTest(unittest.TestCase):
    def _write_legacy_script(
        self, project_root: pathlib.Path, text: str = "echo hi\n"
    ) -> pathlib.Path:
        admin_dir = project_root / "Admin"
        admin_dir.mkdir(parents=True, exist_ok=True)
        script = admin_dir / "project-setup.source"
        script.write_text(text, encoding="utf-8")
        return script

    def test_trust_set_computes_and_records_digest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            script = self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
                encoding="utf-8",
            )

            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
            ):
                diagnostics = project_resolution.gather_project_trust_set_diagnostics(
                    "Legacy"
                )
            expected_digest = hashlib.sha256(script.read_bytes()).hexdigest()

        self.assertTrue(diagnostics["ok"], msg=diagnostics)
        self.assertEqual("none", diagnostics["previous_digest"])
        self.assertEqual(expected_digest, diagnostics["digest"])

    def test_trust_set_fails_cleanly_when_no_legacy_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            project_dir.mkdir(parents=True)

            diagnostics = project_resolution.gather_project_trust_set_diagnostics(
                str(project_dir)
            )

        self.assertFalse(diagnostics["ok"])
        self.assertIn("nothing to trust", diagnostics["message"])

    def test_trust_set_always_overwrites_previous_digest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            script = self._write_legacy_script(project_root, "echo one\n")
            xdg_home = temp_path / "xdg"
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
                encoding="utf-8",
            )
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                first = project_resolution.gather_project_trust_set_diagnostics(
                    "Legacy"
                )
                script.write_text("echo two\n", encoding="utf-8")
                second = project_resolution.gather_project_trust_set_diagnostics(
                    "Legacy"
                )

        self.assertTrue(first["ok"] and second["ok"])
        self.assertEqual(first["digest"], second["previous_digest"])
        self.assertNotEqual(first["digest"], second["digest"])

    def test_trust_unset_removes_record_then_reports_nothing_to_do(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
                encoding="utf-8",
            )
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                project_resolution.gather_project_trust_set_diagnostics("Legacy")
                removed = project_resolution.gather_project_trust_unset_diagnostics(
                    "Legacy"
                )
                again = project_resolution.gather_project_trust_unset_diagnostics(
                    "Legacy"
                )

        self.assertTrue(removed["ok"])
        self.assertNotEqual("none", removed["removed_digest"])
        self.assertFalse(again["ok"])

    def test_trust_list_reports_stale_when_script_edited(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            script = self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
                encoding="utf-8",
            )
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                project_resolution.gather_project_trust_set_diagnostics("Legacy")
                script.write_text("echo edited\n", encoding="utf-8")
                listing = project_resolution.gather_project_trust_list_diagnostics()

        self.assertTrue(listing["ok"])
        self.assertEqual(1, listing["trust_count"])
        record = listing["records"][0]
        self.assertEqual("Legacy", record["name"])
        self.assertTrue(record["path_exists"])
        self.assertFalse(record["digest_matches"])

    def test_trust_set_resolves_registered_project_outside_cwd(self):
        # Regression guard matching the WI's motivating fix: the command
        # this feature's own prompt suggests must resolve the same way
        # `tw activate` resolves projects, not just cwd-relative.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            registered_root = temp_path / "Elsewhere" / "RegisteredLegacy"
            outside_cwd = temp_path / "outside"
            self._write_legacy_script(registered_root)
            outside_cwd.mkdir()

            xdg_home = temp_path / "xdg"
            config_path = xdg_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "schema_version = 1\n\n"
                "[projects.RegisteredLegacy]\n"
                f'root = "{registered_root}"\n',
                encoding="utf-8",
            )

            original_cwd = pathlib.Path.cwd()
            try:
                with mock.patch.dict(
                    os.environ,
                    {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
                ):
                    os.chdir(outside_cwd)
                    diagnostics = (
                        project_resolution.gather_project_trust_set_diagnostics(
                            "RegisteredLegacy"
                        )
                    )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(diagnostics["ok"], msg=diagnostics)


class LegacyTrustActivationDiagnosticsTest(unittest.TestCase):
    def _write_legacy_script(
        self, project_root: pathlib.Path, text: str = "echo hi\n"
    ) -> pathlib.Path:
        admin_dir = project_root / "Admin"
        admin_dir.mkdir(parents=True, exist_ok=True)
        script = admin_dir / "project-setup.source"
        script.write_text(text, encoding="utf-8")
        return script

    def _global_config(self, xdg_home: pathlib.Path, workspace: pathlib.Path) -> None:
        config_path = xdg_home / "taurworks" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
            encoding="utf-8",
        )

    def test_no_legacy_script_leaves_trust_fields_at_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Plain"
            project_root.mkdir(parents=True)
            xdg_home = temp_path / "xdg"
            self._global_config(xdg_home, workspace)

            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
            ):
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Plain"
                    )
                )

        self.assertFalse(diagnostics["legacy_sourcing_enabled"])
        self.assertFalse(diagnostics["legacy_trusted"])
        self.assertFalse(diagnostics["legacy_trust_stale"])

    def test_untrusted_legacy_script_reports_not_trusted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            self._global_config(xdg_home, workspace)

            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)},
            ):
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Legacy"
                    )
                )

        self.assertTrue(diagnostics["legacy_setup_exists"])
        self.assertFalse(diagnostics["legacy_trusted"])
        self.assertFalse(diagnostics["legacy_trust_stale"])

    def test_trusted_matching_digest_reports_trusted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            self._global_config(xdg_home, workspace)
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                project_resolution.gather_project_trust_set_diagnostics("Legacy")
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Legacy"
                    )
                )

        self.assertTrue(diagnostics["legacy_trusted"])
        self.assertFalse(diagnostics["legacy_trust_stale"])

    def test_edited_script_after_trust_reports_stale_not_trusted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            script = self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            self._global_config(xdg_home, workspace)
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                project_resolution.gather_project_trust_set_diagnostics("Legacy")
                script.write_text("echo edited\n", encoding="utf-8")
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Legacy"
                    )
                )

        self.assertFalse(diagnostics["legacy_trusted"])
        self.assertTrue(diagnostics["legacy_trust_stale"])

    def test_trust_ignored_when_recorded_for_a_different_script_path(self):
        # A trust record's path must match the resolved project's own legacy
        # script; a record that points elsewhere must not grant trust here.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            self._write_legacy_script(project_root, "echo same-content\n")
            other_root = workspace / "Other"
            self._write_legacy_script(other_root, "echo same-content\n")
            xdg_home = temp_path / "xdg"
            self._global_config(xdg_home, workspace)
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                # Trust "Other"'s script (identical content/digest, different path).
                project_resolution.gather_project_trust_set_diagnostics("Other")
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Legacy"
                    )
                )

        self.assertFalse(diagnostics["legacy_trusted"])

    def test_shell_payload_includes_legacy_trust_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            workspace = temp_path / "Workspace"
            project_root = workspace / "Legacy"
            self._write_legacy_script(project_root)
            xdg_home = temp_path / "xdg"
            self._global_config(xdg_home, workspace)
            env = {"XDG_CONFIG_HOME": str(xdg_home), "HOME": str(temp_path)}

            with mock.patch.dict(os.environ, env):
                global_config.gather_config_legacy_sourcing_set_diagnostics(True)
                project_resolution.gather_project_trust_set_diagnostics("Legacy")
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Legacy"
                    )
                )
                rendered = project_resolution.format_project_activate_shell_output(
                    diagnostics
                )

        self.assertIn("TAURWORKS_ACTIVATION_PROJECT_NAME=Legacy", rendered)
        self.assertIn("TAURWORKS_ACTIVATION_LEGACY_SETUP_EXISTS=True", rendered)
        self.assertIn("TAURWORKS_ACTIVATION_LEGACY_SOURCING_ENABLED=True", rendered)
        self.assertIn("TAURWORKS_ACTIVATION_LEGACY_TRUSTED=True", rendered)
        self.assertIn("TAURWORKS_ACTIVATION_LEGACY_TRUST_STALE=False", rendered)


if __name__ == "__main__":
    unittest.main()
