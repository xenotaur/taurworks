---
execution_id: 2026_11_09_06_03_14_WI_WORKING_DIR_SYMLINK_ESCAPE_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_SYMLINK_ESCAPE_0001_SELFREVIEW)[2026-11-09T06:03:07+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_09_05_36_39_WI_WORKING_DIR_SYMLINK_ESCAPE_0001
pr: https://github.com/xenotaur/taurworks/pull/117
commit: 6cb00f2ff66fa1cdde3d1efd2a54220d056ee6ad
created_at: 2026-11-09T06:03:14+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/117
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

PR-mode `/lrh-self-review` pass on PR #117 at HEAD `1191796`, the
`_CONFIRM` commit. It ran from `/lrh-confirm-fixes` Step 8 as the
substitute review signal: neither automatic reviewer re-reviews on push
(Copilot ruleset `review_on_push: false`; Codex reviews only when the PR
opens). The pass used a cold-context general-purpose subagent and was
report-only.

This record was created at closeout, on `master`, rather than pushed to the
PR. Pushing it would have moved the PR head and needed another review
round.

# Result

- Verdict: safe to merge as-is; no blocking issues. 196 targeted tests
  re-run OK; execution-record frontmatter parsed and the links checked.
- Findings (3, none blocking):
  1. Low, docs: README.md lines 560 and 764 say only that paths escaping
     `project_root` via `..` are rejected. They don't mention the in-root
     `..` tightening or the leading-`..` behavior of `working-dir set`. The
     invoking session re-checked directly: the text is accurate, just less
     specific than lines 813 and 837. No change was made; the user merged
     with it known.
  2. Very low: `project/sessions/index.jsonl` has `written_branches: []`.
     Not verified as a defect.
  3. Informational: records were still `in_progress` before closeout, as
     expected.
- Not routed to a review-response round. Counted as a substitute review
  signal (`self_review_rounds=1`).

# Validation

The subagent confirmed CI and review state against live GitHub data. CI was
green on `1191796`: 4/4 `lint-and-test` jobs.

# Follow-up

- Optional README precision pass for lines 560 and 764.
