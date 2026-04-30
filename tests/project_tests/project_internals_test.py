import pathlib
import tempfile
import unittest

from taurworks import project_internals


class ProjectInternalsTest(unittest.TestCase):
    def test_resolve_project_target_defaults_to_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = pathlib.Path(temp_dir)
            resolved = project_internals.resolve_project_target(None, cwd)
            self.assertEqual(cwd.resolve(), resolved)

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

            self.assertFalse(diagnostics["changed"])
            self.assertIn(
                f"config file retained without changes: {config_path}",
                diagnostics["skipped"],
            )
            self.assertEqual(
                '[project]\nname = "existing"\n',
                config_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
