---
execution_id: 2026_07_15_22_19_02_WI_ACTIVATION_PRODUCERS_0001
prompt_id: PROMPT(WI-ACTIVATION-PRODUCERS-0001:WI_ACTIVATION_PRODUCERS_0001)[2026-07-15T20:57:56-04:00]
work_item: WI-ACTIVATION-PRODUCERS-0001
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/69
commit: 7d8e777
created_at: 2026-07-15T22:19:02-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-ACTIVATION-PRODUCERS-0001.md
session_transcript: claude-app:149f0939-369e-4d12-afa5-29a079bb476f
---

# Summary

Implement WI-ACTIVATION-PRODUCERS-0001: the producer side of declarative
activation — a CLI writer for `[activation.environment]`, `--env` on
project create/init, convergence of legacy create/refresh onto
`config.toml`, and three guidance-string fixes — so a fresh user can reach
Conda-switching `tw activate` using only shipped commands.

# Result

1. `project_internals.set_activation_environment` plus
   `taurworks project env set ENV_NAME [--project PATH_OR_NAME]` /
   `taurworks project env show [PATH_OR_NAME]`, mirroring the existing
   `project working-dir set/show` pattern exactly (validated Conda name,
   safe writer, never silently overwrites — only an explicit `set` changes
   an existing value).
2. `--env NAME` added to `project create` and `project init`, applied via a
   new `_apply_env_to_diagnostics` helper following the same shape as the
   existing `--working-dir` handling, including on failure paths (env
   fields correctly report "not evaluated because an earlier step failed"
   rather than being silently dropped — verified live).
3. `manager.refresh_project`/`create_project` converged onto writing
   `.taurworks/config.toml` (environment + working_dir) via the safe
   writer, replacing the `.taurworks/project-setup.source` script that
   `tw activate` never read. Existing config values are never overwritten.
   The "fully set up"/"created successfully" message now distinguishes
   whether a Conda environment was actually created.
4. Three guidance strings fixed: legacy-admin activation names
   `taurworks legacy migrate NAME --apply`; workspace-only activation
   names `taurworks project init NAME`; an initialized project with no
   `[activation.environment]` names `taurworks project env set` — and this
   is now surfaced by `tw activate` itself (a new shell `note:` line via a
   broadened existing guidance-display condition), not just `--print`.
5. 20 new tests across `project_internals_test.py`,
   `project_resolution_test.py`, `manager_test.py`, `shell_helper_test.py`,
   `cli_test.py`.

Side effect: this PR's manager.py rewrite happens to delete exactly the
code region that was failing `black --check` on `origin/master` (flagged
during PR #68 review), so `manager.py` is now black-clean without a
separate formatting-only change.

Acceptance criterion verified live (real conda, no manual config editing):
`taurworks project create X --local --env base --working-dir x_repo
--create-working-dir` then `tw activate X` switched `$CONDA_DEFAULT_ENV`
from a starting env to `base` and cd'd to `x_repo`. Also covered by an
automated subprocess test using a fake `conda` stub (matching the repo's
existing convention for shell-level Conda tests).

# Validation

- Python 3.11.8, black 26.3.1, ruff 0.15.12
- `scripts/format --check --diff` — 27 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 228 tests OK (208 prior + 20 new)
- `lrh validate` — no new errors (4 known pre-existing `contributors.md`
  errors remain)
- Manual live-shell verification of the fresh-user end-to-end acceptance
  criterion with real conda

# Follow-up

- On merge: closeout via /lrh-closeout (mark this record landed, resolve
  the work item).
- A separately started background task was fixing the same pre-existing
  `manager.py` black nonconformance; if it produces its own PR after this
  one merges, it should be a no-op on `manager.py` and can likely be
  dismissed.
- Next plan step: WI-TRUSTED-LEGACY-SOURCING-0001, sized by the
  WI-LEGACY-BATCH-MIGRATION-0001 finding that all 11 legacy projects
  source `~/bin/utilities.source`.
