import importlib.util
import pathlib
import tempfile
import unittest

from taurworks import project_internals

# bin/ is not an importable package, so load the one-time migration script by
# path. Its module name has no hyphen, so this is a clean spec-based import.
_MIGRATE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "bin"
    / "migrate_legacy_projects.py"
)
_spec = importlib.util.spec_from_file_location("migrate_legacy_projects", _MIGRATE_PATH)
assert _spec is not None and _spec.loader is not None
migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate)

HOME = pathlib.Path("/home/tester")

STANDARD_TEMPLATE = """#!/bin/bash
source ~/bin/utilities.source

WORKSPACE=~/Workspace/Demo/demo_repo
ENVIRONMENT=DemoEnv
PROJECT=Demo

conda activate $ENVIRONMENT
cd $WORKSPACE
echo "Ready for work on project $PROJECT"
echo
"""


class BuildSymbolTableTest(unittest.TestCase):
    def test_resolves_tilde_and_chained_references(self):
        text = "BASE=~/Workspace\nSUB=$BASE/Demo\nENVIRONMENT=DemoEnv\n"
        symbols = migrate.build_symbol_table(text, HOME)
        self.assertEqual(symbols["BASE"], "/home/tester/Workspace")
        self.assertEqual(symbols["SUB"], "/home/tester/Workspace/Demo")
        self.assertEqual(symbols["ENVIRONMENT"], "DemoEnv")

    def test_rejects_command_substitution_value(self):
        text = "CREDS=$(realpath ~/key.pem)\n"
        symbols = migrate.build_symbol_table(text, HOME)
        self.assertNotIn("CREDS", symbols)

    def test_rejects_reference_to_unknown_variable(self):
        text = "DERIVED=$UNKNOWN/child\n"
        symbols = migrate.build_symbol_table(text, HOME)
        self.assertNotIn("DERIVED", symbols)

    def test_ignores_export_assignments(self):
        text = "export NODE_OPTIONS=--max-old-space-size=8192\n"
        symbols = migrate.build_symbol_table(text, HOME)
        self.assertNotIn("NODE_OPTIONS", symbols)


class PreprocessScriptTest(unittest.TestCase):
    def test_resolves_conda_cd_and_message(self):
        normalized = migrate.preprocess_script(STANDARD_TEMPLATE, HOME)
        self.assertIn("conda activate DemoEnv", normalized)
        self.assertIn("cd /home/tester/Workspace/Demo/demo_repo", normalized)
        # Quotes are preserved here; the downstream parser strips them via shlex.
        self.assertIn('echo "Ready for work on project Demo"', normalized)

    def test_drops_consumed_assignments(self):
        normalized = migrate.preprocess_script(STANDARD_TEMPLATE, HOME)
        self.assertNotIn("WORKSPACE=", normalized)
        self.assertNotIn("ENVIRONMENT=", normalized)

    def test_passes_source_line_through_untouched(self):
        normalized = migrate.preprocess_script(STANDARD_TEMPLATE, HOME)
        self.assertIn("source ~/bin/utilities.source", normalized)

    def test_leaves_command_substitution_export_untouched(self):
        text = "export CREDENTIALS=$(realpath ~/key.pem)\nconda activate Env\n"
        normalized = migrate.preprocess_script(text, HOME)
        self.assertIn("export CREDENTIALS=$(realpath ~/key.pem)", normalized)

    def test_does_not_expand_inside_single_quotes(self):
        # Single quotes suppress shell expansion; the preprocessor must not
        # resolve the reference or record the symbol, so the cd line passes
        # through verbatim for the downstream parser to mark manual-review.
        text = "WORKSPACE=repo\ncd '$WORKSPACE'\n"
        symbols = migrate.build_symbol_table(text, HOME)
        self.assertEqual(symbols.get("WORKSPACE"), "repo")
        normalized = migrate.preprocess_script(text, HOME)
        self.assertIn("cd '$WORKSPACE'", normalized)
        self.assertNotIn("cd 'repo'", normalized)

    def test_single_quoted_assignment_value_is_not_resolved(self):
        text = "TARGET='$OTHER'\nconda activate $TARGET\n"
        symbols = migrate.build_symbol_table(text, HOME)
        self.assertNotIn("TARGET", symbols)
        normalized = migrate.preprocess_script(text, HOME)
        self.assertIn("conda activate $TARGET", normalized)


class CliFlagTest(unittest.TestCase):
    def test_dry_run_flag_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # An empty workspace: no legacy projects, exit 0, no writes.
            code = migrate.main(["--dry-run", "--workspace", tmp_dir])
            self.assertEqual(code, 0)

    def test_dry_run_and_apply_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            migrate.main(["--dry-run", "--apply", "--workspace", "/tmp"])


class PlanProjectTest(unittest.TestCase):
    def _make_project(self, tmp: pathlib.Path, script: str) -> pathlib.Path:
        project_root = tmp / "Demo"
        (project_root / "Admin").mkdir(parents=True)
        (project_root / "demo_repo").mkdir(parents=True)
        (project_root / "Admin" / "project-setup.source").write_text(
            script, encoding="utf-8"
        )
        return project_root

    def test_plan_produces_expected_patch(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            script = (
                "#!/bin/bash\n"
                f"WORKSPACE={tmp}/Demo/demo_repo\n"
                "ENVIRONMENT=DemoEnv\n"
                "PROJECT=Demo\n"
                "conda activate $ENVIRONMENT\n"
                "cd $WORKSPACE\n"
                'echo "Ready for work on project $PROJECT"\n'
            )
            project_root = self._make_project(tmp, script)
            plan = migrate.plan_project(project_root, HOME)
            patch = plan["patch"]
            self.assertEqual(
                patch["activation"]["environment"],
                {"type": "conda", "name": "DemoEnv"},
            )
            self.assertEqual(
                patch["activation"]["message"], "Ready for work on project Demo"
            )
            self.assertEqual(patch["paths"]["working_dir"], "demo_repo")

    def test_existing_config_value_is_preserved_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            script = (
                "#!/bin/bash\n"
                f"WORKSPACE={tmp}/Demo/demo_repo\n"
                "ENVIRONMENT=NewEnv\n"
                "conda activate $ENVIRONMENT\n"
                "cd $WORKSPACE\n"
            )
            project_root = self._make_project(tmp, script)
            (project_root / ".taurworks").mkdir(parents=True, exist_ok=True)
            project_internals.write_project_config(
                project_root,
                {
                    "schema_version": 1,
                    "project": {"name": "Demo"},
                    "activation": {"environment": {"type": "conda", "name": "OldEnv"}},
                },
            )
            plan = migrate.plan_project(project_root, HOME)
            # The pre-existing environment name must not be overwritten.
            self.assertNotIn("environment", plan["patch"].get("activation", {}))
            self.assertTrue(
                any("already configured" in note for note in plan["skipped"])
            )
            # working_dir is still newly added.
            self.assertEqual(plan["patch"]["paths"]["working_dir"], "demo_repo")

    def test_apply_writes_config_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            script = (
                "#!/bin/bash\n"
                f"WORKSPACE={tmp}/Demo/demo_repo\n"
                "ENVIRONMENT=DemoEnv\n"
                "conda activate $ENVIRONMENT\n"
                "cd $WORKSPACE\n"
            )
            project_root = self._make_project(tmp, script)
            plan = migrate.plan_project(project_root, HOME)
            migrate.apply_plan(plan)
            config = project_internals.read_project_config(project_root)
            self.assertEqual(config["activation"]["environment"]["name"], "DemoEnv")
            self.assertEqual(config["paths"]["working_dir"], "demo_repo")

            # Re-running must not change or duplicate anything.
            first = project_internals.project_config_path(project_root).read_text(
                encoding="utf-8"
            )
            replan = migrate.plan_project(project_root, HOME)
            migrate.apply_plan(replan)
            second = project_internals.project_config_path(project_root).read_text(
                encoding="utf-8"
            )
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
