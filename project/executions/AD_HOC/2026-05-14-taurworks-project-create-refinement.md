---
prompt_id: "PROMPT(TAURWORKS_PROJECT_CREATE_REFINEMENT)[IMPLEMENT/2026-05-13]"
work_item: "AD_HOC"
slug: "taurworks-project-create-refinement"
status: "landed"
date: "2026-05-14"
---

# Summary
Implemented the project-create refinement prompt so `taurworks project create NAME` means creating a new project root before initialization-style metadata scaffolding, while preserving no-argument create as a compatibility alias for `project init`.

# Result
- Added `project create --create-working-dir` to explicitly create missing working-directory targets only after safe project-root-relative validation.
- Added `project create --nested` to require explicit opt-in for nested same-name projects.
- Added same-name nested protection when the current project name or current directory basename matches the requested bare `NAME`.
- Updated CLI help, README documentation, and create-focused CLI tests.

# Validation
- Passed: `python -m unittest tests.cli_test -v`.
- Warning: `python -m unittest -v` and `python -m unittest discover -v` ran zero tests because this repository's test files use the `*_test.py` pattern.
- Passed: `python -m unittest discover -s tests -p '*_test.py' -v`.
- Passed: `python -m black src/taurworks/cli.py src/taurworks/project_resolution.py tests/cli_test.py`.
- Passed: `python -m ruff check src/taurworks/cli.py src/taurworks/project_resolution.py tests/cli_test.py`.
- Warning: `python -m pip install -e .` failed because isolated build dependency download for setuptools was blocked by the environment (`Tunnel connection failed: 403 Forbidden`).
- Passed: `python -m pip install -e . --no-build-isolation`.
- Passed: dogfood flow `rm -rf /tmp/taurworks-create-demo && mkdir -p /tmp/taurworks-create-demo && cd /tmp/taurworks-create-demo && taurworks project create TestProject --working-dir test_repo --create-working-dir && taurworks project activate TestProject --print && cd TestProject && if taurworks project create TestProject; then echo 'UNEXPECTED_SUCCESS'; exit 1; else echo 'EXPECTED_CREATE_FAILURE'; fi && taurworks project create TestProject --nested`.
- Warning: `python -m black --check . && python -m ruff check .` was blocked by pre-existing legacy Python 2 syntax and formatting issues in `bin/`.
- Passed: `python -m black --check src/taurworks/cli.py src/taurworks/project_resolution.py tests/cli_test.py && python -m ruff check src/taurworks/cli.py src/taurworks/project_resolution.py tests/cli_test.py`.
- Warning: `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_CREATE_REFINEMENT)[IMPLEMENT/2026-05-13]" --work-item AD_HOC --slug taurworks-project-create-refinement --status landed` failed because the script is not present in this checkout; this record was created manually following `project/executions/README.md`.

# Follow-up
None.
