---
prompt_id: "PROMPT(TAURWORKS_HELP_ALIAS)[IMPLEMENT/2026-05-16]"
work_item: "AD_HOC"
slug: "taurworks-help-alias"
status: "landed"
date: "2026-05-17"
---

# Summary
Implemented the prompt-driven `taurworks help` alias so the Python CLI matches the existing `tw help` shell helper behavior.

# Result
- Added top-level argv normalization so `taurworks help` maps to `taurworks --help` before argparse dispatch.
- Added lightweight support for `taurworks help COMMAND` by routing to the existing command parser help, e.g. `taurworks help project` maps to `taurworks project --help`.
- Added CLI tests covering top-level help alias equality, namespace help alias equality, and preservation of invalid-command failures.
- Updated README and current status documentation to keep the command model accurate.

# Validation
- Warning: `scripts/prompts/record-execution --help` was attempted, but `scripts/prompts/record-execution` is not present in this checkout, so this record was created manually following `project/executions/README.md`.
- Warning: `python -m pip install -e .` was attempted, but build dependency installation could not reach `setuptools>=64` because the package index tunnel returned `403 Forbidden`.
- Passed: `taurworks help`.
- Passed: `taurworks --help`.
- Passed: `taurworks project --help`.
- Passed: `taurworks dev --help`.
- Passed: `taurworks shell --help`.
- Passed: `scripts/lint`.
- Passed: `scripts/test`.
- Passed: `scripts/test-portability`.
- Passed: shell helper smoke check with `taurworks shell print > /tmp/taurworks-shell.sh`, `source /tmp/taurworks-shell.sh`, `tw help`, `tw --help`, and `diff` confirming identical output.
- Passed: `taurworks help project`, `taurworks help dev`, and `taurworks help shell` matched their corresponding `COMMAND --help` output.

# Follow-up
None.
