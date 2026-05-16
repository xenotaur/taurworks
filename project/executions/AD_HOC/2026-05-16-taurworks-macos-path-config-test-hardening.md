---
prompt_id: "PROMPT(TAURWORKS_MACOS_PATH_CONFIG_TEST_HARDENING)[TEST/2026-05-16]"
work_item: "AD_HOC"
slug: "taurworks-macos-path-config-test-hardening"
status: "landed"
date: "2026-05-16"
---

# Summary
Hardened Taurworks tests against macOS path canonicalization differences and accidental reads or writes of real user-global config.

# Result
- Added shared test helpers for semantic path normalization, path assertions, and CLI diagnostic field parsing.
- Updated CLI, global config, project registry, project resolution, and shell-helper tests to compare path fields semantically and to isolate `HOME`/`XDG_CONFIG_HOME` where global config may be consulted.
- Added `scripts/test-portability` to run the unittest suite with temporary `HOME`, `XDG_CONFIG_HOME`, and `TAURWORKS_WORKSPACE` values.
- Expanded Python CI to run on Ubuntu and macOS and to include the portability test script.
- Updated README testing guidance for macOS canonical paths, isolated global config, and the portability check.

# Validation
- `python -m pip install -e .` failed because build isolation attempted to fetch `setuptools>=64` from a network index blocked by a 403 proxy response.
- `scripts/lint` passed.
- `scripts/test` passed.
- `scripts/test-portability` passed.
- `scripts/prompts/record-execution` was requested by the prompt but is not present in this checkout, so this execution record was created manually according to `project/executions/README.md`.

# Follow-up
None.
