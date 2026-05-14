---
prompt_id: "PROMPT(TAURWORKS_PACKAGE_SHELL_HELPER)[IMPLEMENT/2026-05-14]"
work_item: "AD_HOC"
slug: "taurworks-package-shell-helper"
status: "landed"
date: "2026-05-14"
---

# Summary
Packaged and exposed the Taurworks sourceable `tw` shell helper so installed
packages can print the helper without relying on a source checkout.

# Result
- Moved the helper into `src/taurworks/resources/shell/taurworks-shell.sh`.
- Included the helper as setuptools package data.
- Added `taurworks shell print` to print the packaged helper to stdout.
- Documented `pipx install taurworks`, manual helper redirection, manual
  sourcing, and the safety boundary between `taurworks project activate --print`
  and sourced `tw activate`.
- Added tests for package-resource readability and `taurworks shell print`.
- `taurworks shell install --to PATH` was not implemented in this focused PR;
  documented redirection remains the manual install/copy path.

# Validation
- Passed: `./scripts/test`.
- Passed: `./scripts/lint`.
- Warning: `python -m pip install -e .` attempted but build isolation could not
  download `setuptools>=64` through the environment proxy (`403 Forbidden`).
- Passed: `python -m pip install -e . --no-build-isolation`.
- Passed: `PYTHONPATH=src python -m taurworks.cli shell print > /tmp/taurworks-shell.sh`.
- Passed: `grep 'tw' /tmp/taurworks-shell.sh`.
- Passed: `bash -c 'source /tmp/taurworks-shell.sh && type tw'`.
- Passed: `taurworks shell print > /tmp/taurworks-shell.sh` after editable
  install with `--no-build-isolation`.
- Passed: `python -m pip wheel --no-build-isolation --no-deps . -w /tmp/taurworks-wheelhouse`
  plus wheel inspection confirmed `taurworks/resources/shell/taurworks-shell.sh`
  is present.
- Warning: `scripts/prompts/record-execution` was not present in this checkout,
  so this record was created manually using `project/executions/README.md`.

# Follow-up
- Consider adding an explicit `taurworks shell install --to PATH [--force]`
  command in a later focused PR if users need copy semantics beyond shell
  redirection.
