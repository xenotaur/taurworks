---
id: WI-DEV-WORKFLOW-AUTOMATION-0001
title: Add taurworks dev workflow automation v1 (clean/test/smoke/lint/format/build)
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-CURRENT
related_roadmap:
  - ROADMAP-INIT
related_workstreams: []
depends_on: []
blocked_by: []
forbidden_actions:
  - force_push
  - delete_branch
  - implement_init_command
  - implement_develop_command
  - implement_coverage_command
  - implement_update_command
  - implement_precommit_command
  - implement_publish_command
  - implement_sandbox_command
  - implement_version_command
  - implement_validate_command
  - implement_tier3_builtin_defaults
acceptance:
  - "taurworks dev clean/test/smoke/lint/format/build subcommands exist, each resolving via Tier 1 (an explicit command string in .taurworks/config.toml's new [dev.commands] table, e.g. test = \"pytest -x\", parsed with shlex.split and executed without shell=True) then Tier 2 (a project-local script at <base_dir>/scripts/<name>, executed directly as an argv list, not through a shell), where <base_dir> reuses dev.py's existing gather_dev_where_diagnostics() work_directory_guess precedence (configured working_dir, else nearest .git root, else detected project root, else cwd)"
  - "the delegated subprocess's exit code is returned unchanged as taurworks dev <command>'s own exit code, and its stdout/stderr stream live (inherited, not captured-then-reprinted)"
  - "when neither tier resolves for a given command, taurworks dev <command> exits non-zero with a message naming the command and both locations checked ([dev.commands].<name> and the resolved script path) -- never a silent no-op"
  - "run from this repo's own root, taurworks dev clean/test/smoke/lint/format/build each delegate to the matching ./scripts/<name> and produce the same exit code and output as running that script directly"
  - "tests cover Tier 1 resolution, Tier 2 resolution, Tier 1 taking precedence over Tier 2 when both are present, the neither-resolves failure path, and exit-code passthrough for at least one command"
  - "README.md documents the six new dev commands, the two-tier resolution order, and the [dev.commands] config table"
artifacts_expected:
  - src/taurworks/dev.py
  - src/taurworks/cli.py
  - src/taurworks/project_internals.py
  - README.md
  - tests/dev_test.py
  - tests/cli_test.py
---

# WI-DEV-WORKFLOW-AUTOMATION-0001: Add taurworks dev workflow automation v1 (clean/test/smoke/lint/format/build)

## Summary

Add `taurworks dev clean/test/smoke/lint/format/build` as delegate-only
workflow commands, resolving via an explicit `.taurworks/config.toml`
override (Tier 1) then a project-local `scripts/<name>` file (Tier 2), per
`project/design/design.md`'s "Dev command resolution model". This is the
v1 scope decided 2026-07-31 (`project/roadmap/roadmap.md` Phase 6) for
expanding `taurworks dev ...` beyond its current read-only
`where`/`status` diagnostics.

## Problem / Context

`taurworks dev ...` has offered only read-only diagnostics (`dev where`,
`dev status`) since Phase 4. `project/design/design.md` and
`project/design/unified_command_model.md` have long specified a full `dev`
namespace (`init`, `clean`, `develop`, `test`, `smoke`, `coverage`, `lint`,
`format`, `build`, `update`, `precommit`, `publish`, `sandbox`, `version`,
`validate`) and a 3-tier resolution model (explicit configured command →
project-local script → built-in default by project type), but no dev
workflow command beyond diagnostics has ever been implemented, and the
roadmap left "deciding scope for `taurworks dev ...` workflow automation"
as an explicitly open, undecided question (`project/roadmap/roadmap.md`
Phase 4, `project/focus/current_focus.md`).

That scope was decided 2026-07-31 after reviewing the existing design
docs and this repo's own layout: this repo's `scripts/` directory already
has `clean`, `develop`, `test`, `smoke`, `lint`, `format`, and `build` --
seven of the fifteen specified commands. Of those, six (`clean`, `test`,
`smoke`, `lint`, `format`, `build`) are conventional, reversible-or-
regenerable operations with no side effect beyond their stated purpose,
making delegation to them immediately dogfoodable with no new
script-writing required. `develop` was initially considered for v1 too,
but review of the decision caught that this repo's own `scripts/develop`
actually runs `pip install` (constrained developer-mode setup) --
dependency-mutating, not reversible -- so it was moved into the deferred
set alongside `update`. The remaining seven deferred commands (`init`,
`coverage`, `update`, `precommit`, `publish`, `sandbox`, `version`,
`validate`) either lack an existing script to delegate to, or are
higher-risk (irreversible, packaging/release, dependency-mutating) per
`design.md`'s "Transparency and safety" section and `roadmap.md`'s Phase
6. Tier 3 (built-in per-project-type defaults) has no concrete design yet
and is also deferred -- this item is Tier 1 + Tier 2 delegation only.

Also decided as part of this scoping: `design.md`'s "higher-risk commands"
list and `roadmap.md`'s Phase 6 deferred-commands list had drifted out of
sync with each other (`design.md` listed `clean` as higher-risk while
`roadmap.md` did not, and vice versa for `version`/`validate`). Both docs
were reconciled to agree on the same v1/deferred split before this work
item was drafted.

**Prior-art check:**
- *Duplication search* -- in-repo: `src/taurworks/dev.py` currently
  implements only `gather_dev_where_diagnostics`/`gather_dev_status_diagnostics`
  and their formatters; no delegation or subprocess-invocation logic
  exists there or anywhere else in `src/taurworks/`. `manager.py`'s
  `create_conda_environment`/`create_project`/`refresh_project` invoke
  `subprocess.run` for Conda operations, an unrelated code path. Sibling
  repos: none identified. External libraries: none applicable
  (taurworks-specific delegation semantics). Recommendation: proceed.
- *Demand search* -- `project/roadmap/roadmap.md` Phase 6 and
  `project/focus/current_focus.md` (both updated 2026-07-31) are the only
  work items/design docs requesting this; no other proposed or resolved
  work item covers it. Recommendation: proceed.

## Scope

- Add `taurworks dev clean`, `taurworks dev test`, `taurworks dev smoke`,
  `taurworks dev lint`, `taurworks dev format`, and `taurworks dev build`
  subcommands.
- Implement Tier 1 (explicit `[dev.commands]` config override) and Tier 2
  (project-local `scripts/<name>` delegation) resolution only.
- Fail clearly, never silently, when neither tier resolves.
- Document the new commands and config table in README.md.

## Required Changes

1. `src/taurworks/project_internals.py`: add a `dev_command_from_config(config, name)` accessor
   reading `.taurworks/config.toml`'s `[dev.commands]` table (e.g.
   `[dev.commands]\ntest = "pytest -x"`), returning the configured string or
   `None`, following the existing pattern of
   `activation_exports_from_config`/`working_dir_from_config`.
2. `src/taurworks/dev.py`: add a resolution function that, given a command
   name, returns either a Tier 1 shell-split argv (via `shlex.split` on the
   configured string, never `shell=True`), a Tier 2 argv (the resolved
   `scripts/<name>` path plus no extra args in v1), or a clear failure
   naming both locations checked. Reuse
   `gather_dev_where_diagnostics()`'s existing `work_directory_guess`
   resolution (configured `working_dir`, else nearest `.git` root, else
   detected project root, else cwd) as the base directory both tiers
   resolve `.taurworks/config.toml` and `scripts/<name>` against.
3. `src/taurworks/dev.py`: add an execution function that runs the
   resolved argv via `subprocess.run` with inherited stdio (no
   `capture_output`), and returns the child's exit code unchanged.
4. `src/taurworks/cli.py`: add `clean`, `test`, `smoke`, `lint`, `format`,
   and `build` subparsers under `dev`, wired through `_handle_dev_command`
   to the new resolution/execution functions, with `raise SystemExit(<code>)`
   propagating the delegated command's exit code.
5. `tests/dev_test.py`: add cases for Tier 1 resolution, Tier 2 resolution,
   Tier 1 taking precedence when both are configured, the
   neither-resolves failure path (clear message, non-zero exit, no
   subprocess invoked), and exit-code passthrough (a fake script/configured
   command that exits non-zero).
6. `tests/cli_test.py`: add an end-to-end case delegating to a real
   `scripts/<name>`-style fixture script via a real subprocess CLI
   invocation, confirming stdout is inherited and the exit code matches.
7. `README.md`: document the six new `taurworks dev` commands, the
   two-tier resolution order, and the `[dev.commands]` config table syntax.

## Non-Goals

- `taurworks dev init`, `dev develop`, `dev coverage`, `dev update`,
  `dev precommit`, `dev publish`, `dev sandbox`, `dev version`,
  `dev validate` -- all explicitly deferred per `roadmap.md` Phase 6
  (separate future work item(s)). `develop` in particular is deferred
  despite having an existing script, because `scripts/develop` runs `pip
  install` and is therefore dependency-mutating, not reversible.
- Tier 3 (built-in per-project-type defaults) -- no concrete design exists
  yet; this item is Tier 1 + Tier 2 only.
- Extra-argument passthrough (e.g. `taurworks dev test -- -k foo`) --
  keeping v1 narrow; a natural follow-up once the core delegation shape is
  proven.
- Any change to `manager.py`'s legacy top-level commands or `tw`'s shell
  helper.
- Replacing standard tools with a new build/lint/test/package system, per
  `design.md`'s existing non-goal -- these commands only delegate to
  tooling the project already configures or scripts itself.

## Acceptance Criteria

- `taurworks dev clean/test/smoke/lint/format/build` subcommands exist,
  each resolving via Tier 1 (`[dev.commands].<name>` in
  `.taurworks/config.toml`, `shlex.split`, no `shell=True`) then Tier 2
  (`<base_dir>/scripts/<name>`, executed directly as an argv list), using
  the same base-directory precedence as `dev where`'s
  `work_directory_guess`.
- The delegated subprocess's exit code is returned unchanged as
  `taurworks dev <command>`'s own exit code, and its stdout/stderr stream
  live (inherited, not captured-then-reprinted).
- When neither tier resolves, `taurworks dev <command>` exits non-zero
  with a message naming the command and both locations checked -- never a
  silent no-op.
- Run from this repo's own root, each of the six commands delegates to
  the matching `./scripts/<name>` and produces the same exit code and
  output as running that script directly.
- Tests cover Tier 1 resolution, Tier 2 resolution, Tier 1
  precedence-over-Tier 2, the neither-resolves failure path, and
  exit-code passthrough.
- README.md documents the six commands, the resolution order, and the
  `[dev.commands]` config table.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- manual dogfood: run each of the six taurworks dev commands from this repo's own root and confirm they delegate to the matching ./scripts/<name>
- lrh validate

## Risk Notes

- Tier 1's configured command string must never be run with `shell=True`:
  `shlex.split` plus a direct argv `subprocess.run` call avoids shell
  injection even though the string originates from trusted local project
  config, matching this codebase's existing preference for explicit,
  inspectable subprocess invocation over shell interpretation.
- Tier 2's `scripts/<name>` must be resolved and checked for
  existence/executability before invocation, with a clear message if the
  file exists but isn't executable (a likely real mistake, distinct from
  "no script configured at all").
- Silently doing nothing when neither tier resolves would be a regression
  in kind to the WI-LEGACY-CONDA-GATING-0001/`--create-env` lesson this
  codebase already learned: a command that looks like it ran something
  but didn't is worse than a clear failure.
- `develop` was deliberately excluded from v1 despite having an existing
  script, precisely because "has an existing script" and "is safe to
  delegate to by default" are different questions -- a future WI adding
  `develop` (or any other deferred command) must independently verify its
  script's side effects, not just its existence.
