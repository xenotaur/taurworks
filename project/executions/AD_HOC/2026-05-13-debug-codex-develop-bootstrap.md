---
prompt_id: "PROMPT(AD_HOC:DEBUG_CODEX_DEVELOP_BOOTSTRAP)[2026-05-13T16:05:00-04:00]"
work_item: "AD_HOC"
slug: "debug-codex-develop-bootstrap"
status: "in_progress"
date: "2026-05-13"
---

# Summary
Debugged the Codex Cloud bootstrap failure when the environment setup command was changed to `./scripts/develop`.

# Result
- No prior exact execution record was found for this prompt ID.
- `pyproject.toml` declares the PEP 517 build backend as `setuptools.build_meta` with build requirements `setuptools>=64` and `wheel`.
- `setup.py` is the package metadata file that declares extras. Before this change it declared `dev` with `black` and `ruff`, but did not declare `test`, so `.[test]` was stale/missing as a developer-tool setup path.
- `constraints-dev.txt` constrained Black and Ruff, but did not include the build backend prerequisites required when build isolation is disabled.
- `scripts/develop` used `python -m pip install --no-build-isolation -e ".[dev]" -c constraints-dev.txt`, which made the editable install depend on `setuptools.build_meta` already being importable in the active Python environment.
- Root cause: `scripts/develop` disabled build isolation for proxy-restricted environments before ensuring the active environment contained the declared build backend. In a Python 3.12 venv created without `setuptools`, the lower-level command reproduced the Codex failure with `pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'setuptools.build_meta'`.
- Normal build isolation was not a reliable alternative in this Codex environment: `python -m pip install -e ".[dev]" -c constraints-dev.txt` failed while trying to fetch `setuptools>=64` through the configured proxy (`Tunnel connection failed: 403 Forbidden`).
- Implemented the smallest fix that preserves `./scripts/develop` as the shared setup path: added constrained `setuptools` and `wheel` bootstrap entries, made `scripts/develop` install those backend prerequisites before the no-build-isolation editable install, retained `dev` as the formatter/linter developer extra, and added an empty `test` compatibility extra because tests currently use only standard-library `unittest`.
- Updated `README.md` to document `./scripts/develop`, `./scripts/lint`, `./scripts/test`, `./scripts/format --check --diff`, and the recommended Codex Cloud setup command.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- Attempted to read `project/executions/README.md` (failed: file is not present in this repository checkout).
- Attempted `scripts/prompts/check-execution --prompt-id "PROMPT(AD_HOC:DEBUG_CODEX_DEVELOP_BOOTSTRAP)[2026-05-13T16:05:00-04:00]" --project-root .` (failed: script not present in repository).
- Checked for a prior exact prompt execution record with `rg -n 'prompt_id: "PROMPT\(AD_HOC:DEBUG_CODEX_DEVELOP_BOOTSTRAP\)\[2026-05-13T16:05:00-04:00\]"|DEBUG_CODEX_DEVELOP_BOOTSTRAP' project PROMPTS.md scripts`; no exact prior execution record was found.
- Inspected `pyproject.toml`, `setup.py`, `constraints-dev.txt`, `environment.yml`, `scripts/develop`, `scripts/lint`, `scripts/format`, `scripts/test`, `.github/workflows/python-ci.yml`, `README.md`, `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, and project execution records mentioning setup behavior.
- Ran `python --version` (Python 3.12.13).
- Ran `python -m pip --version` (pip 26.1.1 from the Python 3.12.13 environment).
- Ran `python -m pip list | grep -E 'pip|setuptools|wheel|black|ruff' || true` (found pip 26.1.1, setuptools 82.0.1, wheel 0.47.0, black 26.3.1, and ruff 0.15.12).
- Ran the requested Python import diagnostic (found `setuptools: 82.0.1` and `setuptools.build_meta: OK` in the active environment).
- Ran pre-change `./scripts/develop` in the active environment (pass because the active environment already had `setuptools.build_meta`).
- Ran the former environment recipe `python -m pip install --upgrade pip setuptools wheel && python -m pip install -e ".[test]"` (failed under build isolation when pip tried to fetch `setuptools>=64` through the proxy; the proxy returned `Tunnel connection failed: 403 Forbidden`).
- Ran pre-change `python -m pip install --no-build-isolation -e ".[dev]" -c constraints-dev.txt` in the active environment (pass because `setuptools.build_meta` was already installed).
- Ran `python -m pip install -e ".[dev]" -c constraints-dev.txt` (failed under build isolation while trying to fetch `setuptools>=64` through the proxy; this confirmed removing `--no-build-isolation` is not the best fix in this environment).
- Created a temporary Python 3.12 venv with `python -m venv --without-pip`, bootstrapped pip with `ensurepip`, confirmed `setuptools` and `setuptools.build_meta` imports failed, then ran `/tmp/taurworks-nobuildbackend/bin/python -m pip install --no-build-isolation -e ".[dev]" -c constraints-dev.txt` (reproduced `BackendUnavailable: Cannot import 'setuptools.build_meta'`).
- After the fix, ran `PATH=/tmp/taurworks-bootstrap-test/bin:$PATH ./scripts/develop` in a temporary venv with pip but no setuptools (failed at the new bootstrap step because the Codex proxy blocked package-index access; this is an external environment limitation for a fresh environment without cached/preinstalled backend wheels, not the original repo-side backend import failure).
- Ran `python -m pip install --no-build-isolation -e ".[test]" -c constraints-dev.txt` (pass; confirms the compatibility `test` extra is now valid under the no-build-isolation path).
- Ran final `./scripts/develop` (pass in the active Codex environment with constrained backend prerequisites present).
- Ran final `./scripts/lint` (pass).
- Ran final `./scripts/test` (pass; 47 tests).
- Ran final `./scripts/format --check --diff` (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(AD_HOC:DEBUG_CODEX_DEVELOP_BOOTSTRAP)[2026-05-13T16:05:00-04:00]" --work-item AD_HOC --slug debug-codex-develop-bootstrap --status in_progress` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Recommended Codex Cloud environment setup after this PR: `./scripts/develop`.
- If Codex Cloud starts from a Python environment that has pip but lacks `setuptools` and `wheel`, the new script will try to install the constrained backend prerequisites first. That still requires either package-index access or a preinstalled/cacheable copy of the constrained packages; the current session's proxy returned 403 for fresh downloads.
- Keep using `./scripts/develop`, `./scripts/lint`, and `./scripts/test` in CI/local/Codex setup rather than ad-hoc pinned Black/Ruff installs.
- Add or restore `scripts/prompts/check-execution`, `scripts/prompts/record-execution`, and `project/executions/README.md` if the prompt workflow is expected to be fully tool-driven in this repository state.
