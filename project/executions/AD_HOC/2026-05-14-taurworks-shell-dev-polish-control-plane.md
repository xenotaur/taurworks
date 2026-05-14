---
prompt_id: "PROMPT(AD_HOC:TAURWORKS_SHELL_DEV_POLISH_CONTROL_PLANE)[2026-05-14T00:00:00+00:00]"
work_item: "AD_HOC"
slug: "taurworks-shell-dev-polish-control-plane"
status: "landed"
date: "2026-05-14"
---

# Summary

Updated Taurworks control-plane documentation for the post-dogfood `tw activate` polish sequence.

# Result

- Captured the next PR sequence for `tw` UX polish, project-list status classification, a minimal read-only `dev` namespace scaffold, and activation-extension design.
- Documented the safety stance separating read-only `taurworks project activate --print`, explicit shell-mutating sourced `taurworks-shell.sh` `tw activate`, and legacy `Admin/project-setup.source` migration/design.
- Added activation-extension design notes for future readiness messages, environment activation, trusted startup hooks, legacy migration, and sourcing trust boundaries.
- Updated affected design and work-item README documentation.

# Validation

- Blocked: `scripts/version tools` because `scripts/version` is not present in this checkout.
- Passed: `scripts/format --check --diff`
- Passed: `scripts/lint`
- Passed: `scripts/test`
- Passed: `./scripts/smoke`
- Blocked: `scripts/prompts/record-execution --prompt-id "PROMPT(AD_HOC:TAURWORKS_SHELL_DEV_POLISH_CONTROL_PLANE)[2026-05-14T00:00:00+00:00]" --work-item AD_HOC --slug taurworks-shell-dev-polish-control-plane --status landed` because `scripts/prompts/record-execution` is not present in this checkout. This record was created manually following `project/executions/README.md`.

# Follow-up

Implement the documented behavior changes in small, separate PRs: `tw` UX polish, project-list classification, read-only `dev` scaffold, and activation-extension design refinement before implementation.
