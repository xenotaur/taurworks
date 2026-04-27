---
prompt_id: "PROMPT(TAURWORKS_PROJECT_WHERE)[STAGE_2/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-project-where-stage-2"
status: "landed"
date: "2026-04-27"
---

# Summary
Implemented `taurworks project where` as a read-only diagnostics command that reports cwd, project-root discovery state, config path candidate, metadata presence, and resolution limitations.

# Result
- Added `src/taurworks/project_resolution.py` with a read-only resolver and stable text formatter.
- Wired `taurworks project where` in `src/taurworks/cli.py` to emit diagnostics while preserving placeholder behavior for `project list`.
- Updated README and unified command-model documentation for the implemented read-only `project where` behavior.
- Updated/added tests for command output labels, unresolved state handling, metadata detection, and XDG config-path behavior.

# Validation
- Attempted `python -m pip install -e .` (failed due network/proxy restrictions resolving `setuptools>=64`).
- Attempted `taurworks project where` (failed because editable install did not complete, so `taurworks` command was unavailable).
- Ran `PYTHONPATH=src python -m taurworks.cli project where`.
- Ran `PYTHONPATH=src python -m unittest discover tests '*_test.py'`.
- Ran `scripts/test` (fails in current environment without editable install).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_WHERE)[STAGE_2/2026-04-27]" --work-item AD_HOC --slug taurworks-project-where-stage-2 --status landed` (script missing in repository).

# Follow-up
- Add or restore `scripts/prompts/record-execution` if prompt-workflow automation is required in this repository branch.
- Consider normalizing local test bootstrap so `scripts/test` can run without requiring a successful networked editable install.
