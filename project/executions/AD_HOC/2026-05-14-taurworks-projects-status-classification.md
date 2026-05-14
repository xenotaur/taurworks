---
prompt_id: "PROMPT(TAURWORKS_PROJECTS_STATUS_CLASSIFICATION)[IMPLEMENT/2026-05-14]"
work_item: "AD_HOC"
slug: "taurworks-projects-status-classification"
status: "landed"
date: "2026-05-14"
---

# Summary
Implemented a focused project-listing status classification pass for top-level `taurworks projects` / delegated `tw projects` behavior.

# Result
- Added workspace entry classifications for `initialized`, `workspace-only`, and `legacy-admin` projects.
- Updated default and detailed project-list output to show status and activation eligibility diagnostics.
- Kept legacy `Admin/project-setup.source` recognition read-only; it is not sourced by listing or activation guidance.
- Updated compatibility activation messaging for non-initialized workspace entries.
- Documented status meanings, initialization guidance, and legacy migration expectations.
- Added tests for status classification, read-only classification behavior, detailed listing diagnostics, delegated `tw projects`, and concise activation messaging.

# Validation
- Passed: `./scripts/test`
- Passed: `./scripts/lint`
- Passed: `./scripts/format --check --diff`
- Passed: temporary workspace validation with `taurworks projects`, `taurworks projects --details`, and sourced-helper `tw projects`.
- Note: `scripts/prompts/record-execution` was requested by the prompt but is not present in this checkout, so this record was created manually according to `project/executions/README.md`.

# Follow-up
- Add a dedicated legacy migration tool/script later if the project decides to support converting `Admin/project-setup.source` setups into `.taurworks/config.toml`.
