---
prompt_id: "PROMPT(TAURWORKS_DECLARATIVE_ACTIVATION_CONFIG_DESIGN)[DESIGN/2026-05-15]"
work_item: "WI-ACTIVATION-CONFIG-0001"
slug: "taurworks-declarative-activation-config-design"
status: "landed"
date: "2026-05-16"
---

# Summary
Designed Phase 2 declarative activation config for Taurworks after Phase 1
dogfooding, focusing on the safe legacy setup subset that can be represented in
`.taurworks/config.toml`.

# Result
- Expanded `project/design/activation_extension.md` with detailed planned schema
  behavior for `[activation].message`, Conda-only initial
  `[activation.environment]`, and `[activation.exports]`.
- Documented safety constraints: no arbitrary script sourcing by default, no
  arbitrary user commands by default, no shell startup-file edits, no automatic
  `conda init`, no secret leakage in normal output, and no shell mutation from
  `taurworks project activate --print`.
- Deferred user scripts/hooks behind explicit future opt-in and trust semantics.
- Proposed `taurworks legacy inspect PROJECT` and `taurworks legacy migrate
  PROJECT --apply` as conservative migration tooling that prefers declarative
  fields over copying scripts.
- Added `WI-ACTIVATION-CONFIG-0001` as the follow-up implementation package for
  activation message/exports, Conda activation, legacy inspect, legacy migrate,
  and trusted hooks after dogfood.
- Updated design and work-item indexes so the planned design and implementation
  package are discoverable.

# Validation
- Passed: `scripts/format --check --diff`.
- Passed: `scripts/lint`.
- Passed: `scripts/test` with a non-fatal warning that `conda env list` timed
  out after 2 seconds.
- Passed: `git diff --check`.
- Blocked: `lrh validate` because `lrh` is not installed in this environment.
- Blocked: `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_DECLARATIVE_ACTIVATION_CONFIG_DESIGN)[DESIGN/2026-05-15]" --work-item WI-ACTIVATION-CONFIG-0001 --slug taurworks-declarative-activation-config-design --status in_progress` because `scripts/prompts/record-execution` is not present in this checkout; this record was created manually using `project/executions/README.md` conventions.

# Follow-up
- Implement activation message and exports in a separate PR.
- Implement Conda activation in `tw activate` in a separate PR.
- Implement legacy inspect/migrate in separate PRs.
- Design trusted hooks after declarative activation dogfooding.
