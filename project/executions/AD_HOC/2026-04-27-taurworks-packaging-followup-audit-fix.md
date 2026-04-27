---
prompt_id: "PROMPT(TAURWORKS_PACKAGING_FOLLOWUP)[AUDIT_FIX/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-packaging-followup-audit-fix"
status: "landed"
date: "2026-04-27"
---

# Summary
Audited post-migration packaging and updated repository metadata, scripts, tests, and docs to align with the `src/taurworks` layout and modern editable-install expectations.

# Result
- Added `pyproject.toml` with a modern setuptools build backend (`setuptools.build_meta`) and build requirements for PEP 517/660 editable installs.
- Kept existing package metadata and console script wiring in `setup.py` to minimize scope.
- Added a CLI help smoke test (`python -m taurworks.cli --help`) alongside import-path smoke coverage.
- Updated README install and smoke-test commands to use `python -m pip install -e .` and module CLI invocation.
- Updated remaining documentation references that still used pre-`src/` source paths.
- Corrected script messaging that still referenced the old package name (`treemi`).

# Validation
- `python -m pip install -e .` failed in this environment because build dependencies could not be fetched through the configured proxy.
- `python -m pip install -e . --no-build-isolation` reached the PEP 517 editable-check path but failed because `setuptools` is not installed in the runtime environment.
- With `PYTHONPATH=src`, smoke tests and CLI checks passed.

# Follow-up
- Re-run editable-install validation in an environment with network access (or preinstalled `setuptools>=64`) to confirm absence of legacy `setup.py develop` deprecation warnings end-to-end.
- `scripts/prompts/record-execution` was attempted but is not present in this repository checkout; this record was created manually following existing repository conventions.
