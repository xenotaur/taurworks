import os
import pathlib
import tempfile
import tomllib
import unittest
from unittest import mock

from taurworks import project_registry


class ProjectRegistryTest(unittest.TestCase):

    def test_register_writes_global_config_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "xdg"
            project_root = root / "outside" / "HiddenProject"
            project_root.mkdir(parents=True)
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(project_root)
                )
            config_path = config_home / "taurworks" / "config.toml"
            config = tomllib.loads(config_path.read_text(encoding="utf-8"))

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(str(project_root.resolve()), diagnostics["project_root"])
        self.assertEqual(
            str(project_root.resolve()), config["projects"]["HiddenProject"]["root"]
        )
        self.assertEqual(1, config["schema_version"])

    def test_unregister_removes_only_registry_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "xdg"
            project_root = root / "HiddenProject"
            config_file = project_root / ".taurworks" / "config.toml"
            config_file.parent.mkdir(parents=True)
            config_file.write_text("schema_version = 1\n", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                register = project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(project_root)
                )
                unregister = project_registry.gather_project_unregister_diagnostics(
                    "HiddenProject"
                )
            config_path = config_home / "taurworks" / "config.toml"
            config = tomllib.loads(config_path.read_text(encoding="utf-8"))
            project_config_still_exists = config_file.is_file()

        self.assertTrue(register["ok"])
        self.assertTrue(unregister["ok"])
        self.assertTrue(project_config_still_exists)
        self.assertNotIn("projects", config)
        self.assertFalse(unregister["project_files_deleted"])

    def test_registry_list_reports_entry_status_and_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "xdg"
            project_root = root / "HiddenProject"
            config_file = project_root / ".taurworks" / "config.toml"
            config_file.parent.mkdir(parents=True)
            config_file.write_text("schema_version = 1\n", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(project_root)
                )
                before = (config_home / "taurworks" / "config.toml").read_text(
                    encoding="utf-8"
                )
                diagnostics = (
                    project_registry.gather_project_registry_list_diagnostics()
                )
                after = (config_home / "taurworks" / "config.toml").read_text(
                    encoding="utf-8"
                )

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(before, after)
        self.assertFalse(diagnostics["mutation_performed"])
        self.assertEqual(1, diagnostics["project_count"])
        self.assertTrue(diagnostics["projects"][0]["path_exists"])
        self.assertTrue(diagnostics["projects"][0]["project_config_exists"])

    def test_missing_path_requires_allow_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "xdg"
            missing_project = root / "missing"
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                rejected = project_registry.gather_project_register_diagnostics(
                    "MissingProject", str(missing_project)
                )
                allowed = project_registry.gather_project_register_diagnostics(
                    "MissingProject", str(missing_project), allow_missing=True
                )
            config = tomllib.loads(
                (config_home / "taurworks" / "config.toml").read_text(encoding="utf-8")
            )

        self.assertFalse(rejected["ok"])
        self.assertTrue(allowed["ok"])
        self.assertFalse(allowed["path_exists"])
        self.assertEqual(
            str(missing_project.resolve()), config["projects"]["MissingProject"]["root"]
        )

    def test_duplicate_name_requires_force(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "xdg"
            first_project = root / "first"
            second_project = root / "second"
            first_project.mkdir()
            second_project.mkdir()
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                first = project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(first_project)
                )
                duplicate = project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(second_project)
                )
                forced = project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(second_project), force=True
                )
            config = tomllib.loads(
                (config_home / "taurworks" / "config.toml").read_text(encoding="utf-8")
            )

        self.assertTrue(first["ok"])
        self.assertFalse(duplicate["ok"])
        self.assertIn("--force", duplicate["error"])
        self.assertTrue(forced["ok"])
        self.assertTrue(forced["overwrote_existing"])
        self.assertEqual(
            str(second_project.resolve()), config["projects"]["HiddenProject"]["root"]
        )

    def test_registry_workspace_name_collision_is_visible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "xdg"
            workspace = root / "workspace"
            workspace_child = workspace / "HiddenProject"
            external_project = root / "external" / "HiddenProject"
            workspace_child.mkdir(parents=True)
            external_project.mkdir(parents=True)
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                f'schema_version = 1\n\n[workspace]\nroot = "{workspace}"\n',
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                register = project_registry.gather_project_register_diagnostics(
                    "HiddenProject", str(external_project)
                )
                listing = project_registry.gather_project_registry_list_diagnostics()

        self.assertTrue(register["ok"])
        self.assertTrue(register["collision_with_workspace_child"])
        self.assertEqual(
            str(workspace_child.resolve()), register["workspace_child_root"]
        )
        self.assertTrue(listing["projects"][0]["collision_with_workspace_child"])
