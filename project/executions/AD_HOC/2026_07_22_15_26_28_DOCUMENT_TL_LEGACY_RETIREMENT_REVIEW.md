---
execution_id: 2026_07_22_15_26_28_DOCUMENT_TL_LEGACY_RETIREMENT_REVIEW
prompt_id: PROMPT(AD_HOC:DOCUMENT_TL_LEGACY_RETIREMENT_REVIEW)[2026-07-22T15:19:53-04:00]
work_item: AD_HOC
status: landed
rerun_of: null
pr: https://github.com/xenotaur/taurworks/pull/78
commit: 2567cf58c82ca3574919138de748a01848f815ba
created_at: 2026-07-22T15:26:28-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/78
session_transcript: claude-app:146d1a52-87d7-4028-97f7-b7118179f5d8
---

# Summary

Addressed automated code-review feedback (`chatgpt-codex-connector`) on
PR #78, which documents the `tl`-compatible retirement recipe for migrated
legacy scripts in `README.md`. No primary execution record exists for this
branch — the PR was created ad-hoc, intentionally skipping `/lrh-implement`
per the user's explicit request to avoid work-item ceremony for a one-off
doc addition — so `rerun_of` is left empty.

# Result

Both review comments were real, presence-confirmed, valid, and feasible to
fix — none skipped:

1. **Revoke legacy trust when retiring the script**
   (`chatgpt-codex-connector`): the original recipe never mentioned
   `taurworks project trust unset NAME`. A trust record's digest is keyed
   on content, not path, and lives in user-global config
   (`~/.config/taurworks/config.toml`), untouched by moving the project
   file. If `Admin/project-setup.source` is ever restored with identical
   content (e.g. a `git checkout`/`reset`), a lingering trust record
   matches again and `tw activate` silently re-sources it, recreating the
   exact duplication the recipe exists to prevent. Added `trust unset` to
   the retirement steps.
2. **Account for scripts whose behavior depends on their path**
   (`chatgpt-codex-connector`): the recipe's "`tl` keeps working unchanged"
   claim doesn't hold for scripts using `${BASH_SOURCE[0]}`/`$0` to resolve
   their own directory (e.g. to source an adjacent file) — moving from
   `Admin/` to `.taurworks/` changes that context. None of the 10 real
   scripts moved earlier this session used this pattern (all used
   absolute/`~`-based sourcing), so no live bug was hit, but the recipe now
   explicitly calls out checking for this before moving.

Self-caught while fixing comment 1: my first draft claimed
`taurworks project trust unset` is a clean no-op on a never-trusted
project. Checked against `src/taurworks/cli.py:198-199` —
`if not diagnostics["ok"]: raise SystemExit(1)` — it actually exits
non-zero (with a harmless, informative "not trusted; nothing to do"
message). Corrected the wording before committing rather than leaving an
inaccurate claim in the docs.

# Validation

- `gh pr view 78 --json headRefName,headRefOid,state` +
  `git rev-parse HEAD` / `git branch --show-current` — branch and SHA both
  matched before any changes.
- `scripts/format --check --diff` — clean (28 files unchanged); docs-only
  change, no Python files touched.
- `scripts/lint` — black + ruff both clean.
- `lrh validate` — 4 pre-existing `contributors.md` errors only (unrelated,
  documented pre-existing gap); no new errors introduced.
- `scripts/test` not run — docs-only change with no runtime surface.

# Follow-up

- `session_transcript` should be updated from `pending` to
  `claude-app:<session-id>` after this session ends.
- Recommend running `/lrh-confirm-fixes https://github.com/xenotaur/taurworks/pull/78`
  before merge to verify these fixes against the current diff and resolve
  the review threads.
