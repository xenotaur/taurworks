---
execution_id: 2026_07_14_00_43_50_WI_LEGACY_BATCH_MIGRATION_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LEGACY_BATCH_MIGRATION_0001_REVIEW)[2026-07-14T00:34:23-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_13_22_13_52_WI_LEGACY_BATCH_MIGRATION_0001
pr: https://github.com/xenotaur/taurworks/pull/68
commit: 4e1dd07
created_at: 2026-07-14T00:43:50-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/68
session_transcript: claude-app:149f0939-369e-4d12-afa5-29a079bb476f
---

# Summary

Address two Codex P2 review comments on PR #68 (legacy batch migrator),
both in `bin/migrate_legacy_projects.py`.

# Result

Both comments valid and fixed (commit 4e1dd07):

1. **Preserve shell quoting (correctness).** The preprocessor expanded
   `$VAR` references regardless of quoting, so `cd '$WORKSPACE'` would be
   rewritten to `cd 'repo'` and could migrate behavior the original script
   never had (single quotes suppress expansion in the shell). Fixed by
   refusing any single-quoted assignment value in `_resolve_value` and
   passing any single-quoted rewritable line through raw in
   `preprocess_script`, so the existing shlex-based parser handles quoting
   correctly (and marks `cd '$WORKSPACE'` manual-review). None of the 11 real
   scripts single-quote their references, so no applied migration changes;
   this only tightens safety for the general case the reviewer raised.

2. **Accept the documented `--dry-run` flag.** The WI validation path
   documents `python bin/migrate_legacy_projects.py --dry-run`, but only
   `--apply` was defined, so argparse exited with "unrecognized arguments".
   Added `--dry-run` as a no-op flag affirming the default, in a mutually
   exclusive group with `--apply`.

Added four regression tests (single-quote non-expansion for both a rewritable
line and an assignment value; `--dry-run` accepted; `--dry-run`/`--apply`
mutually exclusive). Nothing was skipped.

# Validation

- Python 3.11, black 26.3.1, ruff 0.15.12
- black + ruff clean on both changed files
- `scripts/test` — 208 tests OK (204 prior + 4 new)
- `lrh validate` — no new errors (4 known pre-existing `contributors.md`)
- `python bin/migrate_legacy_projects.py --dry-run` now runs instead of
  erroring

# Follow-up

- No re-apply needed: the fix does not change output for any of the 11
  already-migrated projects (none use single quotes).
- On merge: closeout via /lrh-closeout (mark this record and the primary
  record landed, resolve WI-LEGACY-BATCH-MIGRATION-0001).
