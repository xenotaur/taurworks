---
execution_id: 2026_07_23_03_34_42_CLOSE_OUT_LEGACY_EXECUTION_RECORDS
prompt_id: PROMPT(AD_HOC:CLOSE_OUT_LEGACY_EXECUTION_RECORDS)[2026-07-23T03:34:21-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/82
commit: 
created_at: 2026-07-23T03:34:42-04:00
agent: claude_app
instruction_source: ad_hoc conversation — user asked to close out the April/May execution-record backlog identified while auditing session status ("option 2": mark records landed and fix the stale README causing the drift)
session_transcript: pending
---

# Summary

Close out four pre-`lrh`-CLI `AD_HOC` execution records (2026-04-30 through
2026-05-15) identified as stale during a session-status audit, and fix
`project/executions/README.md`, which still documented the superseded
`scripts/prompts/*` tooling as the primary path — the root cause of why
nobody translated these records when the `lrh` CLI took over.

# Result

- Read all four records in full and verified their described work is
  actually present in the current codebase (test layout under
  `tests/smoke/`, `constraints-dev.txt` + `scripts/develop` CI alignment,
  the `setuptools_major >= 64` backend-bootstrap check in `scripts/develop`,
  and the global-config/registry/activation design whose follow-ups shipped
  via `WI-UNIFIED-COMMAND-MODEL-0001`, `WI-ACTIVATION-CONFIG-0001`, and
  `WI-TRUSTED-LEGACY-SOURCING-0001`).
- Flipped `status` from `in_progress` to `landed` in all four, and appended
  a short "Closed out retroactively on 2026-07-23" note to each explaining
  why it was never closed sooner and pointing at the refreshed README.
- Rewrote `project/executions/README.md`: documents `lrh prompt
  label`/`record-execution`/`check-execution`/`update-execution` as the
  primary workflow, the current schema
  (`execution_id`/`prompt_id`/`work_item`/`status`/`rerun_of`/`pr`/`commit`/`created_at`/`agent`/`instruction_source`/`session_transcript`)
  and filename convention
  (`<YYYY_MM_DD_HH_MM_SS>_<SLUG_UPPER_UNDERSCORE>.md`), and the full
  `status` enum confirmed via `lrh prompt record-execution --help`
  (`planned`/`in_progress`/`landed`/`failed`/`reverted`/`superseded`). Added
  a "Legacy records" section explaining the old schema/tooling explicitly,
  so this class of drift is easier to recognize next time rather than
  silently recurring.

**Process note:** mid-task, discovered the Bash tool's default working
directory (`.claude/worktrees/intelligent-einstein-81d3f9`) differs from
the worktree my file-editing tools were operating in
(`.claude/worktrees/vigorous-heyrovsky-6935a9`), which turned out to be
checked out to `claude/legacy-migrate-tl-fallback-6a92f3` — a different,
concurrent session's branch. My edits had landed there uncommitted. Moved
them off that branch via a scoped `git stash push -u -- <5 files>` (stashes
are shared across worktrees of the same repo) and popped the stash in the
correct worktree/branch, leaving the concurrent session's checkout
undisturbed. Confirmed via `git status --short` in both worktrees before
and after.

# Validation

- `lrh validate` — 4 errors, 0 warnings; identical pre-existing
  `contributors.md` baseline, no new errors
- Docs/execution-records-only change; no Python files touched, so
  `scripts/format`/`lint`/`test` were not run (consistent with how the
  similar docs-only PR #80 was validated)
- Manually confirmed each of the four records' described work is still
  present in the current codebase (see Result above) before marking them
  landed, rather than assuming from the record text alone

# Follow-up

- `session_transcript` is `pending`; update to `claude-app:<session-id>`
  once the session ID is known.
- No further action needed on these four records — they're now closed out
  and the README fix should prevent recurrence. If more pre-`lrh`-schema
  records turn up elsewhere, the same "verify work landed, flip status,
  note why it was late" pattern applies.
