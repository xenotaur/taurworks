import contextlib
import io
import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock

from taurworks import manager


class ManagerModuleTest(unittest.TestCase):
    def test_camel_to_snake(self):
        self.assertEqual(manager.camel_to_snake("ProjectName"), "project_name")

    def test_get_directory_info_counts_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "a.txt").write_text("a", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.txt").write_text("bc", encoding="utf-8")
            size, count = manager.get_directory_info(str(root))
        self.assertEqual(count, 2)
        self.assertGreaterEqual(size, 3)

    def test_get_conda_environments_returns_empty_set_on_timeout(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with unittest.mock.patch.object(
                manager.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(["conda", "env", "list"], 2),
            ) as run_mock:
                envs = manager.get_conda_environments()

        self.assertEqual(envs, set())
        self.assertIn(
            "Warning: Could not fetch Conda environments: "
            "`conda env list` timed out after 2 seconds",
            stdout.getvalue(),
        )
        run_mock.assert_called_once_with(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=manager.CONDA_ENV_LIST_TIMEOUT_SECONDS,
        )

    def test_project_status_classification_for_workspace_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            initialized = workspace / "Initialized"
            workspace_only = workspace / "WorkspaceOnly"
            legacy_admin = workspace / "LegacyAdmin"
            metadata_only = workspace / "MetadataOnly"
            missing_workdir = workspace / "MissingWorkdir"
            initialized_repo = initialized / "repo"
            initialized_config = initialized / ".taurworks" / "config.toml"
            missing_workdir_config = missing_workdir / ".taurworks" / "config.toml"
            legacy_setup = legacy_admin / "Admin" / "project-setup.source"

            initialized_config.parent.mkdir(parents=True)
            initialized_repo.mkdir(parents=True)
            initialized_config.write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "Initialized"\n\n'
                    '[paths]\nworking_dir = "repo"\n'
                ),
                encoding="utf-8",
            )
            workspace_only.mkdir()
            metadata_only.joinpath(".taurworks").mkdir(parents=True)
            missing_workdir_config.parent.mkdir(parents=True)
            missing_workdir_config.write_text(
                (
                    "schema_version = 1\n\n"
                    '[project]\nname = "MissingWorkdir"\n\n'
                    '[paths]\nworking_dir = "missing"\n'
                ),
                encoding="utf-8",
            )
            legacy_setup.parent.mkdir(parents=True)
            legacy_setup.write_text("echo should-not-run\n", encoding="utf-8")

            initialized_status = manager.classify_project_entry(initialized)
            workspace_only_status = manager.classify_project_entry(workspace_only)
            legacy_admin_status = manager.classify_project_entry(legacy_admin)
            metadata_only_status = manager.classify_project_entry(metadata_only)
            missing_workdir_status = manager.classify_project_entry(missing_workdir)

        self.assertEqual(
            initialized_status["status"], manager.PROJECT_STATUS_INITIALIZED
        )
        self.assertTrue(initialized_status["activation_eligible"])
        self.assertEqual(initialized_status["working_dir"], "repo")
        self.assertTrue(initialized_status["working_dir_exists"])
        self.assertEqual(
            workspace_only_status["status"], manager.PROJECT_STATUS_WORKSPACE_ONLY
        )
        self.assertFalse(workspace_only_status["activation_eligible"])
        self.assertEqual(
            legacy_admin_status["status"], manager.PROJECT_STATUS_LEGACY_ADMIN
        )
        self.assertFalse(legacy_admin_status["activation_eligible"])
        self.assertIn("not sourced", legacy_admin_status["status_message"])
        self.assertEqual(
            metadata_only_status["status"], manager.PROJECT_STATUS_WORKSPACE_ONLY
        )
        self.assertTrue(metadata_only_status["metadata_dir_exists"])
        self.assertIn("config.toml is missing", metadata_only_status["status_message"])
        self.assertEqual(
            missing_workdir_status["status"], manager.PROJECT_STATUS_INITIALIZED
        )
        self.assertTrue(missing_workdir_status["working_dir_configured"])
        self.assertFalse(missing_workdir_status["working_dir_exists"])
        self.assertFalse(missing_workdir_status["activation_eligible"])
        self.assertIn("missing on disk", missing_workdir_status["status_message"])

    def test_classification_does_not_mutate_files_or_source_legacy_admin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyAdmin"
            setup_script = project_dir / "Admin" / "project-setup.source"
            sentinel = project_dir / "sourced.txt"
            setup_script.parent.mkdir(parents=True)
            setup_script.write_text(
                f"#!/bin/sh\nprintf touched > {sentinel}\n", encoding="utf-8"
            )
            before_paths = sorted(
                path.relative_to(project_dir) for path in project_dir.rglob("*")
            )

            status = manager.classify_project_entry(project_dir)

            after_paths = sorted(
                path.relative_to(project_dir) for path in project_dir.rglob("*")
            )

        self.assertEqual(status["status"], manager.PROJECT_STATUS_LEGACY_ADMIN)
        self.assertEqual(before_paths, after_paths)
        self.assertFalse(sentinel.exists())


if __name__ == "__main__":
    unittest.main()
