---
prompt_id: "PROMPT(TAURWORKS_SRC_LAYOUT_MIGRATION)[IMPLEMENT/2026-04-27]"
work_item: "AD_HOC"
slug: "taurworks-src-layout-migration"
status: "landed"
date: "2026-04-27"
---

# Summary
Migrated the Python package to a `src/` layout by moving `taurworks/` to `src/taurworks/` and updating packaging discovery in `setup.py`.

# Result
- `setup.py` now discovers packages from `src` via `find_packages(where="src")` and `package_dir={"": "src"}`.
- Added a small smoke test to assert `import taurworks` remains valid.
- Updated README with editable install/import/CLI verification instructions and noted `src/` layout.

# Validation
- Attempted to run `scripts/prompts/record-execution` but the helper script is not present in this repository checkout.
- Attempted editable install (`pip install -e .`), but this environment could not fetch/import build backend dependencies due network/proxy constraints.
- Ran import checks outside repo root, CLI help, and unit tests with the available environment.

# Follow-up
- Optionally add `scripts/prompts/record-execution` helper if prompt-workflow automation is desired in this repository.
