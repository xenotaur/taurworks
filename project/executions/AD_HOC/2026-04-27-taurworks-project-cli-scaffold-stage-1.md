---
prompt_id: "PROMPT(TAURWORKS_PROJECT_CLI_SCAFFOLD)[STAGE_1/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-project-cli-scaffold-stage-1"
status: "landed"
date: "2026-04-27"
---

# Summary
Added a minimal scaffold for `taurworks project ...` in the CLI with placeholder `where` and `list` command paths, while preserving existing top-level commands.

# Result
- Added a `project` namespace parser in `src/taurworks/cli.py`.
- Added placeholder dispatch for `taurworks project where` and `taurworks project list` with explicit non-implementation messaging.
- Updated README and unified command model documentation to reflect scaffolded namespace status.
- Extended smoke tests to cover `taurworks project --help` and placeholder behavior.

# Validation
- Attempted `python -m pip install -e .` but it failed due to offline/proxy restrictions fetching build dependencies (`setuptools>=64`).
- Attempted `taurworks --help` and `taurworks project --help`, but `taurworks` was unavailable because editable install did not complete.
- Ran `PYTHONPATH=src python -m taurworks.cli --help`.
- Ran `PYTHONPATH=src python -m taurworks.cli project --help`.
- Ran `PYTHONPATH=src python -m taurworks.cli project where`.
- Ran `PYTHONPATH=src python -m unittest discover tests '*_test.py'`.

# Follow-up
- The helper script `scripts/prompts/record-execution` is not present in this repository checkout, so this execution record was added manually.
