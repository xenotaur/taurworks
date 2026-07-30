---
id: WI-TAURWORKS-DEBUG-FLAG-0001
title: Add --debug/TAURWORKS_DEBUG flag; gate manager.py narration and audit cli.py formatters
type: deliverable
status: resolved
blocked: false
blocked_reason: null
resolution: "Implemented and merged in PR #95 (commit d6c43cc86a53c1bb840b4b1860983e4a1fe2bb4a). Adds a global `--debug` flag / `$TAURWORKS_DEBUG` fallback (flag takes precedence), gating manager.py's create/refresh narration (all 56 print() calls audited) while keeping every final actionable result line unconditional in both success and failure paths. list_projects and activate_project needed no code change -- neither has separate narration to gate. Audit of cli.py's 5 formatter modules (global_config.py, project_resolution.py, project_registry.py, dev.py, legacy.py) plus cli.py itself found zero debug-shaped output anywhere -- every command already prints exactly one documented-result string; nothing gated as a result. Review caught one real bug (whitespace-only $TAURWORKS_DEBUG misclassified as truthy) -- fixed and independently re-verified. This completes all four work items drafted from project/design/packaging_and_install.md."
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
  - implement_setup_command
  - implement_bin_repo_split
  - implement_path_loss_diagnostic
  - remove_final_result_lines
acceptance:
  - "a global --debug flag exists on the top-level argparse parser (src/taurworks/cli.py), and an equivalent TAURWORKS_DEBUG environment variable is honored, with the flag taking precedence when both are set"
  - "all ~56 unconditional print() calls in src/taurworks/manager.py's create/refresh/activate commands move behind the debug flag, except each command's final actionable result line (e.g. \"To activate, run: tw activate {project_name}\", \"✔ Project '{project_name}' created successfully.\"), which stays unconditional; list_projects (the projects command) is treated differently: its listing output (the header/rows in the non-debug branch, and the \"No projects found\" line) is the command's actual result, not narration, and stays unconditional in its entirety — it has no single final result line to carve out, since the listing itself is the result"
  - "cli.py's formatter modules (global_config.py, project_resolution.py, project_registry.py, dev.py, legacy.py) are audited for output that is actually a debug trace versus the command's documented result; any genuinely debug-shaped output found is gated behind the same flag, and the audit's findings (including \"none found\" if that's the outcome) are recorded in this WI's resolution"
  - "tests cover both --debug/TAURWORKS_DEBUG on and off for at least one manager.py command, confirming narration is suppressed by default and shown when the flag/env var is set"
  - "README.md documents the new flag and env var"
artifacts_expected:
  - src/taurworks/cli.py
  - src/taurworks/manager.py
  - src/taurworks/global_config.py
  - src/taurworks/project_resolution.py
  - src/taurworks/project_registry.py
  - src/taurworks/dev.py
  - src/taurworks/legacy.py
  - README.md
  - tests/
---

# WI-TAURWORKS-DEBUG-FLAG-0001: Add --debug/TAURWORKS_DEBUG flag; gate manager.py narration and audit cli.py formatters

## Summary

Add a global `--debug` flag and `TAURWORKS_DEBUG` environment variable,
gate `src/taurworks/manager.py`'s ~56 unconditional progress-narration
`print()` calls behind it, and audit `cli.py`'s formatter modules for any
output that is actually debug-shaped rather than the command's documented
result. This is Decisions #5 from `project/design/packaging_and_install.md`.

## Problem / Context

`src/taurworks/manager.py`'s legacy top-level commands (`create`,
`refresh`, `activate`, `projects`) print 56 unconditional lines of
step-by-step narration (`"Creating Conda environment..."`, `"✔ Taurworks
config already up to date"`) with no flag to suppress them.
`src/taurworks/cli.py`'s namespaced commands already route through
formatter functions, which is the right shape, but nothing currently
distinguishes "normal result" from "debug trace" for either code path.

Review caught a real gap in the original "gate everything except the final
result line" framing: `list_projects` (backing the `projects` command,
`manager.py:467-517`) has no single final result line at all — its "No
projects found" line (line 471) and its entire "Available projects" header
plus per-project rows (lines 478-517) *are* the command's result, listed
incrementally rather than summarized in one closing line. Gating all of
`list_projects`'s prints as if they were narration would make `taurworks
projects` produce no output whatsoever by default, a real regression, not
a debug-noise cleanup. `projects` is therefore treated as a special case:
its listing output stays unconditional in its entirety, while `create`,
`refresh`, and `activate` keep the original narration-except-final-line
treatment, since each of those does have a distinct closing result line
separate from its step-by-step progress prints.

Prior art check: no existing `--debug`/`TAURWORKS_DEBUG` effort found
in-repo (`grep -rl "TAURWORKS_DEBUG\|--debug flag\|debug flag"` across work
items/roadmap/focus returns nothing). At the time this work item was
drafted no `FOCUS-*`/`ROADMAP-*` phase covered this; `project/focus/current_focus.md`
(`FOCUS-CURRENT`) and `project/roadmap/roadmap.md` (`ROADMAP-INIT` Phase 8)
have since been updated to cover this and the other three
`project/design/packaging_and_install.md` work items; `related_focus`/
`related_roadmap` above reflect that.

One of four work items drafted from `project/design/packaging_and_install.md`;
the others cover the `taurworks setup` command, the `bin/`/`taurscripts`
repo split, and the Conda PATH-loss diagnostic. This WI is scoped to the
debug-flag mechanism and the `manager.py`/`cli.py` output audit only.

## Scope

- Add the global `--debug` flag and `TAURWORKS_DEBUG` env var.
- Gate `manager.py`'s narration prints behind it, keeping final result
  lines unconditional for `create`/`refresh`/`activate`, and keeping
  `projects`'s entire listing output unconditional (it has no separate
  narration to gate — the listing is the result).
- Audit `cli.py`'s formatter modules; gate anything genuinely debug-shaped.
- Document the flag/env var in README.md.

## Required Changes

1. Add `--debug` to the top-level `argparse` parser in `src/taurworks/cli.py`.
2. Read `TAURWORKS_DEBUG` as a fallback when `--debug` is not passed; thread
   a single boolean through to command handlers.
3. In `src/taurworks/manager.py`, gate `create`/`refresh`/`activate`'s
   unconditional narration prints behind the debug flag, except each
   command's final actionable success/failure line. Treat `projects`
   (`list_projects`) differently: leave its entire listing output
   (the "No projects found" line and the "Available projects" header/rows)
   unconditional — it is the command's result, not narration, and has no
   separate final line to carve out from the rest.
4. Audit `global_config.py`, `project_resolution.py`, `project_registry.py`,
   `dev.py`, and `legacy.py` for debug-shaped output (internal resolution
   traces, intermediate diagnostic fields not needed for the command's
   stated purpose); gate anything found.
5. Update README.md to document `--debug`/`TAURWORKS_DEBUG`.

## Non-Goals

- The `taurworks setup` command (separate WI).
- The `bin/`/`taurscripts` repo split (separate WI).
- The Conda PATH-loss diagnostic in `tw` (separate WI).
- Per-command debug flags — one global boolean, not several independent
  ones per subcommand.
- Removing or changing any command's final actionable result line.

## Acceptance Criteria

- A global `--debug` flag exists on the top-level `argparse` parser
  (`src/taurworks/cli.py`), and an equivalent `TAURWORKS_DEBUG` environment
  variable is honored, with the flag taking precedence when both are set.
- All ~56 unconditional `print()` calls in `src/taurworks/manager.py`'s
  `create`/`refresh`/`activate` commands move behind the debug flag,
  except each command's final actionable result line (e.g. `"To
  activate, run: tw activate {project_name}"`, `"✔ Project
  '{project_name}' created successfully."`), which stays unconditional.
  `projects` (`list_projects`) is a special case: its listing output (the
  "No projects found" line and the "Available projects" header/rows) is
  the command's actual result, not narration, and stays unconditional in
  its entirety.
- `cli.py`'s formatter modules (`global_config.py`, `project_resolution.py`,
  `project_registry.py`, `dev.py`, `legacy.py`) are audited for output that
  is actually a debug trace versus the command's documented result; any
  genuinely debug-shaped output found is gated behind the same flag, and
  the audit's findings (including "none found" if that's the outcome) are
  recorded in this WI's resolution.
- Tests cover both `--debug`/`TAURWORKS_DEBUG` on and off for at least one
  `manager.py` command, confirming narration is suppressed by default and
  shown when the flag/env var is set.
- README.md documents the new flag and env var.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- lrh validate
