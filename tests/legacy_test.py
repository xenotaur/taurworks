import pathlib
import tempfile
import unittest

from taurworks import legacy
from taurworks import project_internals

LEGACY_SCRIPT = """#!/bin/bash
# Activate Conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ExampleEnv
export API_TOKEN=abc123
export DYNAMIC_VALUE=$(cat secret.txt)
cd "repo"
echo "Ready for work on ExampleProject"
"""


def _write_legacy_script(project_dir: pathlib.Path, text: str = LEGACY_SCRIPT) -> None:
    admin_dir = project_dir / "Admin"
    admin_dir.mkdir(parents=True, exist_ok=True)
    (admin_dir / "project-setup.source").write_text(text, encoding="utf-8")


class ParseLegacySetupScriptTest(unittest.TestCase):
    def test_detects_conda_activate(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        conda_matches = [m for m in matches if m["kind"] == "conda_activate"]
        self.assertEqual(len(conda_matches), 1)
        self.assertEqual(conda_matches[0]["detected"]["name"], "ExampleEnv")

    def test_detects_simple_export_and_marks_value_redacted(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        export_matches = [m for m in matches if m["kind"] == "export"]
        self.assertEqual(len(export_matches), 1)
        self.assertEqual(export_matches[0]["detected"]["name"], "API_TOKEN")
        self.assertTrue(export_matches[0]["detected"]["value_redacted"])

    def test_detects_cd(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        cd_matches = [m for m in matches if m["kind"] == "cd"]
        self.assertEqual(len(cd_matches), 1)
        self.assertEqual(cd_matches[0]["detected"]["path"], "repo")

    def test_detects_readiness_message(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        message_matches = [m for m in matches if m["kind"] == "message"]
        self.assertEqual(len(message_matches), 1)
        self.assertEqual(
            message_matches[0]["detected"]["message"],
            "Ready for work on ExampleProject",
        )

    def test_dynamic_export_value_is_unsupported_and_redacted(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        unsupported = [m for m in matches if m["kind"] == "unsupported"]
        dynamic_export = [
            m for m in unsupported if m["detected"].get("name") == "DYNAMIC_VALUE"
        ]
        self.assertEqual(len(dynamic_export), 1)
        self.assertNotIn("cat secret.txt", dynamic_export[0]["raw"])
        self.assertIn("<redacted>", dynamic_export[0]["raw"])

    def test_source_line_is_unsupported(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        unsupported_notes = [m["note"] for m in matches if m["kind"] == "unsupported"]
        self.assertTrue(
            any(
                "does not match a supported pattern" in note
                for note in unsupported_notes
            )
        )

    def test_blank_lines_and_comments_are_skipped(self):
        matches = legacy.parse_legacy_setup_script(LEGACY_SCRIPT)
        raw_lines = [m["raw"] for m in matches]
        self.assertFalse(any(line.strip().startswith("#") for line in raw_lines))

    def test_invalid_export_name_is_unsupported(self):
        matches = legacy.parse_legacy_setup_script("export 1BAD=value\n")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["kind"], "unsupported")
        self.assertIn("<redacted>", matches[0]["raw"])


class GatherLegacyInspectDiagnosticsTest(unittest.TestCase):
    def test_reports_missing_legacy_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "NoLegacy"
            project_dir.mkdir()
            diagnostics = legacy.gather_legacy_inspect_diagnostics(str(project_dir))
        self.assertFalse(diagnostics["ok"])
        self.assertFalse(diagnostics["legacy_setup_exists"])

    def test_inspect_never_writes_or_executes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir)
            sentinel = project_dir / "sourced.txt"
            before = sorted(p.relative_to(project_dir) for p in project_dir.rglob("*"))

            diagnostics = legacy.gather_legacy_inspect_diagnostics(str(project_dir))

            after = sorted(p.relative_to(project_dir) for p in project_dir.rglob("*"))

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(before, after)
        self.assertFalse(sentinel.exists())
        self.assertFalse((project_dir / ".taurworks").exists())

    def test_inspect_counts_supported_and_unsupported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir)
            diagnostics = legacy.gather_legacy_inspect_diagnostics(str(project_dir))

        self.assertEqual(diagnostics["supported_count"], 4)
        self.assertEqual(diagnostics["unsupported_count"], 2)

    def test_format_inspect_output_never_leaks_export_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir)
            diagnostics = legacy.gather_legacy_inspect_diagnostics(str(project_dir))
            output = legacy.format_legacy_inspect_output(diagnostics)

        self.assertNotIn("abc123", output)
        self.assertNotIn("cat secret.txt", output)
        self.assertIn("API_TOKEN=<redacted>", output)


class GatherLegacyMigrateDiagnosticsTest(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir)

            diagnostics = legacy.gather_legacy_migrate_diagnostics(
                str(project_dir), apply=False
            )

        self.assertTrue(diagnostics["ok"])
        self.assertFalse(diagnostics["config_written"])
        self.assertFalse((project_dir / ".taurworks").exists())
        self.assertTrue(len(diagnostics["applied"]) > 0)

    def test_apply_writes_unambiguous_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir)
            (project_dir / "repo").mkdir()

            diagnostics = legacy.gather_legacy_migrate_diagnostics(
                str(project_dir), apply=True
            )

            config = project_internals.read_project_config(project_dir)

        self.assertTrue(diagnostics["ok"])
        self.assertTrue(diagnostics["config_written"])
        self.assertEqual(config["activation"]["environment"]["name"], "ExampleEnv")
        self.assertEqual(config["activation"]["exports"]["API_TOKEN"], "abc123")
        self.assertEqual(
            config["activation"]["message"], "Ready for work on ExampleProject"
        )
        self.assertEqual(config["paths"]["working_dir"], "repo")

    def test_apply_preserves_existing_config_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir)
            (project_dir / ".taurworks").mkdir()
            project_internals.write_project_config(
                project_dir,
                {
                    "schema_version": 1,
                    "project": {"name": "LegacyProject"},
                    "activation": {
                        "environment": {"type": "conda", "name": "PreExisting"}
                    },
                },
            )

            diagnostics = legacy.gather_legacy_migrate_diagnostics(
                str(project_dir), apply=True
            )

            config = project_internals.read_project_config(project_dir)

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(config["activation"]["environment"]["name"], "PreExisting")
        self.assertTrue(
            any("already configured" in note for note in diagnostics["skipped"])
        )

    def test_ambiguous_duplicate_export_is_flagged_and_not_applied(self):
        script = "export DUPLICATE=one\nexport DUPLICATE=two\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir, script)

            diagnostics = legacy.gather_legacy_migrate_diagnostics(
                str(project_dir), apply=True
            )

        self.assertTrue(diagnostics["ok"])
        self.assertFalse(diagnostics["config_written"])
        self.assertTrue(
            any("ambiguous" in note for note in diagnostics["manual_review"])
        )

    def test_cd_target_outside_project_root_requires_manual_review(self):
        script = "cd ../outside\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir, script)

            diagnostics = legacy.gather_legacy_migrate_diagnostics(
                str(project_dir), apply=True
            )

        self.assertTrue(diagnostics["ok"])
        self.assertFalse(diagnostics["config_written"])
        self.assertTrue(len(diagnostics["manual_review"]) > 0)

    def test_no_unambiguous_matches_reports_no_change(self):
        script = "export DYNAMIC=$(date)\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = pathlib.Path(temp_dir) / "LegacyProject"
            _write_legacy_script(project_dir, script)

            diagnostics = legacy.gather_legacy_migrate_diagnostics(
                str(project_dir), apply=True
            )

        self.assertTrue(diagnostics["ok"])
        self.assertFalse(diagnostics["config_written"])
        self.assertIn("nothing would change", diagnostics["message"])


if __name__ == "__main__":
    unittest.main()
