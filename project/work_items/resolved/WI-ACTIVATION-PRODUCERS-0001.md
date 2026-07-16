---
id: WI-ACTIVATION-PRODUCERS-0001
title: Add producer-side commands and guidance for activation environment config
type: deliverable
status: resolved
blocked: false
blocked_reason: null
resolution: "Implemented and merged in PR #69 (commit 51f090e): project env set/show, --env on create/init, legacy create/refresh convergence onto config.toml, three guidance-string fixes. Fresh-user end-to-end criterion verified live with real conda."
---

# WI-ACTIVATION-PRODUCERS-0001: Producer-side activation authoring and guidance

## Summary
Give taurworks the missing "producer side" of declarative activation: a CLI
writer for `[activation.environment]`, environment flags on project
create/init, convergence of legacy create/refresh onto `config.toml`, and
guidance strings that name the intended next step instead of dead-ending.

## Problem / Context
The 2026-07-11 dogfood session established that the activation consumer chain
(`config.toml` → `project activate --shell` → sourced `tw activate`) works
end-to-end, but no shipped command ever writes `[activation.environment]`:
`project create`/`init` write only schema/project/paths, there is no
`env set`-style command, and legacy `create`/`refresh` write a
`.taurworks/project-setup.source` script that nothing reads while reporting
"fully set up." A fresh user cannot reach Conda-switching activation using
only shipped commands — the missing end-to-end criterion that let every
prior slice be "done" while the product was not.

## Scope
- New `taurworks project env` subcommands (set/show) writing validated
  `[activation.environment]` data.
- `--env NAME` on `project create` and `project init`.
- Legacy `create`/`refresh` convergence onto `config.toml`.
- Guidance-string fixes in activation and refresh output.

## Required Changes
1. Add `taurworks project env set ENV_NAME [--project PATH_OR_NAME]` and
   `taurworks project env show [PATH_OR_NAME]` in `src/taurworks/cli.py` and
   the project-resolution layer, symmetric with the existing
   `project working-dir set/show`. Values are validated with the existing
   Conda-name validator in `src/taurworks/project_internals.py` and written
   with the safe TOML writer (`write_project_config`). Type remains `conda`.
2. Add `--env NAME` to `project create` and `project init`, recording
   `[activation.environment] type = "conda"` at initialization time.
3. Converge legacy `create`/`refresh` in `src/taurworks/manager.py`: write
   `.taurworks/config.toml` (environment name, working_dir set to the created
   repo directory) via the safe writer instead of generating
   `.taurworks/project-setup.source`; correct the "✔ Project X is fully set
   up" message to state what was and was not done.
4. Guidance strings: (a) the legacy-admin activation warning names
   `taurworks legacy migrate NAME --apply` as the next step; (b) activating
   an initialized project with no `[activation.environment]` prints a note
   naming `taurworks project env set`; (c) the workspace-only warning names
   `taurworks project init`.
5. Unit tests covering each new command, flag, convergence behavior, and
   guidance string.

## Non-Goals
- Do not implement any script sourcing or trust mechanism — that is
  WI-TRUSTED-LEGACY-SOURCING-0001.
- Do not add venv/Docker or any non-conda environment strategy.
- Do not remove or rename legacy top-level commands.
- Do not change export `~`-expansion semantics or the redaction/payload
  separation model.

## Acceptance Criteria
- End-to-end fresh-user test: starting with no project,
  `taurworks project create X --env X --working-dir x_repo
  --create-working-dir` followed by `tw activate X` in a real shell switches
  the Conda environment and changes directory, using only shipped commands.
- `taurworks project env set`/`show` round-trip a validated environment name
  and reject invalid ones before writing.
- Legacy `taurworks create NAME` no longer writes
  `.taurworks/project-setup.source` and the resulting project is
  activation-eligible (or its output states exactly what is missing).
- All three guidance strings appear in the appropriate activation/refresh
  outputs, covered by tests.
- `scripts/test` passes; `lrh validate` introduces no new errors.

## Validation
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Manual shell test of the fresh-user end-to-end criterion

## Risk Notes
- Convergence changes long-standing legacy command side effects; tests must
  pin the new contract so `tl`-era workflows are not silently broken (the
  Admin/ scripts `tl` reads are untouched by this item).
- `black` version drift between local anaconda and CI constraints has bitten
  this repo before; check before wide reformatting.
