---
prompt_id: "PROMPT(TAURWORKS_ACTIVATION_MESSAGE_EXPORTS)[IMPLEMENT/2026-05-16]"
work_item: "AD_HOC"
slug: "activation-message-exports"
status: "landed"
date: "2026-05-16"
---

# Summary
Implemented the first safe slice of Phase 2 declarative activation config: optional activation readiness messages and literal activation exports consumed by the sourced `tw activate` helper.

# Result
- Added project-local `[activation].message` parsing.
- Added validated string `[activation.exports]` parsing using conservative environment variable names.
- Added redacted human activation diagnostics and a separate `taurworks project activate --shell` payload for the sourced helper.
- Updated `tw activate` to export generated variables, change directory, and print configured messages without sourcing arbitrary scripts.
- Updated README and activation design documentation.
- Added project-resolution and controlled shell-helper tests for message/export success, redaction, quoting, and invalid-name failure.

# Validation
- `scripts/prompts/record-execution --help` failed because the helper script is not present in this checkout; this record was created manually following `project/executions/README.md`.
- `python -m pip install -e .` failed because build isolation attempted to fetch `setuptools>=64` and the package index tunnel returned HTTP 403.
- `python -m pip install --no-build-isolation -e .` passed.
- `./scripts/format` passed.
- `./scripts/test` passed.
- `./scripts/lint` passed.
- Manual dogfood activation with temporary `XDG_CONFIG_HOME`, temporary workspace, declarative message, and two exports passed.

# Follow-up
- Conda, virtualenv, Docker, arbitrary hooks/scripts, shell startup-file edits, and legacy migration remain deferred to separate PRs.
