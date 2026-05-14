---
prompt_id: "PROMPT(TAURWORKS_PROJECT_RESOLVER_CLI_CONSISTENCY)[IMPLEMENT/2026-05-13]"
work_item: "AD_HOC"
slug: "taurworks-project-resolver-cli-consistency"
status: "landed"
date: "2026-05-14"
---

# Summary
Implemented shared project target resolution semantics for read-only project commands and fixed dogfood CLI consistency issues for `working-dir show [PATH_OR_NAME]` and same-name `activate --print` resolution.

# Result
- Added inspectable project target resolution with stable `resolved_by` reasons.
- Updated `taurworks project working-dir show [PATH_OR_NAME]` to resolve optional project targets and report resolver diagnostics.
- Updated `taurworks project activate [PATH_OR_NAME] --print` to use the shared resolver so a current project name resolves to the current project root.
- Updated README documentation for target-aware working-directory display and shared resolver behavior.
- Added tests for resolver reasons, parent-directory `working-dir show`, current-project `working-dir show`, same-name activation, unknown-name safety, read-only non-mutation, same-name child resolution, and path-only refresh/create preservation.
- Review follow-up preserved path-only refresh/create target behavior and made current project-name resolution win before accidental same-name child paths for read-only resolver callers.

# Validation
- Passed: `python -m unittest tests.project_internals_test -v`
- Passed: `python -m unittest tests.cli_test -v`
- Passed: `./scripts/format`
- Passed: `./scripts/lint`
- Passed: `./scripts/test`
- Review follow-up passed: `scripts/format --check --diff`
- Review follow-up passed: `scripts/lint`
- Review follow-up passed: `scripts/test`
- Review follow-up note: `scripts/version tools` could not run because `scripts/version` is not present in this checkout.
- Blocked by environment/network: `python -m pip install -e .` failed because build-isolation dependency download for `setuptools>=64` returned proxy `403 Forbidden`.
- Passed workaround using repository standard setup: `./scripts/develop`
- Passed dogfood flow after repository setup: `rm -rf /tmp/taurworks-resolver-demo && mkdir -p /tmp/taurworks-resolver-demo/TestProject/test_repo && cd /tmp/taurworks-resolver-demo && taurworks project create TestProject --working-dir test_repo && taurworks project working-dir show TestProject && cd TestProject && taurworks project activate TestProject --print`
- Execution helper unavailable: `scripts/prompts/record-execution --help` failed because the script is not present in this checkout, so this record was created manually following `project/executions/README.md`.

# Follow-up
None.
