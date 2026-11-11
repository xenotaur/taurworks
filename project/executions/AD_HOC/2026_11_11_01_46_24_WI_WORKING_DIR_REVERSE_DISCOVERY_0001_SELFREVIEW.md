---
execution_id: 2026_11_11_01_46_24_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW)[2026-11-11T01:46:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_10_16_21_41_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/118
commit: e5114117b0f4204a47e002f0d99a46dc3cabef08
created_at: 2026-11-11T01:46:24+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

PR-mode `/lrh-self-review` substitute pass 1 on PR #118, at head `8bbfed0`
(the round-1 `_CONFIRM` commit). It used a cold-context general-purpose
subagent and was report-only. This record was created at closeout, on `master`, rather than pushed to the
PR. Pushing it would have moved the PR head and needed another review
round. That follows the PR #117 precedent.

# Result

- Verdict: no runtime breakage (the PR changes planning only), but not
  ready to merge.
- Findings:
  1. Medium: the WI promised `project activate .` via the
     `prefer_project_root` branch, but activate uses
     `prefer_project_root=False` (`project_resolution.py:208-212`). The
     invoking session verified this directly.
  2. Low: the call-site inventory was wrong. `find_current_project` can't
     carry candidates, and the env, trust and legacy-inspect commands were
     missing.
  3–4. Nits: `project working .` was described as "unresolved"; test (i)
     needed a subdirectory; the PR body's test range; a missing
     `tests/project_resolution_test.py`; the `rerun_of` convention.
- This tripped the stop-work condition. The user chose to fix them:
  review-response round 2 (`5b60892`), confirm-fixes round 2.

# Validation

The subagent re-checked citations against `src/`, ran a temp-tree
experiment, `lrh validate` (0/0), and the readiness check
(`prompt_ready: yes`).

# Follow-up

- Fixed in round 2.
