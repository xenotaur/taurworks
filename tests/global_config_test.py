import os
import pathlib
import tempfile
import tomllib
import unittest
from unittest import mock

from helpers import assert_same_path

from taurworks import global_config


class GlobalConfigTest(unittest.TestCase):

    def test_config_path_uses_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"XDG_CONFIG_HOME": temp_dir, "HOME": "/unused-home"}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = global_config.config_path()
        assert_same_path(
            self, resolved.path, pathlib.Path(temp_dir) / "taurworks" / "config.toml"
        )
        self.assertEqual("XDG_CONFIG_HOME", resolved.source)

    def test_config_path_falls_back_to_home_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"HOME": temp_dir}
            with mock.patch.dict(os.environ, env, clear=True):
                resolved = global_config.config_path()
        assert_same_path(
            self,
            resolved.path,
            pathlib.Path(temp_dir) / ".config" / "taurworks" / "config.toml",
        )
        self.assertEqual("default fallback", resolved.source)

    def test_workspace_show_without_config_infers_existing_home_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = pathlib.Path(temp_dir)
            workspace = home / "Workspace"
            workspace.mkdir()
            with mock.patch.dict(os.environ, {"HOME": str(home)}, clear=True):
                diagnostics = global_config.gather_workspace_show_diagnostics()
            self.assertFalse((home / ".config" / "taurworks" / "config.toml").exists())

        self.assertFalse(diagnostics["config_exists"])
        assert_same_path(self, diagnostics["workspace_root"], workspace)
        self.assertEqual("inferred", diagnostics["workspace_root_source"])
        self.assertEqual("none", diagnostics["configured_workspace_root"])
        assert_same_path(self, diagnostics["inferred_workspace_root"], workspace)

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
        assert_same_path(self, diagnostics["workspace_root"], workspace)
        self.assertEqual("configured", diagnostics["workspace_root_source"])
        assert_same_path(self, diagnostics["configured_workspace_root"], workspace)
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
            self.assertFalse(diagnostics["created_config_parent"])
            written = tomllib.loads(config_path.read_text(encoding="utf-8"))

        self.assertTrue(diagnostics["ok"])
        assert_same_path(self, diagnostics["workspace_root"], workspace)
        self.assertEqual(1, written["schema_version"])
        self.assertEqual("keep", written["custom"])
        self.assertEqual("still here", written["other"]["value"])
        assert_same_path(self, written["workspace"]["root"], workspace)

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
            self.assertFalse((config_home / "taurworks" / "config.toml").exists())

        self.assertFalse(diagnostics["ok"])

    def test_workspace_set_preserves_nested_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            workspace = root / "workspace"
            workspace.mkdir()
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        "schema_version = 1",
                        "",
                        "[projects.HiddenProject]",
                        'root = "/tmp/hidden"',
                        'conda_environment = "hidden-env"',
                        "",
                    ]
                ),
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
            written_text = config_path.read_text(encoding="utf-8")
            written = tomllib.loads(written_text)

        self.assertTrue(diagnostics["ok"])
        self.assertIn("[projects.HiddenProject]", written_text)
        self.assertEqual("/tmp/hidden", written["projects"]["HiddenProject"]["root"])
        assert_same_path(self, written["workspace"]["root"], workspace)

    def test_write_config_omits_empty_parent_table_for_nested_projects(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            global_config.write_config(
                {
                    "schema_version": 1,
                    "projects": {"HiddenProject": {"root": "/tmp/hidden"}},
                },
                config_path,
            )
            written_text = config_path.read_text(encoding="utf-8")
            written = tomllib.loads(written_text)

        self.assertNotIn("[projects]", written_text)
        self.assertIn("[projects.HiddenProject]", written_text)
        self.assertEqual("/tmp/hidden", written["projects"]["HiddenProject"]["root"])

    def test_workspace_show_reports_malformed_config_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("schema_version = ", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = global_config.gather_workspace_show_diagnostics()

        self.assertFalse(diagnostics["ok"])
        self.assertEqual("invalid_config", diagnostics["workspace_root_source"])
        self.assertIn("Invalid value", diagnostics["error"])

    def test_workspace_set_reports_malformed_config_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            workspace = root / "workspace"
            workspace.mkdir()
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            original_text = "schema_version = "
            config_path.write_text(original_text, encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = global_config.gather_workspace_set_diagnostics(
                    str(workspace)
                )
            written_text = config_path.read_text(encoding="utf-8")

        self.assertFalse(diagnostics["ok"])
        self.assertEqual(original_text, written_text)
        self.assertIn("Invalid value", diagnostics["error"])

    def test_workspace_set_rejects_unsupported_schema_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            workspace = root / "workspace"
            workspace.mkdir()
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            original_text = "schema_version = 2\n"
            config_path.write_text(original_text, encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = global_config.gather_workspace_set_diagnostics(
                    str(workspace)
                )
            written_text = config_path.read_text(encoding="utf-8")

        self.assertFalse(diagnostics["ok"])
        self.assertEqual(original_text, written_text)
        self.assertIn("unsupported global config schema_version", diagnostics["error"])

    def test_workspace_show_reports_relative_configured_root_as_invalid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                'schema_version = 1\n\n[workspace]\nroot = "relative-workspace"\n',
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home), "HOME": str(root)},
                clear=True,
            ):
                diagnostics = global_config.gather_workspace_show_diagnostics()

        self.assertFalse(diagnostics["ok"])
        self.assertEqual("invalid_config", diagnostics["workspace_root_source"])
        self.assertIn("must be absolute", diagnostics["error"])

    def test_workspace_set_writes_parseable_paths_with_control_characters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            workspace = root / "workspace\nwith-newline"
            workspace.mkdir()
            config_path = config_home / "taurworks" / "config.toml"
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
        self.assertTrue(diagnostics["created_config_parent"])
        assert_same_path(self, written["workspace"]["root"], workspace)


class LegacySourcingSwitchTest(unittest.TestCase):
    def _env(self, config_home: pathlib.Path, home: pathlib.Path) -> dict[str, str]:
        return {"XDG_CONFIG_HOME": str(config_home), "HOME": str(home)}

    def test_default_is_disabled(self):
        config = {}
        self.assertFalse(global_config.configured_legacy_sourcing_enabled(config))

    def test_show_and_enable_and_disable_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            with mock.patch.dict(os.environ, self._env(config_home, root), clear=True):
                initial = global_config.gather_config_legacy_sourcing_show_diagnostics()
                self.assertTrue(initial["ok"])
                self.assertFalse(initial["legacy_sourcing_enabled"])

                enabled = global_config.gather_config_legacy_sourcing_set_diagnostics(
                    True
                )
                self.assertTrue(enabled["ok"])
                self.assertTrue(enabled["legacy_sourcing_enabled"])

                shown = global_config.gather_config_legacy_sourcing_show_diagnostics()
                self.assertTrue(shown["legacy_sourcing_enabled"])

                disabled = global_config.gather_config_legacy_sourcing_set_diagnostics(
                    False
                )
                self.assertTrue(disabled["ok"])
                self.assertFalse(disabled["legacy_sourcing_enabled"])

    def test_enable_preserves_unrelated_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config-home"
            config_path = config_home / "taurworks" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                'schema_version = 1\n\n[workspace]\nroot = "/x"\n', encoding="utf-8"
            )
            with mock.patch.dict(os.environ, self._env(config_home, root), clear=True):
                global_config.gather_config_legacy_sourcing_set_diagnostics(True)
            written = tomllib.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual("/x", written["workspace"]["root"])
        self.assertTrue(written["activation"]["legacy_sourcing"])


class TrustRecordTest(unittest.TestCase):
    DIGEST_A = "a" * 64
    DIGEST_B = "b" * 64

    def _env(self, config_home: pathlib.Path, home: pathlib.Path) -> dict[str, str]:
        return {"XDG_CONFIG_HOME": str(config_home), "HOME": str(home)}

    def test_trust_record_from_config_returns_none_when_absent(self):
        self.assertIsNone(global_config.trust_record_from_config({}, "Proj"))

    def test_trust_record_from_config_rejects_bad_digest(self):
        config = {"trust": {"Proj": {"path": "/x", "digest": "not-hex"}}}
        with self.assertRaises(global_config.GlobalConfigError):
            global_config.trust_record_from_config(config, "Proj")

    def test_trust_record_from_config_rejects_missing_path(self):
        config = {"trust": {"Proj": {"digest": self.DIGEST_A}}}
        with self.assertRaises(global_config.GlobalConfigError):
            global_config.trust_record_from_config(config, "Proj")

    def test_write_then_read_trust_record_round_trips(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            global_config.write_trust_record_preserving_config(
                config_path,
                {},
                "Proj",
                pathlib.Path("/x/Admin/setup.source"),
                self.DIGEST_A,
            )
            config = global_config.read_config(config_path)
        record = global_config.trust_record_from_config(config, "Proj")
        self.assertEqual("/x/Admin/setup.source", record["path"])
        self.assertEqual(self.DIGEST_A, record["digest"])

    def test_write_trust_record_rejects_relative_script_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            with self.assertRaises(global_config.GlobalConfigError) as context:
                global_config.write_trust_record_preserving_config(
                    config_path,
                    {},
                    "Proj",
                    pathlib.Path("relative/setup.source"),
                    self.DIGEST_A,
                )
            self.assertIn("must be absolute", str(context.exception))
            self.assertFalse(config_path.exists())

    def test_write_trust_record_rejects_malformed_digest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            with self.assertRaises(global_config.GlobalConfigError) as context:
                global_config.write_trust_record_preserving_config(
                    config_path, {}, "Proj", pathlib.Path("/x"), "not-a-digest"
                )
            self.assertIn("sha256 digest", str(context.exception))
            self.assertFalse(config_path.exists())

    def test_write_trust_record_overwrites_existing_digest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            global_config.write_trust_record_preserving_config(
                config_path, {}, "Proj", pathlib.Path("/x"), self.DIGEST_A
            )
            config = global_config.read_config(config_path)
            global_config.write_trust_record_preserving_config(
                config_path, config, "Proj", pathlib.Path("/x"), self.DIGEST_B
            )
            reread = global_config.read_config(config_path)
            table_count = config_path.read_text(encoding="utf-8").count("[trust.Proj]")
        record = global_config.trust_record_from_config(reread, "Proj")
        self.assertEqual(self.DIGEST_B, record["digest"])
        # exactly one [trust.Proj] table, not a duplicate
        self.assertEqual(1, table_count)

    def test_write_trust_record_preserves_unrelated_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            config_path.write_text(
                'schema_version = 1\n\n[workspace]\nroot = "/w"\n\n'
                '[trust.Other]\npath = "/y"\ndigest = "' + self.DIGEST_B + '"\n',
                encoding="utf-8",
            )
            config = global_config.read_config(config_path)
            global_config.write_trust_record_preserving_config(
                config_path, config, "Proj", pathlib.Path("/x"), self.DIGEST_A
            )
            written = global_config.read_config(config_path)
        self.assertEqual("/w", written["workspace"]["root"])
        self.assertEqual(
            self.DIGEST_B,
            global_config.trust_record_from_config(written, "Other")["digest"],
        )
        self.assertEqual(
            self.DIGEST_A,
            global_config.trust_record_from_config(written, "Proj")["digest"],
        )

    def test_remove_trust_record_leaves_sibling_intact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            global_config.write_trust_record_preserving_config(
                config_path, {}, "Proj", pathlib.Path("/x"), self.DIGEST_A
            )
            config = global_config.read_config(config_path)
            global_config.write_trust_record_preserving_config(
                config_path, config, "Other", pathlib.Path("/y"), self.DIGEST_B
            )
            config = global_config.read_config(config_path)
            global_config.remove_trust_record_preserving_config(
                config_path, config, "Proj"
            )
            written = global_config.read_config(config_path)
        self.assertIsNone(global_config.trust_record_from_config(written, "Proj"))
        self.assertIsNotNone(global_config.trust_record_from_config(written, "Other"))

    def test_trust_table_never_written_under_projects(self):
        # Regression guard for the exact bug this design avoids: trust data
        # must never live under [projects.NAME], which requires a non-empty
        # `root` and is iterated by the registry.
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / "config.toml"
            global_config.write_trust_record_preserving_config(
                config_path, {}, "Proj", pathlib.Path("/x"), self.DIGEST_A
            )
            text = config_path.read_text(encoding="utf-8")
        self.assertNotIn("[projects.Proj]", text)
        self.assertIn("[trust.Proj]", text)


if __name__ == "__main__":
    unittest.main()
