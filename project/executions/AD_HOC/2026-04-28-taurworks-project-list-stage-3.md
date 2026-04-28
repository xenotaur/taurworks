---
prompt_id: "PROMPT(TAURWORKS_PROJECT_LIST)[STAGE_3/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-project-list-stage-3"
status: "landed"
date: "2026-04-28"
---

# Summary
Implemented `taurworks project list` as a read-only discovery command that reports discovery source, project count, discovered project entries, and stage limitations.
Updated repository scripts to make local validation reliable in offline/proxy-restricted environments.

# Result
- Added shared list-discovery diagnostics and stable output formatting in `src/taurworks/project_resolution.py`.
- Wired `taurworks project list` in `src/taurworks/cli.py` to use the shared diagnostics/formatting path.
- Added command tests for no-project behavior plus deterministic fixture discovery from current context and direct cwd children.
- Updated user-facing README and unified command-model design docs to document the now-implemented read-only `project list` command and its current discovery limitations.
- Updated `scripts/develop` to use `python -m pip install --no-build-isolation -e .` so editable install can succeed without downloading build requirements that are already available locally.
- Updated `scripts/test` to run unit tests with `PYTHONPATH=src` so source-layout imports are deterministic even when editable install is unavailable.

# Validation
- Attempted `python -m pip install -e .` (failed due to proxy/network restriction fetching build dependency `setuptools>=64`).
- Ran `scripts/develop` (succeeds in current environment using `--no-build-isolation` editable install).
- Attempted `taurworks project list` (failed because editable install did not complete, so `taurworks` command was unavailable).
- Attempted `taurworks project where` (failed because editable install did not complete, so `taurworks` command was unavailable).
- Ran `taurworks project list` (succeeds after `scripts/develop`).
- Ran `taurworks project where` (succeeds after `scripts/develop`).
- Ran `PYTHONPATH=src python -m taurworks.cli project list`.
- Ran `PYTHONPATH=src python -m taurworks.cli project where`.
- Ran `PYTHONPATH=src python -m unittest discover tests '*_test.py'`.
- Ran `scripts/test` (succeeds after script update to include `PYTHONPATH=src`).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_LIST)[STAGE_3/2026-04-27]" --work-item AD_HOC --slug taurworks-project-list-stage-3 --status landed` (script missing in repository).

# Follow-up
- Add or restore `scripts/prompts/record-execution` so prompt execution records can be generated through repository tooling.
- Consider making `scripts/test` robust for src-layout execution when editable install is unavailable.
