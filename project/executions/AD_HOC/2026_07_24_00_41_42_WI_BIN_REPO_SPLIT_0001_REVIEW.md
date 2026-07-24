---
execution_id: 2026_07_24_00_41_42_WI_BIN_REPO_SPLIT_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_BIN_REPO_SPLIT_0001_REVIEW)[2026-07-24T00:38:40-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/85
commit: 1fa6250
created_at: 2026-07-24T00:41:42-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/85
session_transcript: pending
---

# Summary

Addressed the 1 open review comment on PR #85
(`project/work_items/proposed/WI-BIN-REPO-SPLIT-0001.md`), a planning-only
work item for the `bin/`/`taurscripts` repo split drafted from
`project/design/packaging_and_install.md`. The comment was a correctness
gap in the WI's packaging requirement, not a code defect, since nothing has
been implemented yet.

# Result

The 1 comment passed presence/validity/feasibility triage and was fixed:

- chatgpt-codex-connector (P2) — "Stage sourceme files inside the package
  tree." Confirmed against `setup.py` (`package_dir={"": "src"}`) that
  `package_data` paths resolve relative to `src/taurworks`, while
  `sourceme/` lives at the repository root — a sibling to `src/`, not
  inside it. The reviewer independently verified this by building a test
  wheel with a `../../sourceme/*.source`-style `package_data` entry and
  confirming it was excluded from the wheel. Reworded Problem/Context,
  Required Change #4, the corresponding acceptance criterion (both
  frontmatter and body), `artifacts_expected`, and the `## Validation`
  section to require relocating (or copying, with an explicit
  synchronization strategy if a canonical copy must remain at the repo
  root) `sourceme/`'s `tl`-delivery file(s) under `src/taurworks` first,
  and to validate the fix by building the package and inspecting the
  actual wheel/sdist contents rather than trusting the `package_data`
  declaration alone.

No comments skipped.

# Validation

- `git rev-parse HEAD` (pre-push): `767cdfeaf733ffd2c260098fc85e67c095885141`
- Tool versions (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `./scripts/format --check --diff`: 28 files unchanged, pass (only markdown changed)
- `./scripts/lint`: black + ruff, pass
- `./scripts/test`: 288 tests, OK
- `lrh validate`: 4 errors, all `contributors/contributors.md` — a
  genuinely pre-existing, confirmed-still-open gap on `master` (see
  `project_contributors_md_gap` memory), unrelated to this PR's content.

# Follow-up

- `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after this session ends.
- Recommend `/lrh-confirm-fixes` before merge to verify the fix against
  the current diff and resolve the review thread.
