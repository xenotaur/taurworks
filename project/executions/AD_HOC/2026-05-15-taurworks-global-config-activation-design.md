---
prompt_id: "PROMPT(TAURWORKS_GLOBAL_CONFIG_ACTIVATION_DESIGN)[DESIGN/2026-05-15]"
work_item: "AD_HOC"
slug: "taurworks-global-config-activation-design"
status: "landed"
date: "2026-05-15"
---

# Summary
Updated Taurworks control-plane design documentation for the next global-resolution and activation-planning phases.

# Result
- Captured planned XDG-style global config and explicit workspace root behavior.
- Captured planned global project registry behavior for projects outside immediate workspace discovery.
- Captured workspace/registry-aware `tw projects` and `tw activate` resolution order and conservative fallback semantics.
- Updated declarative activation design for messages, environment strategies, and exports without arbitrary script sourcing.
- Documented future user-script/hook support as explicit opt-in only with warnings, inspection/dry-run modes, and per-project trust.
- Updated README/status/focus/roadmap/work-item artifacts touched by this design alignment.

# Validation
- Passed: `./scripts/test`.
- Passed: `./scripts/lint`.
- Blocked: `lrh validate` because `lrh` is not installed in this environment.
- Blocked: `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_GLOBAL_CONFIG_ACTIVATION_DESIGN)[DESIGN/2026-05-15]" --work-item AD_HOC --slug taurworks-global-config-activation-design --status landed` because `scripts/prompts/record-execution` is not present in this checkout; this record was created manually using `project/executions/README.md` conventions.

# Follow-up
- Implement Phase 1a global config/workspace commands in a separate PR.
- Implement Phase 1b registry commands in a separate PR.
- Implement Phase 1c workspace/registry-aware listing and activation resolution in a separate PR.
- Keep declarative activation and user-script support as separate future design/implementation slices.
