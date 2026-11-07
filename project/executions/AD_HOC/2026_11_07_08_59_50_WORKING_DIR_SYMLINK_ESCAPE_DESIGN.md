---
execution_id: 2026_11_07_08_59_50_WORKING_DIR_SYMLINK_ESCAPE_DESIGN
prompt_id: PROMPT(AD_HOC:WORKING_DIR_SYMLINK_ESCAPE_DESIGN)[2026-11-07T08:59:50+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/115
commit: 436489d11b8a06f969d1d6defdae552b1243a853
created_at: 2026-11-07T08:59:50+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/115
session_transcript: claude-app:886ad668-3050-4ae4-8925-4fa068b6791c
---

# Summary

Backfill execution record for PR #115's primary design work, authored at
`/lrh-land` closeout because no primary implementation record existed for
the PR (found-or-backfill matrix: not found → backfill). The original work
was two commits on 2026-10-26: `88d5818` ("Design: accept symlinked
working_dir outside project_root; file WI") and `0e76348` ("Pull
WI-WORKING-DIR-SYMLINK-ESCAPE-0001 into active focus/roadmap"). They were
written in an earlier Claude session whose durable ID is not available
here; `session_transcript` above points at the landing session, which
authored this record and all of the PR's `_REVIEW`/`_CONFIRM` records.

# Result

- `project/design/config_model.md` "Working-dir containment and symlinked
  work trees" and `project/design/design.md:29`: `working_dir` containment
  becomes a lexical check on the literal config value (reject absolute and
  every `..`, a deliberate tightening for in-root `..`), the resolved path
  may leave `project_root` through a symlink, and dangling/looping symlinks
  are a helper-level `ProjectConfigError`.
- `WI-WORKING-DIR-SYMLINK-ESCAPE-0001` filed under `work_items/proposed/`;
  it stays `status: proposed` (implementation is separate, later work).
- `current_focus.md` and `roadmap.md` Phase 9 updated to cover it.
- Landed as squash merge `436489d` after four review-response rounds
  (records `2026_11_06_23_47_02`, `2026_11_06_23_55_54`,
  `2026_11_07_00_01_06`, `2026_11_07_06_31_38` `_REVIEW`) and one
  confirm-fixes pass (`2026_11_07_08_55_07_..._CONFIRM`). All three Copilot
  threads resolved as Clear-satisfied; none deferred.

CHAIN-NOTE: cycles=4; stops=3; gates=[chain_init, review_response_r1, stop_amend_r2, stop_amend_r3, stop_amend_r4, confirm_fixes_batch, merge_closeout]; friction=per-caller inventory churn; note="Thread A kept failing re-verification as each round enumerated per-command behavior in more detail; it converged only once the invalid-symlink rule was stated at the helper level. Handoff had claimed the PR was fully green, but 3 unresolved Copilot threads existed."

# Validation

- PR CI on final head `2afcbb7`: 4/4 `lint-and-test` checks passed.
- Substitute cold-context PR review on `2afcbb7`: nothing blocking.
- `lrh validate` at closeout: unchanged pre-existing baseline (3 errors,
  10 warnings, none in files this PR touches).

# Follow-up

- Implement `WI-WORKING-DIR-SYMLINK-ESCAPE-0001` (see its "Implementer
  notes from review" section).
- Pre-existing `lrh validate` YAML errors in
  `work_items/resolved/WI-LEGACY-CONDA-GATING-0001.md` (unrelated).
