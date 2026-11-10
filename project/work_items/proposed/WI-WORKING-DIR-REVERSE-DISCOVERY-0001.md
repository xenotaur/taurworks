---
id: WI-WORKING-DIR-REVERSE-DISCOVERY-0001
title: "Discover the project from inside a symlinked working_dir target (reverse lookup)"
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
depends_on:
  - WI-WORKING-DIR-SYMLINK-ESCAPE-0001
blocked_by: []
forbidden_actions:
  - force_push
  - delete_branch
  - consult_logical_pwd_for_discovery
  - export_project_root_from_tw_activate
  - change_tw_activate_cd_target
  - recursive_filesystem_scan_for_projects
  - guess_between_ambiguous_projects
  - change_physical_walk_precedence
acceptance:
  - "When no `.taurworks/` exists in the physical cwd or its physical parents, cwd-based discovery selects the known project (registered, or an immediate child of the workspace root) whose resolved `paths.working_dir` contains the physical cwd; the physical walk still runs first and still wins whenever it finds a project"
  - "`taurworks dev where`, `dev status`, `dev` workflow commands, `project working`, `project activate --print` with no target, `project where`, and `project working-dir show`/`set` with no explicit target all find the project from inside the external work tree, through one shared discovery function rather than per-caller logic"
  - "When the physical cwd lies inside the resolved working_dir of more than one known project, the deepest (longest) resolved working_dir wins; an exact tie is reported as ambiguous with every candidate listed, and discovery stays unresolved instead of guessing"
  - "Diagnostics say how discovery resolved: a `resolved_by`/discovery-source value distinguishes the physical walk from the working_dir reverse lookup (naming the matched project) in `dev where`/`dev status`, `project where`, and `project activate --print`"
  - "`taurworks project working-dir set [DIR]` run from inside the external work tree stores the configured `working_dir` value joined with the cwd's path relative to the resolved working_dir target (e.g. `working_dir/sub`), never resolving through the link; a leading `..` in DIR may only remove components below the link boundary, and a `..` that would cross it is rejected"
  - "A known project whose working_dir is invalid (absolute, `..`, dangling, or looping), missing, or unconfigured is skipped by the reverse lookup without failing discovery; non-symlinked layouts behave exactly as before, and the reverse lookup only runs when the physical walk finds nothing"
  - "`config_model.md`'s \"Working-dir containment and symlinked work trees\" section is updated to describe the reverse lookup and the revised `working-dir set` mapping, replacing the \"run it from project_root instead\" guidance"
artifacts_expected:
  - src/taurworks/manager.py
  - src/taurworks/dev.py
  - src/taurworks/project_resolution.py
  - src/taurworks/project_internals.py
  - tests/manager_test.py
  - tests/dev_test.py
  - tests/cli_test.py
  - tests/shell_helper_test.py
  - project/design/config_model.md
---

# WI-WORKING-DIR-REVERSE-DISCOVERY-0001: Discover the project from inside a symlinked working_dir target (reverse lookup)

## Summary

Make cwd-based project discovery succeed when the physical cwd is inside the
resolved target of a project's `paths.working_dir` symlink. Today every such
command reports `project_root: unresolved`, because discovery only walks the
physical cwd's parents for `.taurworks/`. Add a deterministic fallback that
runs only when that walk finds nothing: a reverse lookup over the
already-known projects (registry plus workspace children), matching the
physical cwd against each project's resolved working_dir. Also map
`working-dir set` through the link so it works from inside the external tree.
This implements the decision recorded in `project/design/config_model.md`
("Discovery from inside a symlinked work tree").

## Problem / Context

`WI-WORKING-DIR-SYMLINK-ESCAPE-0001` (PR #117) made `working_dir` containment
lexical. A real layout now activates: `project_root` (with `.taurworks/`)
stays on a Google-Drive-synced `Workspace` location, and
`project_root/working_dir` is a symlink to an SSD-local `Tempspace` work tree.
`tw activate` `cd`s to the resolved Tempspace path. Discovery uses
`pathlib.Path.cwd().resolve()` and `project_internals.find_project_root_candidate`,
which walks physical parents only. So every cwd-based command run after
activation reports `project_root: unresolved`. That covers `taurworks dev where`,
`dev status`, `dev test` and the rest. Dogfooding confirmed this, even when
the shell's logical `$PWD` is `Workspace/Proj/working_dir`. The same failure
happens when a terminal, IDE, or agent session opens directly in the external
tree, including git worktrees created under it. Day-to-day `dev` use is
AGENTS.md priority 4.

Call sites that discover from the cwd (re-grep before implementing):
- `dev.py` `gather_dev_where_diagnostics` and the dev-command context
  (`dev.py:78-79`, `dev.py:197-198`)
- `project_resolution.gather_project_where_diagnostics` (`:13-14`)
- `project_resolution.py:775` and the `working-dir set` diagnostics
  (`:1172-1173`)
- `project_internals.resolve_project_target`'s no-target `CURRENT_PROJECT`
  branch (`:132-147`), reached by `project activate`, `working-dir show`,
  `project working` and others through `project_resolution.py:127,209,1083,1668`
- `manager.find_current_project` (`:464-475`)

Options considered (see the design section for full reasoning):
- **Working-dir reverse lookup: chosen.** It works however the user got
  into the tree, uses state that already exists, and is deterministic and
  inspectable.
- **Logical `$PWD` walk, validated by the POSIX `pwd -L` rule: deferred.** It
  fails right after `tw activate`, which `cd`s to the physical path, and in
  sessions opened at physical paths. It would add a second mechanism for
  little gain now.
- **`TAURWORKS_PROJECT_ROOT` exported by `tw activate`: rejected.** The value
  goes stale on `cd` and leaks into subshells, which is the "hidden magic in
  repo discovery" AGENTS.md warns against.
- **`tw activate` `cd`s to the logical path: not needed** once the reverse
  lookup exists, and it would be a visible behaviour change.

Prior art check:
- **Duplication search:** none found. Nothing in `src/`, `project/work_items/`,
  `project/design/` or the backlog consults `$PWD`, exports a project marker,
  or reverse-maps a cwd to a working_dir. `manager.gather_global_projects`
  and `classify_project_entry` already enumerate the known projects and
  compute each `resolved_working_dir`. The lookup should reuse them rather
  than duplicate them.
- **Demand search:** the only demand is this follow-up, recorded in the
  PR #117 execution records' Follow-up sections and in
  `config_model.md`'s current "run `working-dir set working_dir` from
  `project_root` instead" note.

## Scope

- A single shared cwd-discovery function returning the project root, a
  stable `resolved_by` value, and any ambiguity candidates. It applies the
  physical walk first and the working_dir reverse lookup second.
- All cwd-based discovery call sites listed above use it.
- `resolved_by` / discovery-source diagnostics in `dev where`/`dev status`,
  `project where` and `project activate --print`.
- The `working-dir set` mapping through the link when discovery resolved by
  reverse lookup.
- Tests, and the `config_model.md` update.

## Required Changes

1. **Shared function.** Add a cwd-discovery function, for example
   `find_project_root_for_cwd(cwd) -> CwdDiscovery(root, resolved_by,
   candidates)`, at a layer that can see the registry and workspace without
   an import cycle. `manager.py` works, or a new `project_discovery.py`.
   `project_internals` must not import `manager`.
   - Step 1: `find_project_root_candidate(cwd.resolve())`, unchanged. If it
     finds a root, return it with `resolved_by` set to the physical walk.
   - Step 2: only if step 1 found nothing, iterate
     `manager.gather_global_projects()`. Consider only rows with a configured,
     existing, valid `resolved_working_dir`, and select those whose resolved
     working_dir equals or is an ancestor of the physical cwd. Compare
     resolved paths component-wise, not by string prefix.
   - Choose the deepest match. On an exact tie (the same resolved
     working_dir), return no root, `resolved_by` set to ambiguous, and the
     candidate list.
   - Rows whose working_dir metadata is invalid are skipped silently.
     `classify_project_entry` already catches `ProjectConfigError`.
2. **Callers.** Route every cwd-based call site in Problem / Context through
   the shared function. For `resolve_project_target`'s no-target branch,
   pass in the discovered root, or add a hook, so `project_internals` stays
   free of a registry dependency. Add a new `ResolutionReason` value (for
   example `WORKING_DIR_REVERSE_LOOKUP`). Explicit targets (a path, name, or
   `--project`) keep their current precedence, unchanged.
3. **Diagnostics.**
   - `dev where`/`dev status` gain a `resolved_by` (or `discovery_source`)
     field.
   - `project where` reports the reverse lookup as a discovery source and
     names the matched project.
   - `project activate --print` keeps reporting `resolved_by`.
   - An ambiguous result lists the candidate project roots and says to pass
     an explicit target.
4. **`working-dir set` mapping.** In `relative_working_dir`, or a wrapper
   used by the `set` diagnostics: when the physical cwd is not under the
   resolved `project_root` but is inside the project's resolved configured
   working_dir target, compute the stored value lexically. The prefix is the
   configured working_dir value plus the cwd's path relative to the resolved
   target. Apply `DIR` to that prefix with the same rules as PR #117.
   - A leading `..` may only remove components of the tail below the
     resolved target. A `..` that would remove the configured working_dir
     component itself is rejected with an escape-style error.
   - A `..` after any ordinary component is still rejected.
   - The usual lexical, symlink, and existence checks then run on the
     result.
5. **Unchanged.** Keep the physical-walk precedence, `tw activate`'s `cd`
   target, and the shell helper. Add no environment variable and no `$PWD`
   handling. Don't recursively scan the filesystem; only registered projects
   and immediate workspace children are considered, as `project list` does.
6. **Tests.**
   - (a) `dev where` from inside the external target, and from a nested
     subdirectory of it, finds the project with `resolved_by` set to the
     reverse lookup.
   - (b) `project activate --print` with no target, run from the external
     target, resolves the project.
   - (c) `working-dir set` from inside the external target stores
     `working_dir` (no argument) and `working_dir/sub` (from `sub`); a
     leading `..` that would cross the link is rejected.
   - (d) Two projects whose working_dirs point at nested targets resolve to
     the deeper one; two projects sharing one target are reported as
     ambiguous and stay unresolved.
   - (e) A physical `.taurworks/` above the cwd still wins over a
     reverse-lookup match.
   - (f) A project with a dangling or looping working_dir symlink is
     skipped, not fatal.
   - (g) A registered project outside the workspace is found, and an
     unconfigured workspace still works with registry-only lookup.
   - (h) An end-to-end `tw activate` followed by `taurworks dev where` finds
     the project.
7. **Docs.** Update `config_model.md`'s "Working-dir containment and
   symlinked work trees" section, replacing the "run it from project_root
   instead" note. Flip the status line of the new "Discovery from inside a
   symlinked work tree" section to implemented.

## Non-Goals

- A logical `$PWD`-based discovery walk (deferred; a possible later work item
  if non-working_dir symlinks inside projects need it).
- Exporting a project marker from `tw activate`, or changing where it `cd`s.
- Recursive or deep filesystem scanning for projects.
- Discovering an external tree for a project that is neither registered nor
  an immediate child of the configured workspace (register it instead).
- Any change to `working_dir` containment rules from PR #117 beyond the
  `working-dir set` mapping above.

## Acceptance Criteria

See frontmatter `acceptance`. In prose:
- From inside a symlinked working_dir target, cwd-based commands find the
  project through one shared function that runs the physical walk first and
  the reverse lookup second.
- Ambiguity is reported, never guessed.
- Diagnostics show how discovery resolved.
- `working-dir set` works from inside the external tree without crossing the
  link boundary with `..`.
- Non-symlinked layouts are unchanged.
- `config_model.md` describes the result.

## Validation

- ./scripts/format --check --diff
- ./scripts/lint
- ./scripts/test
- lrh validate
- manual dogfood: register (or place under the workspace) a project whose `working_dir` is a symlink to an external directory; `tw activate` it, then run `taurworks dev where`, `taurworks project where` and `taurworks project activate --print` from the external directory and a subdirectory, and confirm each finds the project and reports the reverse lookup; run `taurworks project working-dir set` there and confirm the stored value

## Risk Notes

- **Cost.** The lookup reads one config file per known project. It only
  runs when the physical walk fails, so non-symlinked layouts pay nothing.
- **Trust.** A synced project config can't steer the lookup on its own: it
  names only a relative path, and the symlink that makes a target external
  is a machine-local filesystem detail. The lookup only selects which
  already-known project the cwd belongs to. It never executes anything.
