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


if __name__ == "__main__":
    unittest.main()
