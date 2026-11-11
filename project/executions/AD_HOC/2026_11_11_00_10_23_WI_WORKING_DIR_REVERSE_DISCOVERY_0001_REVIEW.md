---
execution_id: 2026_11_11_00_10_23_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW)[2026-11-11T00:10:13+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_10_23_32_18_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/118
commit:
created_at: 2026-11-11T00:10:23+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: pending
---

# Summary

Round 2 of review-response for PR #118, run inline from `/lrh-land`. It
addresses the findings of the substitute PR-mode self-review on `8bbfed0`.
Those findings tripped the run's stop-work condition, and the user then
asked for them to be fixed ("Yes, fix them"). Fixes are in commit `5b60892`.

# Result

1. **Medium:** the WI promised `project activate . --print` via the
   `prefer_project_root` explicit-path branch, but `activate`'s path-like
   targets use `prefer_project_root=False` (`project_resolution.py:208-212`).
   I verified this directly. My round-1 fix for Copilot thread 1 introduced
   the error. Fix:
   - `activate .` is dropped from AC2, Required Change 2 and test (i).
   - The `prefer_project_root=False` branch is stated as unchanged.
   - The explicit-path branch now names `project working .` and
     `working-dir show .` only.
   - Test (i) also asserts that `activate .` from a physical subdirectory
     keeps resolving to that subdirectory.
2. **Low:** the call-site inventory and command lists. Fix:
   - Corrected which callers reach the no-target branch (only
     `working-dir show`, `:1081-1085`).
   - Documented `resolve_global_activation_project` (`:187`) through
     `manager.find_current_project`, which serves `activate`, `env
     show`/`set`, `trust set`/`unset` and `legacy inspect`.
   - Required Change 2 now requires `find_current_project` (or its
     replacement) to carry `resolved_by` and ambiguity candidates.
   - Added those commands to AC2 and RC3's guidance list, and added test (k).
3. **Nits fixed:**
   - The design text no longer says `project working .` reports
     "unresolved"; it says it silently resolves to the external directory.
   - Test (i) runs from a subdirectory.
   - Added `tests/project_resolution_test.py` to `artifacts_expected`.
   - The PR body now lists tests (a) through (k).
4. **Nit not changed:** `rerun_of` on the `_REVIEW`/`_CONFIRM` side records
   points to the primary creation record, following the PR #117 precedent
   and the skills' own `rerun_of` rules. This round's record points to the
   round-1 `_REVIEW` record, per `/lrh-review-response` Step 7 precedence.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-WORKING-DIR-REVERSE-DISCOVERY-0001`:
  `prompt_ready: yes`.

# Follow-up

- Confirm-fixes on the new head, including a fresh substitute review signal
  (this finding came from a non-thread surface).
