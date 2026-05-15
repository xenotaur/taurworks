import os
import pathlib
import tempfile
import tomllib
import unittest
from unittest import mock

from taurworks import global_config


class GlobalConfigTest(unittest.TestCase):

    def test_config_path_uses_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"XDG_CONFIG_HOME": temp_dir, "HOME": "/unused-home"}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = global_config.config_path()
        self.assertEqual(
            pathlib.Path(temp_dir) / "taurworks" / "config.toml", resolved.path
        )
        self.assertEqual("XDG_CONFIG_HOME", resolved.source)

    def test_config_path_falls_back_to_home_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = global_config.config_path()
        self.assertEqual(
            pathlib.Path(temp_dir) / ".config" / "taurworks" / "config.toml",
            resolved.path,
        )
        self.assertEqual("default fallback", resolved.source)

    def test_workspace_show_without_config_infers_existing_home_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = pathlib.Path(temp_dir)
            workspace = home / "Workspace"
            workspace.mkdir()
            with mock.patch.dict(os.environ, {"HOME": str(home)}, clear=True):
                diagnostics = global_config.gather_workspace_show_diagnostics()

        self.assertFalse(diagnostics["config_exists"])
        self.assertEqual(str(workspace.resolve()), diagnostics["workspace_root"])
        self.assertEqual("inferred", diagnostics["workspace_root_source"])
        self.assertEqual("none", diagnostics["configured_workspace_root"])
        self.assertEqual(
            str(workspace.resolve()), diagnostics["inferred_workspace_root"]
        )
        self.assertFalse((home / ".config" / "taurworks" / "config.toml").exists())

    def test_workspace_show_with_configured_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            workspace = root / "configured-workspace"
            workspace.mkdir()
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
                diagnostics = global_config.gather_workspace_show_diagnostics()

        self.assertTrue(diagnostics["config_exists"])
        self.assertEqual(str(workspace.resolve()), diagnostics["workspace_root"])
        self.assertEqual("configured", diagnostics["workspace_root_source"])
        self.assertEqual(str(workspace), diagnostics["configured_workspace_root"])
        self.assertEqual("none", diagnostics["inferred_workspace_root"])

    def test_workspace_set_writes_config_and_preserves_unrelated_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            workspace = root / "workspace"
            workspace.mkdir()
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                'schema_version = 1\ncustom = "keep"\n\n[other]\nvalue = "still here"\n',
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = global_config.gather_workspace_set_diagnostics(
                    str(workspace)
                )

            written = tomllib.loads(config_path.read_text(encoding="utf-8"))

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(str(workspace.resolve()), diagnostics["workspace_root"])
        self.assertEqual(1, written["schema_version"])
        self.assertEqual("keep", written["custom"])
        self.assertEqual("still here", written["other"]["value"])
        self.assertEqual(str(workspace.resolve()), written["workspace"]["root"])

    def test_workspace_set_rejects_missing_path_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            missing_workspace = root / "missing"
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = global_config.gather_workspace_set_diagnostics(
                    str(missing_workspace)
                )

        self.assertFalse(diagnostics["ok"])
        self.assertFalse((config_home / "taurworks" / "config.toml").exists())


if __name__ == "__main__":
    unittest.main()
