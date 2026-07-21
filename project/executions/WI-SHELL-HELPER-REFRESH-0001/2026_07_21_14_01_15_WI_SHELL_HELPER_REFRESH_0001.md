---
execution_id: 2026_07_21_14_01_15_WI_SHELL_HELPER_REFRESH_0001
prompt_id: PROMPT(WI-SHELL-HELPER-REFRESH-0001:WI_SHELL_HELPER_REFRESH_0001)[2026-07-21T13:14:04-04:00]
work_item: WI-SHELL-HELPER-REFRESH-0001
status: in_progress
rerun_of: null
pr: https://github.com/xenotaur/taurworks/pull/76
commit: 5a77190b4aafff5b59608524a373b4c7861ee254
created_at: 2026-07-21T14:01:15-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SHELL-HELPER-REFRESH-0001.md
session_transcript: pending
---

# Summary

Implemented `WI-SHELL-HELPER-REFRESH-0001` (Phase 1 of
`project/design/shell_helper_refresh.md`): `tw shell refresh`, an explicit
shell function that regenerates the on-disk `taurworks-shell.sh` helper from
the currently installed package and re-sources it into the current shell.

# Result

Prior-art check (WI predates the check): duplication search found no
existing implementation in `src/`, `.claude/skills/`, or elsewhere in-repo;
no sibling repos or external libraries identified as relevant. Demand search
found no other overlapping work items or backlog entries. Recommendation:
proceed — no action needed.

Changes:

- `src/taurworks/resources/shell/taurworks-shell.sh`: added
  `_tw_shell_refresh()` (resolves target path via
  `${TAURWORKS_SHELL_HELPER_PATH:-$HOME/.config/taurworks/taurworks-shell.sh}`,
  calls `command taurworks shell print`, writes via a temp-file-then-`mv`
  pattern for atomicity, leaves the existing file untouched on any failure,
  then `source`s the result) and `shell refresh` dispatch in `tw()`.
- `README.md`: documented `tw shell refresh` next to the `tw activate`
  section, including the `TAURWORKS_SHELL_HELPER_PATH` override and the
  one-time manual bootstrap step for shells that predate the command.
  Updated the pre-existing "Stale shell-helper mitigation" note (added by
  `WI-TL-BREAKGLASS-0001`) to name `tw shell refresh` instead of its
  `tw install`/`tw refresh` placeholder text.
- `tests/shell_helper_test.py`: new `ShellRefreshTest` — successful
  refresh+re-source (proven by a marker function becoming callable in the
  same shell after refresh, not just a file-content check), `taurworks
  shell print` failure leaves the existing file untouched, default path vs.
  `TAURWORKS_SHELL_HELPER_PATH` override, and unexpected-argument rejection.

Manual dogfood test against the real package (not the test shims): sourced
the current helper (with `tw shell refresh` already defined), appended a
temporary marker function to the packaged resource file on disk, ran `tw
shell refresh`, and confirmed the marker became callable in the same shell
without restarting it; the marker was removed before committing. Also
exercised the other side of the bootstrap gap: sourcing the pre-WI helper
(no `tw shell refresh` defined) and running `tw shell refresh` falls through
to `command taurworks shell refresh`, which argparse correctly rejects with
`invalid choice: 'refresh'` — the gap fails loud with a clear error, not
silently, matching the design's stated expectation.

Passive staleness detection (Option B in the design) was not implemented,
per `forbidden_actions: implement_passive_staleness_detection` — deferred to
a follow-up work item once this one is dogfooded.

# Validation

- `scripts/version tools` — Python 3.11.10, Black 26.3.1, Ruff 0.15.12
  (Taurworks conda env).
- `scripts/format --check --diff` — one file initially needed reformatting
  (`tests/shell_helper_test.py`); applied `scripts/format`, re-verified
  clean (28 files unchanged).
- `scripts/lint` — black + ruff both clean.
- `scripts/test` — `Ran 285 tests ... OK` (281 pre-existing + 4 new).
- `lrh validate` — 4 pre-existing `contributors.md` errors only (unrelated,
  documented pre-existing gap); no new errors introduced.

# Follow-up

- `session_transcript` should be updated from `pending` to
  `claude-app:<session-id>` after this session ends.
- The follow-up work item for Option B (passive staleness detection on
  `tw activate`) is still not filed, per the design's phased sequencing —
  recommend opening it once this PR has had a round of real dogfooding.
- This PR's branch (`xenotaur/feat/wi-shell-helper-refresh-0001-impl`)
  deliberately does not reuse the planning PR's branch name
  (`xenotaur/feat/wi-shell-helper-refresh-0001`, PR #75) to avoid the
  slug-collision idempotence-check issue documented in this session's
  `feedback` memory — any `/lrh-review-response` or `/lrh-confirm-fixes`
  run on this PR should use the natural branch-derived slug
  (`wi-shell-helper-refresh-0001-impl-review`/`-confirm`) without needing
  manual correction.
