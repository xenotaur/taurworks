---
prompt_id: "PROMPT(AD_HOC:ALIGN_CI_DEV_TOOLS)[2026-05-13T13:15:00-04:00]"
work_item: "AD_HOC"
slug: "align-ci-dev-tools"
status: "in_progress"
date: "2026-05-13"
---

# Summary
Aligned Taurworks CI with the repository-local constrained developer setup path.

# Result
- Found CI/developer-tool drift: `.github/workflows/python-ci.yml` installed `black==24.10.0` and `ruff==0.6.9` directly, while `environment.yml` recorded newer local tool pins (`black==26.3.1` and `ruff==0.15.12`).
- Added `constraints-dev.txt` as the canonical exact-version source for Black and Ruff.
- Added a minimal `dev` extra in `setup.py` so developer tools are abstract package metadata while exact versions remain constrained by `constraints-dev.txt`.
- Updated `scripts/develop` to install `taurworks` in editable developer mode with `constraints-dev.txt` and print Python, pip, Black, and Ruff versions for drift diagnostics.
- Updated GitHub Actions to call `./scripts/develop` instead of hand-installing pinned Black/Ruff versions.
- Updated `scripts/lint` to run Black check mode with `--diff`, and updated `scripts/format` to pass through options such as `--check --diff`.
- Updated `README.md` to document `./scripts/develop`, local quality commands, CI alignment, and Codex Cloud guidance to avoid ad-hoc formatter/linter installs.
- Removed Black/Ruff pins from `environment.yml` so those exact versions live only in `constraints-dev.txt`.
- Branch: `work`; PR link: not yet known in this environment.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- Attempted to read `project/executions/README.md` (failed: file is not present in this repository checkout).
- Attempted `scripts/prompts/check-execution --prompt-id "PROMPT(AD_HOC:ALIGN_CI_DEV_TOOLS)[2026-05-13T13:15:00-04:00]" --project-root .` (failed: script not present in repository).
- Checked for a prior exact prompt execution record with `rg -n 'prompt_id: "PROMPT\(AD_HOC:ALIGN_CI_DEV_TOOLS\)\[2026-05-13T13:15:00-04:00\]"' project/executions`; no exact prior execution record was found.
- Inspected `.github/workflows/python-ci.yml`, `scripts/develop`, `scripts/lint`, `scripts/format`, `scripts/test`, related scripts, `pyproject.toml`, `setup.py`, `environment.yml`, README documentation, and project-control docs mentioning CI/developer setup.
- Ran `./scripts/develop` (pass; pip upgrade lookup emitted repeated `Tunnel connection failed: 403 Forbidden` warnings against the configured package index, but the installed pip was already current enough and the constrained editable install succeeded with existing/cached tools).
- Ran `./scripts/lint` (pass).
- Ran `./scripts/test` (pass).
- Ran `./scripts/format --check --diff` (pass).
- Ran `./scripts/smoke` (pass).
- Ran a small workflow sanity check to confirm `.github/workflows/python-ci.yml` contains `./scripts/develop`, `./scripts/lint`, and `./scripts/test` entries (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(AD_HOC:ALIGN_CI_DEV_TOOLS)[2026-05-13T13:15:00-04:00]" --work-item AD_HOC --slug align-ci-dev-tools --status in_progress` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Codex Cloud agents should run `./scripts/develop`, then `./scripts/lint` and `./scripts/test`; they should not install Black/Ruff with ad-hoc pinned commands because `constraints-dev.txt` is the repository source of truth.
- If Codex Cloud package-index proxy restrictions persist, preinstall/cache the versions in `constraints-dev.txt` or configure package-index access before relying on `./scripts/develop` in a fresh environment.
- Add or restore `scripts/prompts/check-execution`, `scripts/prompts/record-execution`, and `project/executions/README.md` if the prompt workflow is expected to be mandatory in this repository state.
