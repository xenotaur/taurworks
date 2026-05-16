---
prompt_id: "PROMPT(TAURWORKS_PROJECT_CREATE_WORKSPACE_DEFAULT)[IMPLEMENT/2026-05-16]"
work_item: "AD_HOC"
slug: "taurworks-project-create-workspace-default"
status: "landed"
date: "2026-05-16"
---

# Summary
Implemented workspace-root default target semantics for `taurworks project create NAME`, plus explicit `--local` and `--path PATH` create modes.

# Result
- Bare `project create NAME` now resolves to the configured XDG global workspace root and fails clearly when no workspace root is configured.
- `project create NAME --local` preserves cwd-relative creation as an explicit opt-in.
- `project create NAME --path PATH` creates at an explicit target path and validates that `PATH` basename matches `NAME`.
- Create output reports target selection, workspace root source, path arguments, and out-of-workspace warnings.
- README documentation and CLI/unit/shell-helper tests were updated for the new semantics.

# Validation
- Passed: `python -m unittest tests.cli_test.CliCommandTest.test_project_create_bare_name_defaults_to_configured_workspace tests.cli_test.CliCommandTest.test_project_create_workspace_default_creates_working_dir_under_workspace tests.cli_test.CliCommandTest.test_project_create_local_creates_under_cwd tests.cli_test.CliCommandTest.test_project_create_explicit_path_creates_at_path_and_warns_outside_workspace tests.cli_test.CliCommandTest.test_project_create_local_and_path_are_mutually_exclusive tests.cli_test.CliCommandTest.test_project_create_no_configured_workspace_requires_explicit_target tests.cli_test.CliCommandTest.test_project_create_path_does_not_ignore_name tests.cli_test.CliCommandTest.test_project_create_with_create_working_dir_creates_and_records_it tests.cli_test.CliCommandTest.test_project_create_nested_allows_same_name_child`
- Passed: `./scripts/test`
- Passed: `./scripts/lint`
- Passed: `./scripts/format --check --diff`
- Warning: `python -m pip install -e .` attempted but build isolation dependency download failed because the environment returned `Tunnel connection failed: 403 Forbidden` for `setuptools>=64`.
- Passed: manual workspace/local/path create validation with temporary `XDG_CONFIG_HOME`, including `taurworks projects`, `taurworks project activate Alpha --print`, and sourced `tw activate Alpha`.
- Warning: `scripts/prompts/record-execution` was requested but is not present in this checkout, so this record was created manually following `project/executions/README.md`.

# Follow-up
None.
