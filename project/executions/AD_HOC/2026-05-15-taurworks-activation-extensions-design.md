---
prompt_id: "PROMPT(TAURWORKS_ACTIVATION_EXTENSIONS_DESIGN)[DESIGN/2026-05-14]"
work_item: "AD_HOC"
slug: "taurworks-activation-extensions-design"
status: "landed"
date: "2026-05-15"
---

# Summary

Documented future activation-extension design for readiness messages,
declarative environment activation, trusted startup hooks, and legacy
`Admin/project-setup.source` migration.

# Result

- Found no prior execution record for this exact prompt ID before starting.
- Expanded `project/design/activation_extension.md` into a focused future design
  document with explicit non-goals and safety boundaries.
- Linked the activation-extension design from the root README activation section.
- Did not implement environment activation, startup hooks, legacy setup sourcing,
  shell wrapper behavior changes, or `dev` workflow automation.

# Validation

- Passed: `./scripts/lint && ./scripts/test`.
- Note: `./scripts/test` completed successfully after warning that fetching Conda
  environments timed out after 2 seconds.
- Blocked: `scripts/prompts/record-execution --help` because the
  `scripts/prompts/record-execution` helper is not present in this checkout; this
  record was created manually using the documented execution-record schema.

# Follow-up

None for this design PR. Future implementation should proceed in separate PRs
following the documented phased approach.
