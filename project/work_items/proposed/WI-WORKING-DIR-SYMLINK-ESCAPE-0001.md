---
id: WI-WORKING-DIR-SYMLINK-ESCAPE-0001
title: Allow working_dir to be a symlink outside project_root (lexical containment)
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
  - implement_working_dir_trust_gate
  - implement_global_allowlist_of_external_roots
  - implement_name_mismatch_warning
  - implement_working_dir_link_helper_command
  - accept_absolute_or_dotdot_working_dir_values
  - change_project_root_registration_semantics
acceptance:
  - "`paths.working_dir` continues to reject absolute paths and any path containing a `..` component, evaluated against the literal, unresolved config value — unchanged from today"
  - "`paths.working_dir` is accepted when it names a path that is lexically a (possibly nested) child of `project_root`, even when that path is a symlink whose fully resolved target lies outside `project_root`"
  - "existence/is-directory checks continue to follow symlinks transparently (no change to that behavior), and a dangling symlink, symlink loop, or non-directory target still produces the existing error path"
  - "all four current call sites share the fix: `tw activate` / `taurworks project activate --print` (via `resolve_configured_working_dir`), `taurworks project working-dir show`, `taurworks project working-dir set`, and `taurworks project init`/`project create --working-dir`"
  - "the five existing tests that assert escape-rejection (`tests/project_internals_test.py::test_relative_working_dir_rejects_paths_outside_project_root`, and the four `\"may not escape\"` assertions in `tests/cli_test.py`) still pass unchanged for `..`/absolute inputs"
  - "new tests cover: a working_dir that is a symlink to a directory outside project_root (accepted), a working_dir containing `..` that also happens to traverse a symlink (still rejected), and a working_dir symlink that is dangling or loops (still an error)"
  - "no new config field, global allowlist, or trust-gate is introduced; `config_model.md`'s Tier 1/Tier 2 legacy-script trust model is untouched"
artifacts_expected:
  - src/taurworks/project_internals.py
  - project/design/config_model.md
  - project/design/design.md
  - tests/project_internals_test.py
  - tests/cli_test.py
---

# WI-WORKING-DIR-SYMLINK-ESCAPE-0001: Allow working_dir to be a symlink outside project_root (lexical containment)

## Summary

Change `working_dir` containment validation from a check against the fully
resolved (symlink-followed) path to a check against the literal, unresolved
config value. This lets `paths.working_dir` name a path that is itself a
symlink whose real target lies outside `project_root`, while continuing to
reject any config value that is absolute or contains a `..` component. This
implements the design decision recorded in `project/design/config_model.md`
("Working-dir containment and symlinked work trees") and
`project/design/design.md` (amending the "deferred unless a later design
explicitly accepts them" note).

## Problem / Context

A real, current workflow hit this: `project_root` (and non-code metadata —
`.taurworks/`, archival material) stays on a Google-Drive-synced `Workspace`
location, while the actual Git-tracked work tree moved to an SSD-local
`Tempspace` location to avoid Google Drive sync thrashing from active
builds, tests, and growing `git worktree` usage. The resulting on-disk
layout is a same-named symlink: `project_root/working_dir` is a symlink
whose target is an identically-named path under `Tempspace`, e.g.
`~/Workspace/Project/working_dir -> ~/Tempspace/.../Project/working_dir`.

`tw activate` currently fails for this layout with:

```text
tw activate: activation failed for Project.
tw activate: Configured working_dir is invalid or activation data could not
be read safely: working_dir must stay inside the project root and may not
escape with '..'. Run `taurworks project working-dir set [DIR]` from inside
the project to replace invalid working_dir metadata, or edit
.taurworks/config.toml to fix activation metadata.
```

The suggested remedy in that message (`taurworks project working-dir set
[DIR]`) does not actually work around the problem: it hits the identical
check (see Required Changes below), so it is currently a dead end for this
layout.

Root cause: `relative_working_dir` (`src/taurworks/project_internals.py:483-514`)
and `relative_working_dir_metadata` (`project_internals.py:539-565`) both
call `.resolve()` on the joined `project_root`/`working_dir` path *before*
testing containment via `Path.relative_to`. `.resolve()` follows symlinks to
their real target, so a symlink under `project_root` pointing outside it
always fails the containment check — the check was never actually guarding
against symlinks specifically; that's incidental fallout from reusing a
resolved-path containment test for what should be a lexical one. (This is
distinct from the existing, deliberate rejection of a *symlinked
`.taurworks/` metadata directory itself*, which is a different, intentional
safety rule — see `tests/project_internals_test.py:87-118,163-177` and
`tests/cli_test.py:1840-1864,2253-2288` — and is not in scope here.)

Options considered and rejected (see conversation history / prior design
discussion for full reasoning):

- Re-registering `project_root` at the Tempspace location: rejected because
  `project_root` also anchors non-code, Workspace-resident content
  (`.taurworks/`, archival material) that is not moving.
- A global config allowlist of trusted external roots, or a trust-gate
  modeled on the existing legacy-script Tier 1/Tier 2 mechanism: rejected as
  disproportionate. That mechanism exists to gate arbitrary code execution;
  a `working_dir` symlink only changes a `cd` target, a materially smaller
  blast radius, and placing the "allow" flag in project-local
  `.taurworks/config.toml` (which may be synced) would also violate this
  project's own stated principle that project content must never be able to
  grant itself trust (`src/taurworks/cli.py:880-883`).
- A hard error (or warning) when the symlink's name doesn't match its
  target's basename: rejected because it would be noisy/incorrect for
  legitimate `git worktree` layouts, where a workstream/worktree directory
  is deliberately named differently from the project it belongs to (this is
  not a hypothetical — it matches an already-observed real directory shape).

Prior art check: at the time this was drafted, no existing work item,
roadmap phase, or focus entry covered symlinked `working_dir` handling;
`config_model.md`'s existing `working_dir` section (`paths.working_dir`
relative/absolute rules) and `design.md:29`'s "Absolute working-directory
paths are deferred unless a later design explicitly accepts them" were the
only directly related prior decisions, both amended by this work item's
paired design change rather than contradicted. `project/focus/current_focus.md`
(`FOCUS-CURRENT`) and `project/roadmap/roadmap.md` (`ROADMAP-INIT` Phase 9)
have since been updated to cover this; `related_focus`/`related_roadmap`
above reflect that.

## Scope

- Change the containment check in `relative_working_dir` and
  `relative_working_dir_metadata` from resolved-path containment to lexical
  containment (reject absolute/`..` in the literal value; otherwise accept).
- Verify the fix propagates correctly to every caller of those two
  functions, without needing its own separate fix:
  - `resolve_configured_working_dir` (`project_internals.py:568-577`) — used
    by `tw activate` / `taurworks project activate --print`.
  - `set_working_dir` (`project_internals.py:517-536`) — used by `taurworks
    project working-dir set`.
  - `create_working_dir_metadata_target` (`project_internals.py:580-596`)
    and `set_working_dir_metadata` (`project_internals.py:599-635`) — used
    by `taurworks project init`/`project create --working-dir` and by
    `working-dir set`'s metadata-recording path.
- Update the five existing tests that assert today's escape-rejection
  behavior so they keep asserting it for `..`/absolute inputs specifically
  (not for symlinks), and add new tests for the symlink-permitted case and
  for symlink-loop/dangling-symlink failure modes.
- No shell-helper (`taurworks-shell.sh`) changes are expected; this is a
  pure `project_internals.py` validation change.

## Required Changes

1. In `relative_working_dir` (`project_internals.py:483-514`): stop calling
   `.resolve()` on the joined `cwd`/`raw_path` target before the containment
   check. Keep `cwd.resolve()` (trusted base), reject `raw_path.is_absolute()`
   and any `".."` in `raw_path.parts` exactly as today, then build the
   lexical target as `cwd_resolved / raw_path` without resolving `raw_path`'s
   own components. Use `.is_dir()` (which already follows symlinks) for the
   existence check; use `.resolve()` only when producing a path for display
   (e.g. the final `cd` target string), never for the containment gate.
2. Apply the equivalent change to `relative_working_dir_metadata`
   (`project_internals.py:539-565`), used by the no-cwd-context metadata
   path (`working-dir set`, `project init`/`create --working-dir`).
3. Confirm (via the new tests in step 5) that a symlink loop or a target
   that doesn't resolve still raises — this should fall out of existing
   `except (ProjectConfigError, OSError, tomllib.TOMLDecodeError)` handling
   in callers (`project_resolution.py:1753-1761,1983-1987`) without new
   exception plumbing, since `Path.resolve()`/`.is_dir()` already raise
   `OSError` on a loop.
4. Do not add any new config field, CLI flag, global allowlist, or
   trust-gate. Do not add a name-matching warning (see Problem/Context for
   why both were rejected as part of this change's design decision).
5. Update `tests/project_internals_test.py:156-161`
   (`test_relative_working_dir_rejects_paths_outside_project_root`) and the
   four `"may not escape"` assertions in `tests/cli_test.py` (around lines
   1427-1449, 1742, 2219-2250, 2544) to confirm they still exercise `..`
   specifically. Add new tests: (a) a `working_dir` that is a symlink to an
   external directory is accepted by both `relative_working_dir` and
   `relative_working_dir_metadata`, and by `tw activate`/`working-dir set`
   end-to-end; (b) a `working_dir` value containing `..` is still rejected
   even if a component along the way is a symlink; (c) a dangling or
   self-looping `working_dir` symlink still produces the existing
   "must be an existing directory" / error path, not a crash.
6. No change needed to `src/taurworks/resources/shell/taurworks-shell.sh` or
   to `tl` (`src/taurworks/resources/sourceme/aliases.source`) — confirm
   this remains true rather than assuming it.

## Non-Goals

- Re-pointing `project_root` itself, or any change to project registration
  (`taurworks project register`) semantics.
- Any global-config allowlist, trust-gate, or opt-in flag for external
  `working_dir` targets.
- Any warning or validation tied to the symlink's name matching (or not
  matching) its target's basename.
- A `taurworks project working-dir link`-style convenience command to
  create/verify the Workspace↔Tempspace symlink pair — a plausible, separate
  future work item, not part of this one.
- Adding `project/workstreams/` to this repository — a separate,
  independent decision, not a prerequisite or consequence of this fix.

## Acceptance Criteria

See frontmatter `acceptance` list above; restated in prose:

- `paths.working_dir` still rejects absolute paths and `..` components,
  checked against the literal config value.
- `paths.working_dir` is accepted when it is a symlink whose resolved target
  lies outside `project_root`, at all four call sites (`tw activate`/
  `project activate --print`, `working-dir show`, `working-dir set`, `project
  init`/`create --working-dir`).
- Existence/is-directory checks keep following symlinks transparently;
  dangling symlinks, symlink loops, and non-directory targets still error.
- All five existing escape-rejection tests pass unchanged in intent (still
  guarding `..`/absolute); new tests cover the symlink-accepted and
  symlink-failure-mode cases.
- No new config surface, allowlist, or trust-gate is introduced.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- manual dogfood: create a project with `project_root` in one directory and
  a `working_dir` symlink pointing to a directory outside it; confirm `tw
  activate` and `taurworks project activate --print` resolve correctly, and
  that `taurworks project working-dir set` on the same layout succeeds
  instead of hitting the escape error.
- lrh validate
