---
execution_id: 2026_07_22_22_20_36_WI_LEGACY_MIGRATE_TL_FALLBACK_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LEGACY_MIGRATE_TL_FALLBACK_0001_REVIEW)[2026-07-22T22:16:05-04:00]
work_item: AD_HOC
status: landed
rerun_of: null
pr: https://github.com/xenotaur/taurworks/pull/79
commit: 67b4e485e9246a5486a09254698b7d8e0cffc14e
created_at: 2026-07-22T22:20:36-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/79
session_transcript: claude-app:146d1a52-87d7-4028-97f7-b7118179f5d8
---

# Summary

Addressed automated code-review feedback (`copilot-pull-request-reviewer`,
`chatgpt-codex-connector`) on PR #79, which created the planning work item
`WI-LEGACY-MIGRATE-TL-FALLBACK-0001` (no primary execution record exists —
`/lrh-work-item` doesn't create one — so `rerun_of` is left empty). Notably,
another session is concurrently implementing this WI on a separate branch
(`claude/legacy-migrate-tl-fallback-6a92f3`); verified before touching
anything that PR #79's remote `HEAD` still matched exactly what this
session pushed when the WI was created (`f28d52a`), confirming the other
session has not touched this branch.

# Result

All 4 review comments were real, presence-confirmed, valid, and feasible to
fix — none skipped. Two (comments 2 and 3) identified genuine design flaws
in the WI's spec, not just wording issues, so the fix required substantially
reworking Required Changes, Scope, Acceptance Criteria, and Risk Notes
rather than a small edit:

1. **Project count/list mismatch (`copilot-pull-request-reviewer`)**: "10
   real projects" named 12. Recounted: 11 projects actually fit the
   "redundant `Admin/` script" pattern this WI addresses; `Taurworks` was a
   distinct bug (case-mismatch in an already-migrated `tl` companion, no
   `Admin/` script involved) and doesn't belong in this specific list.
   Fixed the count and removed `Taurworks` from the list, with a one-line
   note explaining why.
2. **[P1] Require complete merge coverage, not just `unsupported_count == 0`
   (`chatgpt-codex-connector`)**: verified against
   `src/taurworks/legacy.py:293-441` directly — duplicate/conflicting lines
   (e.g. two `conda activate` statements, or an export conflicting with an
   already-configured value) are diverted into `manual_review`/`skipped`
   during merging without ever incrementing `unsupported_count`. The WI's
   original gate would have let a genuinely incomplete migration retire
   silently. Reworked the completeness check to require `manual_review`
   empty and every `skipped` entry's existing value verified equal to what
   the legacy line would have set.
3. **[P2] Allow retirement after an earlier config-only migration
   (`chatgpt-codex-connector`)**: verified `gather_legacy_migrate_diagnostics`
   returns early at `legacy.py:478-482` whenever `merge_result["patch"]` is
   empty — exactly the state after a prior config-only migration (today's
   existing default path), meaning the original design (gated after
   `config_written = True`) could never retire on the single most likely
   real-world sequence. Restructured to make retirement its own
   independently-reachable step.
4. **[P1] Refuse to overwrite an existing `tl` fallback
   (`chatgpt-codex-connector`)**: confirmed via
   `WI-ACTIVATION-PRODUCERS-0001:46-50` that legacy `create`/`refresh`
   historically wrote `.taurworks/project-setup.source` directly, before
   that WI converged them onto `config.toml` — so a pre-existing, unrelated
   file can legitimately already be at the destination. Added a
   require-absent-or-byte-identical guard, failing safely otherwise.

Added 3 new required test cases (duplicate/conflict, rerun-after-earlier-
migration, destination-collision) alongside the original 3, and expanded
Risk Notes to flag the subtlety of the completeness check and the need for
the collision guard to compare content, not just existence.

**Important for the concurrently-implementing session:** this pushes a
substantially reworked spec for a WI another session may already be
implementing against the old version — worth surfacing to that session or
re-reading the WI file fresh before continuing.

# Validation

- `gh pr view 79 --json headRefName,headRefOid,state` +
  `git rev-parse HEAD` — branch and SHA both matched before any changes;
  remote `HEAD` also confirmed unchanged since WI creation, ruling out a
  concurrent-edit collision.
- `scripts/format --check --diff` — clean (28 files unchanged); docs-only
  change, no Python files touched.
- `scripts/lint` — black + ruff both clean.
- `lrh validate` — 4 pre-existing `contributors.md` errors only (unrelated,
  documented pre-existing gap); no new errors introduced.
- `scripts/test` not run — docs-only change with no runtime surface yet
  (this PR contains only the planning WI, not the implementation).

# Follow-up

- `session_transcript` should be updated from `pending` to
  `claude-app:<session-id>` after this session ends.
- Recommend running `/lrh-confirm-fixes https://github.com/xenotaur/taurworks/pull/79`
  before merge to verify these fixes against the current diff and resolve
  the review threads.
- Flag to the user: the other session implementing this WI should be made
  aware of the reworked spec (Required Changes 1-3 in particular are now
  substantially different from what existed when that session may have
  started).
