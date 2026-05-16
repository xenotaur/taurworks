---
prompt_id: "PROMPT(TAURWORKS_XDG_GLOBAL_CONFIG_WORKSPACE)[IMPLEMENT/2026-05-15]"
work_item: "AD_HOC"
slug: "taurworks-xdg-global-config-workspace"
status: "landed"
date: "2026-05-15"
---

# Summary
Implemented Phase 1a XDG-style global config and workspace root support.

# Result
- Added user-global config helpers for `$XDG_CONFIG_HOME/taurworks/config.toml` with fallback to `~/.config/taurworks/config.toml`.
- Added `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`.
- Added tests for XDG path resolution, fallback path resolution, read-only config diagnostics, workspace show behavior, and workspace set preservation of unrelated supported TOML content.
- Updated README and configuration design documentation.

# Validation
- Passed: `./scripts/develop`
- Passed: `./scripts/format`
- Passed: `./scripts/lint`
- Passed: `./scripts/test`
- Blocked by environment/network build isolation: `python -m pip install -e .`
- Passed after existing editable install: temporary-XDG CLI validation for `taurworks config where`, `taurworks workspace show`, `taurworks workspace set /tmp/taurworks-workspace-demo`, and final `taurworks workspace show`.
- Prompt helper note: `scripts/prompts/record-execution --help` could not run because `scripts/prompts/record-execution` is not present in this checkout; this record was created manually using `project/executions/README.md` conventions.

# Follow-up
- Phase 1b/1c should add project registry commands and global activation/listing resolution without changing this Phase 1a foundation retroactively.
