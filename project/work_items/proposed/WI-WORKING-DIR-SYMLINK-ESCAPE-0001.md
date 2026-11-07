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
  - "`paths.working_dir` rejects absolute paths and any path containing a `..` component, evaluated against the literal, unresolved config value — a deliberate tightening: in-root values such as `repo/../repo`, accepted today because the helpers resolve before checking containment, are now rejected, with an error that tells the user to rewrite the value in plain relative form"
  - "`paths.working_dir` is accepted when it names a path that is lexically a (possibly nested) child of `project_root`, even when that path is a symlink whose fully resolved target lies outside `project_root`"
  - "existence/is-directory checks continue to follow symlinks transparently, and each caller's existing ordinary-missing-directory policy is unchanged (see the Scope inventory): `working-dir set` still requires an existing directory; `project create --working-dir` still records a missing path while `project init --working-dir` still rejects it unless `--create-working-dir` is supplied (which still creates it for either command); `project activate --print` and `dev where`/`status` still report it without failing (`tw activate` still refuses to `cd`); `taurworks project working`/`taurworks working` still fail; project classification still marks it not activation-eligible; legacy migration still sends it to manual review"
  - "a dangling or looping symlink anywhere in the lexical `project_root`/`working_dir` path makes both helpers raise `ProjectConfigError` (the same error they raise for an absolute or escaping value), distinguished from an ordinary missing path; each caller keeps its existing handling of that error unchanged (no per-caller changes, so e.g. `dev where`/`status` still degrades gracefully); and `--create-working-dir` never creates a directory through such a symlink while still creating an ordinary missing directory"
  - "every caller of the two helpers in the Scope inventory gets the fix through the shared helpers, with no per-caller containment logic: `project working-dir set`, `project init`/`project create --working-dir`, `project activate --print`/`tw activate`, `taurworks project working`/`taurworks working`, `dev where`/`dev status`, project classification (`manager.classify_project_entry`), and legacy migration of relative `cd` targets; legacy migration's separate resolved-path normalization of absolute `cd` targets (`legacy._normalize_cd_target`) is unchanged; `project working-dir show`, which performs no validation, is unaffected"
  - "the five existing tests that assert escape-rejection (`tests/project_internals_test.py::test_relative_working_dir_rejects_paths_outside_project_root`, and the four `\"may not escape\"` assertions in `tests/cli_test.py`) still pass for `..`/absolute inputs"
  - "new tests cover: a working_dir that is a symlink to a directory outside project_root (accepted); an in-root `..` value such as `repo/../repo` (now rejected); a working_dir containing `..` that also traverses a symlink (rejected); a dangling or looping working_dir symlink (error, not `working_dir_exists: False`); `project init ROOT --working-dir link --create-working-dir` with a dangling `link` (rejected, external target not created); and an ordinary missing working_dir (still reported missing by metadata paths and still created by `--create-working-dir`)"
  - "the cwd-relative `working-dir set DIR` mapping question (see Open Questions) is decided and documented in `config_model.md` before or with the implementation"
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
symlink whose real target lies outside `project_root`, while rejecting any
config value that is absolute or contains a `..` component (a tightening for
in-root `..` values, which are accepted today), and rejecting dangling or
looping symlinks explicitly instead of treating them as missing paths. This
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
  containment (reject absolute/`..` in the literal value; otherwise accept),
  and add an explicit dangling/looping-symlink check, enforced before any
  `--create-working-dir` `mkdir`.
- Verify the fix propagates correctly to every caller of those two
  functions, without needing its own separate fix. Call-site inventory
  (as of this WI's drafting; re-grep before implementing):
  - `relative_working_dir` → `set_working_dir` (`project_internals.py:517-536`)
    → `taurworks project working-dir set` (`project_resolution.py:1189`).
    Requires an existing directory.
  - `relative_working_dir_metadata`, directly → `gather_project_init_diagnostics`
    / `gather_project_create_diagnostics` pre-validation
    (`project_resolution.py:365-380, 889-902`), and via
    `set_working_dir_metadata` (`project_internals.py:599-635`) /
    `create_working_dir_metadata_target` (`project_internals.py:580-596`)
    → `taurworks project init`/`project create --working-dir
    [--create-working-dir]`. For an ordinary missing path, `project create`
    records it, while `project init` rejects it ("must be an existing
    directory unless --create-working-dir is supplied",
    `project_resolution.py:386-392`); the creation flag creates it for
    either command.
  - `relative_working_dir_metadata`, directly → legacy migration
    (`legacy.py:408`, `_merge_legacy_matches_into_config`). A missing target
    goes to manual review. An *absolute* legacy `cd` target is first
    normalized by `legacy._normalize_cd_target` (`legacy.py:266-280`), which
    has its own resolved-path containment check; this WI leaves it
    unchanged, so an absolute target reached through the symlink still goes
    to manual review. Only relative targets get the lexical rule.
  - `relative_working_dir_metadata` via `resolve_configured_working_dir`
    (`project_internals.py:568-577`) →
    - `taurworks project activate --print` (`project_resolution.py:1982`):
      reports `working_dir_exists: False` successfully for an ordinary
      missing path; `tw activate`, which runs the same diagnostics via `activate --shell`, then fails at
      the shell layer (`taurworks-shell.sh:334-337`);
    - `taurworks project working` / `taurworks working`
      (`gather_project_path_diagnostics`, `project_resolution.py:1752`):
      fails (`ok=False`) for an ordinary missing path;
    - `taurworks dev where` / `dev status` / dev-command resolution
      (`dev.py:42`): reports existence without failing;
    - project classification for listing and activation eligibility
      (`manager.py:298`, `classify_project_entry`): a missing path marks
      the project "not eligible for `tw activate`".
  - Not a caller: `taurworks project working-dir show`
    (`gather_project_working_dir_show_diagnostics`,
    `project_resolution.py:1078-1146`) echoes the raw config string and
    performs no working_dir validation; it is unaffected by this WI.

  Every caller above already catches `ProjectConfigError` from these
  helpers (it is how an absolute or escaping value is rejected today). The
  invalid-symlink rule (Required Change 3) raises that same error, so each
  caller handles an invalid symlink exactly as it handles an escaping value
  now; no caller's error handling changes.
- Update the five existing tests that assert today's escape-rejection
  behavior so they keep asserting it for `..`/absolute inputs specifically
  (not for symlinks), and add new tests for the symlink-permitted case and
  for symlink-loop/dangling-symlink failure modes.
- No shell-helper (`taurworks-shell.sh`) changes are expected; this is a
  pure `project_internals.py` validation change.

## Required Changes

1. In `relative_working_dir` (`project_internals.py:483-514`): stop calling
   `.resolve()` on the joined `cwd`/`raw_path` target before the containment
   check. Reject `raw_path.is_absolute()` as today, and add a new rejection
   of any `".."` in the *derived stored value*'s parts (today's code has no
   such literal check — it only rejects a resolved target outside the root,
   so in-root `..` is currently accepted; this is the deliberate tightening).
   How the cwd-relative `DIR` is mapped to that stored value is the open
   question below; whatever is chosen must not resolve through a symlink
   component of the configured path. Use `.is_dir()` (which already follows
   symlinks) for the existence check; use `.resolve()` only when producing a
   path for display (e.g. the final `cd` target string), never for the
   containment gate.
2. Apply the equivalent change to `relative_working_dir_metadata`
   (`project_internals.py:539-565`), used by the no-cwd-context metadata
   paths (`project init`/`create --working-dir`, legacy migration, and every
   `resolve_configured_working_dir` caller — see the Scope inventory): reject
   absolute values and any `..` component in the literal value, then check
   containment lexically. Keep returning `(relative_path, is_dir)` for an
   ordinary missing path so metadata-only callers keep reporting
   `working_dir_exists: False`.
3. Add an explicit invalid-symlink check shared by both helpers: walk each
   prefix of the lexical `project_root`/`working_dir` path and raise
   `ProjectConfigError` when a component `is_symlink()` but does not resolve
   to an existing target (dangling) or loops. Do not rely on incidental
   `OSError` behavior for this: on Python 3.11, `Path.is_dir()` returns
   `False` (it does not raise) for both a dangling link and a loop, which
   would otherwise be indistinguishable from an ordinary missing directory,
   and non-strict `Path.resolve()` raises `RuntimeError` (not `OSError`) on a
   loop — which the callers' existing `except (ProjectConfigError, OSError,
   tomllib.TOMLDecodeError)` handling (`project_resolution.py:1753-1761,
   1983-1987`) would not catch.
4. In `create_working_dir_metadata_target` (`project_internals.py:580-596`):
   the step 3 check must run before `mkdir(parents=True, exist_ok=True)`, so
   `project init ROOT --working-dir link --create-working-dir` with a
   dangling `link` is rejected instead of creating the link's external
   target. Ordinary missing-directory creation (no symlink component) is
   unchanged.
5. Do not add any new config field, CLI flag, global allowlist, or
   trust-gate. Do not add a name-matching warning (see Problem/Context for
   why both were rejected as part of this change's design decision).
6. Update `tests/project_internals_test.py:156-161`
   (`test_relative_working_dir_rejects_paths_outside_project_root`) and the
   four `"may not escape"` assertions in `tests/cli_test.py` (around lines
   1427-1449, 1742, 2219-2250, 2544) to confirm they still exercise `..`
   specifically. Add new tests: (a) a `working_dir` that is a symlink to an
   external directory is accepted by both `relative_working_dir` and
   `relative_working_dir_metadata`, and by `tw activate`/`working-dir set`
   end-to-end; (b) an in-root `..` value such as `repo/../repo` is now
   rejected; (c) a `working_dir` value containing `..` is rejected even if a
   component along the way is a symlink; (d) a dangling or self-looping
   `working_dir` symlink makes both helpers raise `ProjectConfigError` (not
   `RuntimeError`, and not a `working_dir_exists: False` result), and,
   end-to-end, `project activate --print` fails with its invalid-working_dir
   guidance rather than reporting the directory as missing; (e) `--create-working-dir`
   with a dangling symlink is rejected and the external target is not
   created; (f) an ordinary missing `working_dir` is still reported as
   missing by metadata paths and still created by `--create-working-dir`.
7. No change needed to `src/taurworks/resources/shell/taurworks-shell.sh` or
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

- `paths.working_dir` rejects absolute paths and every `..` component,
  checked against the literal config value — including in-root `..` values
  that are accepted today (a documented tightening).
- `paths.working_dir` is accepted when it is a symlink whose resolved target
  lies outside `project_root`, at every caller of the two helpers (Scope
  inventory); `working-dir show` performs no validation and is unaffected.
- Existence/is-directory checks keep following symlinks transparently, and
  each caller's ordinary missing-directory policy is unchanged; a dangling
  or looping symlink component makes both helpers raise `ProjectConfigError`,
  which each caller handles as it already handles an escaping value, and
  `--create-working-dir` never creates through one.
- All five existing escape-rejection tests still pass (still guarding
  `..`/absolute); new tests cover the in-root `..` tightening, the
  symlink-accepted case, the invalid-symlink failure modes (including with
  `--create-working-dir`), and preserved ordinary-missing-directory behavior.
- No new config surface, allowlist, or trust-gate is introduced.

## Open Questions

- **cwd-relative `working-dir set DIR`.** `DIR` is interpreted relative to
  the current directory, not `project_root`, and today it is resolved
  (`(cwd / DIR).resolve()`). Under lexical containment the implementation
  must decide how `DIR` becomes the stored, `..`-free `paths.working_dir`
  value without resolving through a symlink component — e.g. whether a
  leading `..` in `DIR` is applied to the physical (resolved) cwd, and how
  `working-dir set` with no argument behaves when the user's cwd is inside
  the symlinked external work tree (its physical path is then outside
  `project_root`; the logical `$PWD` may still be inside it). Decide this
  and record it in `config_model.md` as part of implementing this item.

## Implementer notes from review

Non-blocking points raised by the PR #115 review and substitute review,
recorded here so they are settled during implementation rather than lost:

- **Error text vs existing tests.** The new `..` error should tell the user
  to rewrite the value in plain relative form, while the four
  `tests/cli_test.py` assertions match the substring `"may not escape"`.
  Either keep that substring in the new message or update those assertions
  deliberately; "still pass" (acceptance) and "Update" (Required Change 6)
  both refer to this choice.
- **Messages that become misleading.** `dev.py:61` ("configured working_dir
  resolved safely inside the project root") and the `--create-working-dir`
  help text (`cli.py:757`, "stays inside the project root") will be wrong
  once a symlinked `working_dir` resolves outside the root. Reword them;
  this adds `src/taurworks/dev.py` and `src/taurworks/cli.py` to the
  touched files.
- **Python versions.** Required Change 3's reasoning is Python-3.11
  behavior; nothing pins `requires-python`, and on 3.13+ non-strict
  `resolve()` returns instead of raising `RuntimeError` on a loop. The
  explicit symlink check must not depend on either behavior.
- **Same error *type*.** "The same `ProjectConfigError`" means the same
  exception type, not the same message; give dangling/looping symlinks
  their own message rather than reusing the "may not escape" text.
- **Valid link, missing tail.** With a valid external symlink component
  followed by a missing tail (`link/missing`), `--create-working-dir`
  creates the directory inside the external target. The design implies
  this is allowed; confirm and document it, and test it under (f).

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
