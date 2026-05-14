import pathlib
import tempfile
import unittest

from taurworks import project_internals


class ProjectInternalsTest(unittest.TestCase):
    def test_resolve_project_target_defaults_to_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = pathlib.Path(temp_dir)
            resolved = project_internals.resolve_project_target(None, cwd)
            self.assertEqual(cwd.resolve(), resolved.project_root)
            self.assertEqual(
                project_internals.ResolutionReason.DEFAULT_CURRENT_DIRECTORY,
                resolved.resolved_by,
            )

    def test_resolve_project_target_uses_current_project_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = pathlib.Path(temp_dir)
            project_dir = root_dir / "TestProject"
            same_name_child = project_dir / "TestProject"
            same_name_child.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "TestProject"\n',
                encoding="utf-8",
            )
            resolved = project_internals.resolve_project_target(
                "TestProject",
                project_dir,
                prefer_project_root=True,
            )
        self.assertEqual(project_dir.resolve(), resolved.project_root)
        self.assertNotEqual(same_name_child.resolve(), resolved.project_root)
        self.assertEqual(
            project_internals.ResolutionReason.CURRENT_PROJECT_NAME,
            resolved.resolved_by,
        )

    def test_resolve_project_target_collapses_existing_child_to_project_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = pathlib.Path(temp_dir)
            project_dir = root_dir / "TestProject"
            child_dir = project_dir / "repo"
            child_dir.mkdir(parents=True)
            (project_dir / ".taurworks").mkdir()
            resolved = project_internals.resolve_project_target(
                str(child_dir),
                root_dir,
                prefer_project_root=True,
            )
        self.assertEqual(project_dir.resolve(), resolved.project_root)
        self.assertEqual(
            project_internals.ResolutionReason.EXISTING_PATH_PROJECT_ROOT,
            resolved.resolved_by,
        )

    def test_find_project_root_candidate_walks_parents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            project_root = root / "proj"
            nested = project_root / "a" / "b"
            (project_root / ".taurworks").mkdir(parents=True)
            nested.mkdir(parents=True)
            resolved = project_internals.find_project_root_candidate(nested)
            self.assertEqual(project_root, resolved)

    def test_scaffold_project_metadata_preserves_existing_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            config_path = metadata_dir / "config.toml"
            config_path.write_text('[project]\nname = "existing"\n', encoding="utf-8")
            diagnostics = project_internals.scaffold_project_metadata(project_dir)
            self.assertTrue(diagnostics["changed"])
            self.assertIn(
                f"config repaired: {config_path}",
                diagnostics["updated"],
            )
            config = project_internals.read_project_config(project_dir)
            self.assertEqual(1, config["schema_version"])
            self.assertEqual("existing", config["project"]["name"])

    def test_scaffold_project_metadata_warns_for_symlinked_metadata_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = pathlib.Path(temp_dir)
            project_dir = root_dir / "proj"
            project_dir.mkdir()
            linked_metadata_dir = root_dir / "linked-metadata"
            linked_metadata_dir.mkdir()
            metadata_symlink = project_dir / ".taurworks"
            metadata_symlink.symlink_to(linked_metadata_dir, target_is_directory=True)
            diagnostics = project_internals.scaffold_project_metadata(project_dir)
            self.assertFalse(diagnostics["changed"])
            self.assertIn(
                f"metadata path is a symlink and is not modified for safety: {metadata_symlink}",
                diagnostics["warnings"],
            )

    def test_scaffold_project_metadata_warns_for_symlinked_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = pathlib.Path(temp_dir)
            project_dir = root_dir / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            config_target = root_dir / "config-target.toml"
            config_target.write_text(
                '[project]\nname = "external-target"\n', encoding="utf-8"
            )
            config_symlink = metadata_dir / "config.toml"
            config_symlink.symlink_to(config_target)
            diagnostics = project_internals.scaffold_project_metadata(project_dir)
            self.assertFalse(diagnostics["changed"])
            self.assertIn(
                f"config path is a symlink and is not modified for safety: {config_symlink}",
                diagnostics["warnings"],
            )

    def test_scaffold_project_metadata_writes_minimal_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "SchemaProject"
            diagnostics = project_internals.scaffold_project_metadata(project_dir)
            self.assertTrue(diagnostics["changed"])
            config = project_internals.read_project_config(project_dir)
            self.assertEqual(1, config["schema_version"])
            self.assertEqual("SchemaProject", config["project"]["name"])
            self.assertNotIn("paths", config)

    def test_scaffold_project_metadata_repairs_empty_project_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "RepairedProject"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            config_path = metadata_dir / "config.toml"
            config_path.write_text(
                'schema_version = 1\n\n[project]\nname = ""\n',
                encoding="utf-8",
            )
            diagnostics = project_internals.scaffold_project_metadata(project_dir)
            self.assertTrue(diagnostics["changed"])
            config = project_internals.read_project_config(project_dir)
            self.assertEqual("RepairedProject", config["project"]["name"])

    def test_relative_working_dir_rejects_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            project_dir.mkdir()
            with self.assertRaises(project_internals.ProjectConfigError):
                project_internals.relative_working_dir(
                    project_dir, project_dir, str(project_dir)
                )

    def test_relative_working_dir_rejects_paths_outside_project_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            project_dir.mkdir()
            with self.assertRaises(project_internals.ProjectConfigError):
                project_internals.relative_working_dir(project_dir, project_dir, "..")

    def test_write_project_config_rejects_symlinked_metadata_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = pathlib.Path(temp_dir)
            project_dir = root_dir / "proj"
            project_dir.mkdir()
            linked_metadata_dir = root_dir / "linked-metadata"
            linked_metadata_dir.mkdir()
            metadata_symlink = project_dir / ".taurworks"
            metadata_symlink.symlink_to(linked_metadata_dir, target_is_directory=True)
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.write_project_config(
                    project_dir,
                    {"schema_version": 1, "project": {"name": "proj"}},
                )
            self.assertIn("metadata path is a symlink", str(context.exception))

    def test_write_project_config_rejects_non_bare_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            (project_dir / ".taurworks").mkdir(parents=True)
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.write_project_config(
                    project_dir,
                    {
                        "schema_version": 1,
                        "project": {"name": "proj"},
                        "quoted key": "value",
                    },
                )
            self.assertIn("unsupported TOML key", str(context.exception))

    def test_scaffold_project_metadata_skips_config_with_unsupported_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            config_path = metadata_dir / "config.toml"
            original_config = '[project]\nname = "proj"\n\n"quoted key" = "value"\n'
            config_path.write_text(original_config, encoding="utf-8")
            diagnostics = project_internals.scaffold_project_metadata(project_dir)
            self.assertFalse(diagnostics["changed"])
            self.assertIn(
                "config file update skipped",
                "\n".join(diagnostics["skipped"]),
            )
            self.assertIn(
                "unsupported TOML key",
                "\n".join(diagnostics["warnings"]),
            )
            self.assertEqual(original_config, config_path.read_text(encoding="utf-8"))

    def test_ensure_minimal_project_config_rejects_future_schema_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            project_dir.mkdir()
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.ensure_minimal_project_config(
                    project_dir,
                    {"schema_version": 2, "project": {"name": "proj"}},
                )
            self.assertIn(
                "unsupported project config schema_version", str(context.exception)
            )

    def test_ensure_minimal_project_config_defaults_invalid_schema_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            project_dir.mkdir()
            config, changes = project_internals.ensure_minimal_project_config(
                project_dir,
                {"schema_version": "legacy", "project": {"name": "proj"}},
            )
            self.assertEqual(1, config["schema_version"])
            self.assertIn("schema_version set to 1", changes)


if __name__ == "__main__":
    unittest.main()
