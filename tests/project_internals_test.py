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
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.relative_working_dir(project_dir, project_dir, "..")
            self.assertIn("may not escape", str(context.exception))
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.relative_working_dir_metadata(
                    project_dir, "../outside"
                )
            self.assertIn("may not escape", str(context.exception))

    def _make_symlinked_project(
        self, temp_dir: str
    ) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        """Return (project_dir, link, external) with project_dir/link -> external."""
        root_dir = pathlib.Path(temp_dir).resolve()
        project_dir = root_dir / "Workspace" / "proj"
        project_dir.mkdir(parents=True)
        external = root_dir / "Tempspace" / "proj" / "working_dir"
        external.mkdir(parents=True)
        link = project_dir / "working_dir"
        link.symlink_to(external, target_is_directory=True)
        return project_dir, link, external

    def test_working_dir_symlink_to_external_directory_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, _link, external = self._make_symlinked_project(temp_dir)

            relative = project_internals.relative_working_dir(
                project_dir, project_dir, "working_dir"
            )
            self.assertEqual(pathlib.Path("working_dir"), relative)

            relative, exists = project_internals.relative_working_dir_metadata(
                project_dir, "working_dir"
            )
            self.assertEqual(pathlib.Path("working_dir"), relative)
            self.assertTrue(exists)

            relative, resolved, exists = (
                project_internals.resolve_configured_working_dir(
                    project_dir, "working_dir"
                )
            )
            self.assertEqual(pathlib.Path("working_dir"), relative)
            self.assertEqual(external, resolved)
            self.assertTrue(exists)

    def test_working_dir_set_stores_symlink_path_and_nested_child(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, _link, external = self._make_symlinked_project(temp_dir)
            (external / "sub").mkdir()
            (project_dir / ".taurworks").mkdir()
            (project_dir / ".taurworks" / "config.toml").write_text(
                'schema_version = 1\n\n[project]\nname = "proj"\n',
                encoding="utf-8",
            )
            _previous, stored, _repairs = project_internals.set_working_dir(
                project_dir, project_dir, "working_dir/sub"
            )
            self.assertEqual("working_dir/sub", stored)
            config = project_internals.read_project_config(project_dir)
            self.assertEqual("working_dir/sub", config["paths"]["working_dir"])

    def test_relative_working_dir_leading_dotdot_steps_up_physical_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            (project_dir / "docs").mkdir(parents=True)
            (project_dir / "repo").mkdir()
            relative = project_internals.relative_working_dir(
                project_dir, project_dir / "docs", "../repo"
            )
            self.assertEqual(pathlib.Path("repo"), relative)
            relative = project_internals.relative_working_dir(
                project_dir, project_dir / "docs", ".."
            )
            self.assertEqual(pathlib.Path("."), relative)
            relative = project_internals.relative_working_dir(
                project_dir, project_dir / "repo", None
            )
            self.assertEqual(pathlib.Path("repo"), relative)
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.relative_working_dir(
                    project_dir, project_dir / "docs", "../.."
                )
            self.assertIn("may not escape", str(context.exception))

    def test_in_root_dotdot_working_dir_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            (project_dir / "repo").mkdir(parents=True)
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.relative_working_dir_metadata(
                    project_dir, "repo/../repo"
                )
            self.assertIn("may not escape", str(context.exception))
            self.assertIn("plain relative path", str(context.exception))
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.relative_working_dir(
                    project_dir, project_dir, "repo/../repo"
                )
            self.assertIn("plain relative path", str(context.exception))

    def test_dotdot_through_symlink_component_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, _link, external = self._make_symlinked_project(temp_dir)
            (external.parent / "sibling").mkdir()
            for value in ("working_dir/..", "working_dir/../sibling"):
                with self.subTest(value=value):
                    with self.assertRaises(project_internals.ProjectConfigError):
                        project_internals.relative_working_dir_metadata(
                            project_dir, value
                        )
                    with self.assertRaises(project_internals.ProjectConfigError):
                        project_internals.relative_working_dir(
                            project_dir, project_dir, value
                        )

    def _assert_invalid_symlink_rejected(
        self, project_dir: pathlib.Path, value: str, expected_text: str
    ) -> None:
        with self.assertRaises(project_internals.ProjectConfigError) as context:
            project_internals.relative_working_dir_metadata(project_dir, value)
        self.assertIn(expected_text, str(context.exception))
        self.assertNotIn("may not escape", str(context.exception))
        with self.assertRaises(project_internals.ProjectConfigError) as context:
            project_internals.relative_working_dir(project_dir, project_dir, value)
        self.assertIn(expected_text, str(context.exception))
        with self.assertRaises(project_internals.ProjectConfigError):
            project_internals.resolve_configured_working_dir(project_dir, value)

    def test_dangling_working_dir_symlink_raises_config_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            project_dir.mkdir()
            missing_target = pathlib.Path(temp_dir).resolve() / "gone" / "working_dir"
            (project_dir / "working_dir").symlink_to(
                missing_target, target_is_directory=True
            )
            self._assert_invalid_symlink_rejected(
                project_dir, "working_dir", "dangling symlink"
            )
            self._assert_invalid_symlink_rejected(
                project_dir, "working_dir/sub", "dangling symlink"
            )

    def test_looping_working_dir_symlink_raises_config_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            project_dir.mkdir()
            (project_dir / "self").symlink_to(project_dir / "self")
            (project_dir / "a").symlink_to(project_dir / "b")
            (project_dir / "b").symlink_to(project_dir / "a")
            for value in ("self", "self/sub", "a"):
                with self.subTest(value=value):
                    self._assert_invalid_symlink_rejected(
                        project_dir, value, "symlink loop"
                    )

    def test_dangling_symlink_inside_external_target_raises_config_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, _link, external = self._make_symlinked_project(temp_dir)
            (external / "inner").symlink_to(
                external / "missing", target_is_directory=True
            )
            self._assert_invalid_symlink_rejected(
                project_dir, "working_dir/inner", "dangling symlink"
            )

    def test_ordinary_missing_working_dir_is_reported_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            project_dir.mkdir()
            relative, exists = project_internals.relative_working_dir_metadata(
                project_dir, "repo/nested"
            )
            self.assertEqual(pathlib.Path("repo/nested"), relative)
            self.assertFalse(exists)
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.relative_working_dir(project_dir, project_dir, "repo")
            self.assertIn("must be an existing directory", str(context.exception))

    def test_create_working_dir_creates_ordinary_missing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            project_dir.mkdir()
            relative, resolved, created = (
                project_internals.create_working_dir_metadata_target(
                    project_dir, "repo/nested"
                )
            )
            self.assertEqual("repo/nested", relative)
            self.assertTrue(created)
            self.assertTrue((project_dir / "repo" / "nested").is_dir())
            self.assertEqual(project_dir / "repo" / "nested", resolved)

    def test_create_working_dir_creates_missing_tail_inside_valid_symlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir, _link, external = self._make_symlinked_project(temp_dir)
            relative, resolved, created = (
                project_internals.create_working_dir_metadata_target(
                    project_dir, "working_dir/missing"
                )
            )
            self.assertEqual("working_dir/missing", relative)
            self.assertTrue(created)
            self.assertEqual(external / "missing", resolved)
            self.assertTrue((external / "missing").is_dir())

    def test_create_working_dir_refuses_dangling_symlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir).resolve() / "proj"
            project_dir.mkdir()
            missing_target = pathlib.Path(temp_dir).resolve() / "gone" / "working_dir"
            (project_dir / "working_dir").symlink_to(
                missing_target, target_is_directory=True
            )
            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.create_working_dir_metadata_target(
                    project_dir, "working_dir"
                )
            self.assertIn("dangling symlink", str(context.exception))
            self.assertFalse(missing_target.exists())
            self.assertFalse(missing_target.parent.exists())

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

    def test_set_working_dir_preserves_nested_activation_exports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            repo_dir = project_dir / "repo"
            metadata_dir = project_dir / ".taurworks"
            repo_dir.mkdir(parents=True)
            metadata_dir.mkdir()
            (metadata_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "proj"\n\n'
                    '[activation]\nmessage = "Ready"\n\n'
                    '[activation.exports]\nNODE_OPTIONS = "--max-old-space-size=8192"\n'
                ),
                encoding="utf-8",
            )

            project_internals.set_working_dir(project_dir, project_dir, "repo")
            config = project_internals.read_project_config(project_dir)

        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertEqual("Ready", config["activation"]["message"])
        self.assertEqual(
            "--max-old-space-size=8192",
            config["activation"]["exports"]["NODE_OPTIONS"],
        )

    def test_set_activation_environment_writes_new_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)

            previous_name, configured_name, repairs = (
                project_internals.set_activation_environment(project_dir, "MyEnv")
            )
            config = project_internals.read_project_config(project_dir)

        self.assertIsNone(previous_name)
        self.assertEqual("MyEnv", configured_name)
        self.assertIn("schema_version set to 1", repairs)
        self.assertEqual("conda", config["activation"]["environment"]["type"])
        self.assertEqual("MyEnv", config["activation"]["environment"]["name"])

    def test_set_activation_environment_overwrites_previous_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            (metadata_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "proj"\n\n'
                    "[activation.environment]\n"
                    'type = "conda"\n'
                    'name = "OldEnv"\n'
                ),
                encoding="utf-8",
            )

            previous_name, configured_name, _repairs = (
                project_internals.set_activation_environment(project_dir, "NewEnv")
            )
            config = project_internals.read_project_config(project_dir)

        self.assertEqual("OldEnv", previous_name)
        self.assertEqual("NewEnv", configured_name)
        self.assertEqual("NewEnv", config["activation"]["environment"]["name"])

    def test_set_activation_environment_overwrites_malformed_existing_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            (metadata_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "proj"\n\n'
                    "[activation.environment]\n"
                    'type = "venv"\n'  # unsupported type: malformed per validator
                ),
                encoding="utf-8",
            )

            previous_name, configured_name, _repairs = (
                project_internals.set_activation_environment(project_dir, "NewEnv")
            )
            config = project_internals.read_project_config(project_dir)

        self.assertIsNone(previous_name)
        self.assertEqual("NewEnv", configured_name)
        self.assertEqual("conda", config["activation"]["environment"]["type"])
        self.assertEqual("NewEnv", config["activation"]["environment"]["name"])

    def test_set_activation_environment_rejects_invalid_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)

            with self.assertRaises(project_internals.ProjectConfigError) as context:
                project_internals.set_activation_environment(project_dir, "../unsafe")
            self.assertIn(
                "invalid Conda activation environment name", str(context.exception)
            )
            self.assertFalse(
                (metadata_dir / "config.toml").exists(),
                "invalid name must not write config",
            )

    def test_set_activation_environment_preserves_nested_working_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "proj"
            metadata_dir = project_dir / ".taurworks"
            metadata_dir.mkdir(parents=True)
            (metadata_dir / "config.toml").write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "proj"\n\n'
                    '[paths]\nworking_dir = "repo"\n'
                ),
                encoding="utf-8",
            )

            project_internals.set_activation_environment(project_dir, "MyEnv")
            config = project_internals.read_project_config(project_dir)

        self.assertEqual("repo", config["paths"]["working_dir"])
        self.assertEqual("MyEnv", config["activation"]["environment"]["name"])

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
