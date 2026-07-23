---
execution_id: 2026_07_23_16_12_33_WI_TAURWORKS_SETUP_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TAURWORKS_SETUP_0001_REVIEW)[2026-07-23T16:08:09-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/84
commit: 546cbbf
created_at: 2026-07-23T16:12:33-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/84
session_transcript: pending
---

# Summary

Addressed 3 open review comments on PR #84
(`project/work_items/proposed/WI-TAURWORKS-SETUP-0001.md`), a planning-only
work item for the `taurworks setup` command drafted from
`project/design/packaging_and_install.md`. All comments were correctness
gaps in the WI's scope/requirements, not code defects, since nothing has
been implemented yet.

# Result

All 3 comments passed presence/validity/feasibility triage and were fixed:

- chatgpt-codex-connector (P1) — "Keep setup and refresh on the same helper
  path." Confirmed `_tw_shell_refresh`'s `target_path` in
  `src/taurworks/resources/shell/taurworks-shell.sh:349` has no
  `XDG_CONFIG_HOME` awareness, unlike the setup command this WI proposes.
  Added a Required Change/Acceptance Criterion for a matching XDG-aware
  path-resolution fix in `tw shell refresh`, carved out as a narrow
  exception to the WI's broader "don't touch `tw shell refresh` semantics"
  Non-Goal (only the target-path *resolution* changes, not its
  regenerate/re-source behavior), plus a required integration test for the
  setup-then-refresh sequence.
- chatgpt-codex-connector (P1) — "Include the tl source file in the
  installed package." Confirmed `setup.py`'s `package_data` only lists
  `resources/shell/taurworks-shell.sh`, not `sourceme/`. Documented the
  cross-WI dependency in Problem/Context and Required Changes: the
  `sourceme/` packaging change belongs to `WI-BIN-REPO-SPLIT-0001`, and
  this WI's `tl`-placement acceptance criterion must be validated against
  an installed wheel/pipx environment, not only `PYTHONPATH=src`. Initially
  added a formal `depends_on: [WI-BIN-REPO-SPLIT-0001]` frontmatter field,
  but reverted it after `lrh validate` correctly rejected it as
  `UNKNOWN_DEPENDENCY` (that WI isn't merged to master yet, so its ID isn't
  resolvable in this tree) — kept the sequencing guidance as prose instead,
  which needs no schema validation.
- chatgpt-codex-connector (P2) — "Resolve the checkout root before
  installing." Confirmed the WI's original `scripts/install` shim
  description (`pipx install . --force && taurworks setup`) would resolve
  `.` from the caller's cwd, unlike `scripts/build`/`scripts/check-workflows`,
  both of which compute and `cd` to a `repo_root` first. Updated the
  Required Change/Acceptance Criterion to specify deriving the repo root
  the same way before running pipx.

No comments skipped.

# Validation

- `git rev-parse HEAD` (pre-push): `ab6774ce2e9f3a49693a27599ba3ec860b091128`
- Tool versions (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `./scripts/format --check --diff`: 28 files unchanged, pass (only markdown changed)
- `./scripts/lint`: black + ruff, pass
- `./scripts/test`: 288 tests, OK
- `lrh validate`: 4 errors, all pre-existing `contributors/contributors.md`
  drift relative to `master` — this branch was cut before that fix landed
  on `master` (commit `9f46d63`); unrelated to this PR's content. A
  transient 5th error (`UNKNOWN_DEPENDENCY` on a forward `depends_on`
  reference) was introduced and then reverted during this pass, per above.

# Follow-up

- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Recommend `/lrh-confirm-fixes` before merge to verify the fixes against
  the current diff and resolve the review threads.
- If `WI-BIN-REPO-SPLIT-0001` (PR #85) merges first, consider adding a
  formal `depends_on` entry to this WI at that point, now that the ID
  would resolve.
