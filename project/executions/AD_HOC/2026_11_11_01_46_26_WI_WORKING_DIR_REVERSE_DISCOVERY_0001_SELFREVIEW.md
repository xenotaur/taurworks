---
execution_id: 2026_11_11_01_46_26_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW)[2026-11-11T01:46:26+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_10_16_21_41_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/118
commit: e5114117b0f4204a47e002f0d99a46dc3cabef08
created_at: 2026-11-11T01:46:26+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

PR-mode `/lrh-self-review` substitute pass 2 on PR #118, at head `561e970`
(the round-2 `_CONFIRM` commit), required because round 2's findings were
non-thread findings. It used a cold-context subagent and was report-only.
This record was created at closeout, on `master`, rather than pushed to the
PR. Pushing it would have moved the PR head and needed another review
round. That follows the PR #117 precedent.

# Result

- Verdict: safe to merge, but with WI gaps worth fixing.
- Findings:
  1. Medium: `ProjectResolution` (`project_internals.py:36-43`) had no
     carrier for ambiguity candidates on the `resolve_project_target`
     path. The invoking session verified this directly.
  2. Low-medium: "pass a target" guidance was wrong for `working-dir
     show`, whose names resolve relative to the cwd.
  3. Low: inventory gaps (the `project root` and `taurworks working`/`root`
     emitters, the `:775` create guard, `project where`).
  4. Low: the `:127` wording.
- This tripped the stop-work condition again. The user chose "Fix in PR
  (round 3)": review-response round 3 (`6b7e35f`), confirm-fixes round 3.

# Validation

The subagent re-checked citations and ran a temp-tree experiment with an
isolated HOME/XDG.

# Follow-up

- Fixed in round 3.
