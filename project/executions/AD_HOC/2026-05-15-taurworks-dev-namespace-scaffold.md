---
prompt_id: "PROMPT(TAURWORKS_DEV_NAMESPACE_SCAFFOLD)[IMPLEMENT/2026-05-14]"
work_item: "AD_HOC"
slug: "taurworks-dev-namespace-scaffold"
status: "landed"
date: "2026-05-15"
---

# Summary
Implemented a focused minimal `taurworks dev ...` namespace scaffold for read-only repository/developer workflow diagnostics.

# Result
- Added `taurworks dev --help`, `taurworks dev where`, and `taurworks dev status`.
- `dev where` reports cwd, detected Taurworks project root, configured working directory, work-directory guess, whether cwd is inside the configured working directory, and no-mutation status.
- `dev status` reports a smaller read-only summary and explicitly leaves detailed VCS workflow automation for future work.
- Updated README/status/roadmap documentation to describe the implemented minimal read-only scaffold and keep broad workflow automation deferred.
- Added CLI and shell-helper delegation tests covering the new namespace.

# Validation
- Passed: `./scripts/develop`.
- Passed: `taurworks dev --help`.
- Passed: `taurworks dev where`.
- Passed: `taurworks dev status`.
- Passed: `taurworks shell print > /tmp/taurworks-shell.sh && bash -c 'source /tmp/taurworks-shell.sh && tw dev where'`.
- Passed: `./scripts/lint`.
- Passed: `./scripts/test`.
- Blocked: `python -m pip install -e .` attempted, but build-isolation dependency fetch for `setuptools>=64` failed behind a 403 network/proxy limitation. The repository's documented constrained setup path, `./scripts/develop`, succeeded.
- Note: `scripts/prompts/record-execution` was requested but is not present in this checkout, so this record was created manually following `project/executions/README.md`.

# Follow-up
- Add real `taurworks dev` workflow commands only in later, separately reviewed slices after trust and automation boundaries are designed.
