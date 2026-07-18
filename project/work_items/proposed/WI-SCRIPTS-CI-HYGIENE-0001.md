---
resolution: null
blocked_reason: null
blocked: false
id: WI-SCRIPTS-CI-HYGIENE-0001
title: Close scripts/ and CI hygiene gaps found in LRH-benchmarked audit
type: operation
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_activation_work
  - implement_trust_gating
  - add_actionlint_or_precommit
  - publish_package
acceptance:
  - scripts/version runs standalone and prints python/pip/black/ruff versions
  - scripts/check-workflows runs standalone and validates .github/workflows/*.yml syntax
  - .github/workflows/python-ci.yml runs check-workflows and version-reporting steps ahead of lint, with lint/test/test-portability/smoke unchanged
  - scripts/build produces a dist/ directory containing a wheel and sdist from a clean checkout
  - scripts/clean removes dist/, build/, *.egg-info, __pycache__, .ruff_cache with no other side effects
  - scripts/publish's "please run build first" message is verified true after scripts/build has run
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - scripts/version
  - scripts/check-workflows
  - scripts/build
  - scripts/clean
  - .github/workflows/python-ci.yml
---

# WI-SCRIPTS-CI-HYGIENE-0001: Close scripts/ and CI hygiene gaps found in LRH-benchmarked audit

## Summary
Close the scripts/ and CI hygiene gaps found by an LRH-benchmarked audit of
taurworks: add standalone tool-version reporting and workflow-YAML
validation to close a small, already-assessed CI gap, and add
`scripts/build`/`scripts/clean` to fix a currently-false cross-reference in
`scripts/publish` and round out basic dev hygiene.

## Problem / Context
A read-only audit benchmarked taurworks's `scripts/` and CI against
LogicalRoboticsHarness (LRH) conventions, reusing the "CI ↔ local script
drift" friction pattern and LRH's `assess-continuous-integration-status`
request template. Applying that template's checklist against taurworks
produced a final status of `PROCEED_WITH_ADAPTATION`: taurworks's CI
(`.github/workflows/python-ci.yml`) is already deliberately LRH-style
(commit `79c8969`), so this is a small additive slice, not a migration —
the gap is a missing standalone version-report command and a missing
workflow-YAML validation step, both named in LRH's normal validation
sequence. Independently, `scripts/publish`'s failure branch claims "No dist
directory found, please run build first" while no `scripts/build` exists,
and `scripts/clean` is the standard companion gap. Both groups are too
small individually to justify separate tracking overhead, so they're
combined into one work item with two independently landable task groups.

## Scope
- Add `scripts/version`: standalone tool-version report (python, pip,
  black, ruff), replacing the version-printing currently only available as
  a side effect of `scripts/develop`.
- Add `scripts/check-workflows`: lightweight YAML syntax validation of
  `.github/workflows/*.yml`.
- Wire both into `.github/workflows/python-ci.yml` as validation steps
  ahead of lint.
- Add `scripts/build`: minimal sdist/wheel build so `scripts/publish`'s
  existing failure message becomes true.
- Add `scripts/clean`: remove `dist/`, `build/`, `*.egg-info`,
  `__pycache__`, `.ruff_cache`.

## Required Changes
1. Create `scripts/version` (executable, matching the bash conventions of
   the other `scripts/*` entries): prints `python --version`,
   `pip --version`, `black --version`, `ruff --version`. Must run standalone
   without requiring `scripts/develop` to have just run.
2. Create `scripts/check-workflows` (executable): validates YAML syntax for
   every file under `.github/workflows/*.yml`. Use only what's already
   available (stdlib or already-installed packages) — do not add a new
   dependency or actionlint.
3. Edit `.github/workflows/python-ci.yml`: add a "Check workflows" step
   running `./scripts/check-workflows` and a "Report tool versions" step
   running `./scripts/version`, both ahead of the existing Lint step. Keep
   `scripts/develop` as setup/bootstrap only — do not fold these into it.
4. Create `scripts/build` (executable): produce sdist/wheel into `dist/`.
5. Create `scripts/clean` (executable): remove `dist/`, `build/`,
   `*.egg-info`, `__pycache__`, and `.ruff_cache` from the repo root.
6. No change to `scripts/publish`'s upload/publish logic — only its
   preconditions become real once `scripts/build` exists.

## Non-Goals
- Do not touch activation, trust-gating, or any dogfood-recovery-plan
  surface area (tracked separately: WI-INTERIM-TL-PIPX-0001,
  WI-LEGACY-BATCH-MIGRATION-0001, WI-ACTIVATION-PRODUCERS-0001,
  WI-TRUSTED-LEGACY-SOURCING-0001).
- Do not add actionlint, pre-commit, tox/nox, or dev containers — no
  repository evidence they're warranted.
- Do not implement PyPI publish readiness — taurworks is not published to
  PyPI (explicit roadmap out-of-scope item).
- Do not widen the CI Python version matrix (currently 3.11 only).
- Do not restructure `scripts/lint` or `scripts/format` — their existing
  `--check --diff` passthrough already satisfies the LRH format-check
  semantic.

## Acceptance Criteria
- `scripts/version` runs standalone and prints python/pip/black/ruff
  versions.
- `scripts/check-workflows` runs standalone, fails on invalid YAML, and
  passes on the current `.github/workflows/python-ci.yml`.
- `.github/workflows/python-ci.yml` runs check-workflows and
  version-reporting steps ahead of lint; existing lint/test/test-portability
  /smoke steps are unchanged.
- `scripts/build` produces a `dist/` directory containing a wheel and sdist
  from a clean checkout.
- `scripts/clean` removes `dist/`, `build/`, `*.egg-info`, `__pycache__`,
  `.ruff_cache` with no other side effects.
- Running `scripts/build` then `scripts/publish` reaches the twine-upload
  branch instead of the missing-dist branch.
- `lrh validate` passes with 0 errors.
- `scripts/test` and `scripts/lint` pass.

## Validation
- `scripts/version`
- `scripts/check-workflows`
- `scripts/lint`
- `scripts/test`
- `scripts/build`
- `scripts/clean`
- `lrh validate`

## Risk Notes
- `scripts/check-workflows` must stay dependency-light — confirm what's
  already available before choosing a YAML-parsing approach.
- `scripts/build` must not mutate `setup.py`/`pyproject.toml` packaging
  metadata as a side effect of testing the build.

## Dependencies / Order
Independent of the dogfood-recovery-plan work items; can be picked up any
time. The two groups (CI slice; build/clean) are independent of each other
and may land as separate PRs.
