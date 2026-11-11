---
execution_id: 2026_11_11_00_11_17_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_CONFIRM)[2026-11-11T00:10:47+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_10_23_33_06_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_CONFIRM
pr: https://github.com/xenotaur/taurworks/pull/118
commit:
created_at: 2026-11-11T00:11:17+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: pending
---

# Summary

Round 2 of `/lrh-confirm-fixes` for PR #118, run inline from `/lrh-land`.
Verified against head `247125d`, after review-response round 2 (`5b60892`).

# Result

- Authoritative thread list: 3 threads, all already resolved in round 1;
  0 with `isResolved == false`.
- The substitute PR-mode self-review findings on `8bbfed0` came as a
  report, not as threads. I classified them against `gh pr diff`; all are
  Clear-satisfied:
  1. The `activate .` promise is removed from AC2, RC2 and test (i), and
     the `prefer_project_root=False` branch is stated as unchanged.
  2. Inventory and command lists: citations corrected; the
     `resolve_global_activation_project` → `find_current_project` path is
     documented, with a requirement to carry `resolved_by` and ambiguity
     candidates; env, trust and legacy-inspect commands added; test (k)
     added.
  3. Nits: the design text, test (i)'s directory, `artifacts_expected` and
     the PR body are fixed. The `rerun_of` convention was kept deliberately.
- Remediation for a non-thread finding: no `resolveReviewThread` is
  possible, so this record plus the round-2 `_REVIEW` record are the
  acknowledgment.
- The user confirmed the batch live.
- Step 6 thread verdict: green.
- Provisional CI at `247125d`: 4 jobs pending.

# Validation

- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Step 8: CI on the post-push head, and a fresh substitute PR-mode review.
  It's required because round 2's findings were non-thread findings.
