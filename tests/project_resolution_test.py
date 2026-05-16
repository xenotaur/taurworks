import os
import pathlib
import tempfile
import unittest

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
        self.assertEqual((project_dir / "TestProject").resolve(), resolved)

    def test_resolve_project_refresh_target_defaults_to_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = pathlib.Path(temp_dir)
            original = pathlib.Path.cwd()
            try:
                __import__("os").chdir(cwd)
                resolved = project_resolution.resolve_project_refresh_target(None)
            finally:
                __import__("os").chdir(original)
        self.assertEqual(cwd.resolve(), resolved)


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
            original_xdg = os.environ.get("XDG_CONFIG_HOME")
            try:
                os.environ["XDG_CONFIG_HOME"] = str(xdg_home)
                os.chdir(outside)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "WorkspaceProject"
                    )
                )
            finally:
                os.chdir(original_cwd)
                if original_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = original_xdg

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(diagnostics["resolved_working_dir"], str(working_dir))
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
            original_xdg = os.environ.get("XDG_CONFIG_HOME")
            try:
                os.environ["XDG_CONFIG_HOME"] = str(xdg_home)
                os.chdir(first_repo)
                diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "SecondProject"
                    )
                )
            finally:
                os.chdir(original_cwd)
                if original_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = original_xdg

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(diagnostics["resolved_working_dir"], str(second_repo))
        self.assertEqual(diagnostics["project_root"], str(second_root))

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

            original_xdg = os.environ.get("XDG_CONFIG_HOME")
            try:
                os.environ["XDG_CONFIG_HOME"] = str(xdg_home)
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
            finally:
                if original_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = original_xdg

        self.assertTrue(workspace_diagnostics["ok"])
        self.assertEqual(
            workspace_diagnostics["resolved_working_dir"], str(workspace_only)
        )
        self.assertIn("not initialized", str(workspace_diagnostics["guidance"]))
        self.assertTrue(legacy_diagnostics["ok"])
        self.assertEqual(legacy_diagnostics["resolved_working_dir"], str(legacy))
        self.assertIn("was not sourced", str(legacy_diagnostics["guidance"]))
        self.assertFalse(sentinel.exists())

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

            original_xdg = os.environ.get("XDG_CONFIG_HOME")
            try:
                os.environ["XDG_CONFIG_HOME"] = str(xdg_home)
                listing = project_resolution.gather_project_list_diagnostics()
                hidden_diagnostics = (
                    project_resolution.gather_project_activate_print_diagnostics(
                        "Hidden"
                    )
                )
            finally:
                if original_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = original_xdg

        names = [project["name"] for project in listing["projects"]]
        self.assertIn("Hidden", names)
        self.assertEqual(names.count("Duplicate"), 1)
        self.assertTrue(hidden_diagnostics["ok"])
        self.assertEqual(hidden_diagnostics["resolved_working_dir"], str(hidden_repo))
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

            original_xdg = os.environ.get("XDG_CONFIG_HOME")
            try:
                os.environ["XDG_CONFIG_HOME"] = str(xdg_home)
                listing = project_resolution.gather_project_list_diagnostics()
            finally:
                if original_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = original_xdg

        names = [project["name"] for project in listing["projects"]]
        self.assertIn("Parent", names)
        self.assertNotIn("Nested", names)


if __name__ == "__main__":
    unittest.main()
