---
prompt_id: "PROMPT(TAURWORKS_UNIFIED_PROJECT_DOCS)[DESIGN_ALIGNMENT/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-unified-project-docs-design-alignment-rerun-2"
status: "landed"
date: "2026-04-27"
rerun_of: "project/executions/AD_HOC/2026-04-27-taurworks-unified-project-docs-design-alignment-rerun-1.md"
---

# Summary
Addressed additional PR review comments for config/docs consistency.

# Result
- Removed ambiguous `Admin/` alternative and normalized project metadata path to `.taurworks/`.
- Clarified that `taurdev` naming maps to `taurworks dev` configuration.
- Added explicit status note in design overview that namespaced commands are target direction, not fully shipped behavior yet.
- Aligned roadmap Phase 4 MVP verbs with canonical expected dev command list.

# Validation
- Reviewed changed markdown for internal consistency.
- Ran lightweight diff checks.

# Follow-up
- Keep command lists and roadmap in lock-step as implementation planning evolves.
