---
execution_id: 2026_07_17_21_14_32_WI_TRUSTED_LEGACY_SOURCING_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TRUSTED_LEGACY_SOURCING_0001_REVIEW)[2026-07-17T21:13:59-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_17_19_42_37_WI_TRUSTED_LEGACY_SOURCING_0001
pr: https://github.com/xenotaur/taurworks/pull/70
commit: 6803058
created_at: 2026-07-17T21:14:32-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/70
session_transcript: claude-app:149f0939-369e-4d12-afa5-29a079bb476f
---

# Summary

Address five open review comments on PR #70 (WI-TRUSTED-LEGACY-SOURCING-0001
implementation): three Copilot/Codex comments about one root-cause issue
(misleading "never ask again" wording), one Copilot comment about missing
write-side validation, and one Codex P2 comment about a real resolution bug
in the prompted trust/inspect flow.

# Result

All five comments verified valid by direct code inspection before fixing
(reading the actual `_tw_offer_legacy_trust`, `write_trust_record_preserving_config`,
and `manager.find_current_project` implementations); all fixed (commit
6803058):

1. **Copilot x2 + Codex (same root cause) -- misleading "[n]ever ask again."**
   The skip branch printed a message implying the choice would persist but
   never wrote anything, so the next `tw activate` would prompt again
   regardless. Collapsed the prompt to three honest choices (source once /
   trust and source / anything else to skip this time), removed the
   separate `n)` branch, and reworded the comment above
   `_tw_legacy_prompt_choice` to stop implying persistence.
2. **Copilot -- `write_trust_record_preserving_config` didn't validate
   inputs.** The only current caller always passes a resolved absolute path
   and a real sha256 digest, so this wasn't an active bug, but the function
   is public API (no leading underscore, mirrors
   `write_project_root_preserving_config`) and a future bad caller could
   silently write corrupted global config. Added absolute-path and
   digest-format validation before writing, symmetric with the existing
   read-side validation in `trust_record_from_config`.
3. **Codex P2 -- prompted inspect/trust used the bare project name instead
   of the resolved project root.** Verified the actual bug by tracing
   `manager.find_current_project`: it calls
   `find_project_root_candidate`, which only recognizes `.taurworks`-having
   roots, not legacy-admin ones. For a project that is neither registered
   nor a workspace child, once `_tw_activate` has already cd'd into it,
   re-resolving the bare name from that same directory falls through to
   treating the name as a *child* of cwd -- a nonexistent path -- so
   `taurworks legacy inspect NAME` and `taurworks project trust set NAME`
   both silently failed to find the project when called from the prompt.
   Added a new `TAURWORKS_ACTIVATION_PROJECT_ROOT` `--shell` payload field
   (the diagnostics already computed `project_root`; it just wasn't
   emitted) and changed `_tw_offer_legacy_trust` to pass that absolute path
   instead of the bare name to both calls.

Nothing was skipped.

# Validation

- Python 3.11.8, black 26.3.1, ruff 0.15.12
- `scripts/format --check --diff` -- 27 files unchanged
- `scripts/lint` -- all checks passed
- `scripts/test` -- 273 tests OK
- `lrh validate` -- no new errors (4 known pre-existing `contributors.md`
  errors remain)
- New regression test reproduces comment 3's exact scenario (unregistered,
  non-workspace legacy project, prompt's "trust" choice) and confirms the
  trust record is written correctly post-fix.

# Follow-up

- Process note: this review-response pass proceeded directly from
  fetching/triaging comments into fixing them, without pausing at an
  explicit confirm gate first -- the session had two client disconnects in
  the middle of the primary implementation and this response followed
  immediately after reconnecting. Flagged to the user in the closing
  summary; no objection raised.
- On merge: closeout via /lrh-closeout (mark this record and the primary
  record landed, resolve WI-TRUSTED-LEGACY-SOURCING-0001).
- Resolving the five GitHub review conversations is a human action.
