---
prompt_id: "PROMPT(TAURWORKS_POST_MERGE_SIDE_EFFECT_SAFETY_AUDIT)[AUDIT/2026-05-17]"
work_item: "AD_HOC"
slug: "taurworks-post-merge-side-effect-safety-audit"
status: "landed"
date: "2026-05-17"
---

# Summary

Performed a non-destructive post-merge side-effect safety audit focused on
Conda creation, Conda activation, environment-variable exports, script sourcing,
subprocess usage, shell mutation through the sourced `tw` helper, and surprising
legacy command behavior.

# Result

- Added `project/audits/side_effects.md` with a side-effect taxonomy,
  command-by-command inventory, required audit answers, findings, and follow-up
  recommendations.
- Added `project/audits/README.md` and linked the audit from the root README.
- Added `scripts/audit-side-effects`, a best-effort non-destructive pattern
  scanner for future side-effect-sensitive reviews.
- Added lightweight tests that verify the audit is discoverable and the helper
  script runs.

# Validation

- Passed: `scripts/format --check`
- Passed: `scripts/lint`
- Passed: `scripts/test`
- Passed: `scripts/audit-side-effects`
- Warning: `scripts/prompts/record-execution --help` could not run because
  `scripts/prompts/record-execution` is not present in this checkout; this
  record was created manually following `project/executions/README.md`.

# Follow-up

- Migrate or deprecate legacy top-level `taurworks refresh` so refresh is
  metadata-only by default.
- Move Conda creation behind an explicit environment command or explicit flag.
- Keep environment activation and exports limited to explicit sourced shell
  helpers such as `tw activate`.
- Require explicit trust/opt-in before any future user/project script sourcing.
