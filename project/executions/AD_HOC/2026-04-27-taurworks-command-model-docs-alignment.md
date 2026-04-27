---
prompt_id: "PROMPT(TAURWORKS_COMMAND_MODEL_DOCS_ALIGNMENT)[DOCS/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-command-model-docs-alignment"
status: "landed"
date: "2026-04-27"
---

# Summary
Aligned repository documentation around the current Taurworks command model and phased roadmap.

# Result
- Updated top-level README with the one-executable model, namespace responsibilities, compatibility-first status, and guardrails.
- Updated unified command model documentation to clearly mark planned vs implemented behavior, shared config/discovery intent, migration constraints, and shell-safety constraints.
- Expanded safety guardrails to clarify print-vs-modify command expectations and parent-shell mutation limits.
- Updated roadmap with explicit in-scope vs out-of-scope boundaries for the current phase.

# Validation
- Attempted editable install: failed in this environment due to unavailable package index/proxy for build dependencies.
- Ran `scripts/test`: failed because `taurworks` package is not importable without editable install in this environment.
- Ran `PYTHONPATH=src python -m taurworks.cli --help`: passed as a local smoke test for current CLI command surface.
- Ran `taurworks --help`: failed because the console entry point is unavailable without successful editable install.

# Follow-up
- Re-run package install and canonical CLI smoke tests in an environment with package-index access.
- The prompt workflow script `scripts/prompts/record-execution` is not present in this repository checkout; execution record was written manually.
