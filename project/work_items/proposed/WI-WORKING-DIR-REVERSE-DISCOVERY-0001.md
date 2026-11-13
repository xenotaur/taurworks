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
  - "From inside the external work tree, these find the project through one shared discovery function rather than per-caller logic: `taurworks dev where`, `dev status` and the `dev` workflow commands; `project where`; `project working-dir show`/`set` with no target; the commands that resolve through `resolve_global_activation_project` with no target (`project activate --print`, `project env show`/`set`, `project trust set`/`unset`, `legacy inspect`); `project working-dir show NAME` (its current-project name check); and explicit existing-directory targets on the `prefer_project_root=True` branch, which is shared by the path emitters `taurworks project working .`, `project root .`, top-level `taurworks working .`/`taurworks root .`, and by `project working-dir show .`. `project create`'s nested-name guard (`_current_project_name`) keeps the physical walk only. Explicit path-like targets to `project activate` and the other `resolve_global_activation_project` commands (`prefer_project_root=False`) keep their current behaviour"
  - "When the physical cwd lies inside the resolved working_dir of more than one known project, the deepest (longest) resolved working_dir wins; an exact tie is reported as ambiguous with every candidate listed and command-specific recovery guidance (pass the project name or path to commands that resolve names through the registry; pass the path to the chosen project_root to `working-dir show`; otherwise rerun from the chosen project_root, with a project-root-relative DIR for `working-dir set`). The affected command then fails instead of guessing: an ambiguous lookup never falls back to the cwd or the target path itself (for example, the path emitters never print the external directory)"
  - "Diagnostics say how discovery resolved: a `resolved_by`/discovery-source value distinguishes the physical walk from the working_dir reverse lookup (naming the matched project) in `dev where`/`dev status`, `project where`, and `project activate --print`; an ambiguous lookup reaches every caller with its candidate list intact, on both the `find_current_project`/`resolve_global_activation_project` path and the `resolve_project_target` path (not collapsed to `None` or to a fallback resolution)"
  - "`taurworks project working-dir set [DIR]` run from inside the external work tree stores the configured `working_dir` value joined with the cwd's path relative to the resolved working_dir target (e.g. `working_dir/sub`), never resolving through the link; the boundary is the last symlink component of the lexical `project_root`/`working_dir` path (e.g. `working_dir` when the configured value is `working_dir/sub` and only `working_dir` is a link): a leading `..` in DIR may only remove components after that symlink component, and a `..` that would remove the symlink component itself is rejected"
  - "A known project whose working_dir is invalid (absolute, `..`, dangling, or looping), missing, or unconfigured is skipped by the reverse lookup without failing discovery; non-symlinked layouts behave exactly as before, except that `dev` commands run from inside a linked `git worktree` checkout nested within the resolved working_dir use that worktree as their work directory, whether or not the working_dir is a symlink (submodules and independent nested clones keep their current behaviour); and the reverse lookup only runs when the physical walk finds nothing"
  - "The linked-worktree test reads the nested checkout's `.git` file (a `gitdir:` path ending in `worktrees/<name>` whose directory contains a `commondir` file) without running `git`; a `.git` directory, a submodule `gitdir` (`modules/<name>`, even when the submodule's own name contains a `worktrees/` component), or an unreadable or malformed `.git` file is not a worktree"
  - "`config_model.md`'s \"Working-dir containment and symlinked work trees\" section is updated to describe the reverse lookup and the revised `working-dir set` mapping, replacing the \"run it from project_root instead\" guidance"
artifacts_expected:
  - src/taurworks/manager.py
  - src/taurworks/dev.py
  - src/taurworks/project_resolution.py
  - src/taurworks/project_internals.py
  - tests/manager_test.py
  - tests/project_resolution_test.py
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
- The `working-dir set` diagnostics (`project_resolution.py:1172-1173`)
- `project_internals.resolve_project_target`'s no-target `CURRENT_PROJECT`
  branch (`:132-147`). Only `project working-dir show` reaches it with no
  target (`project_resolution.py:1081-1085`). The other callers (`:127`
  for `init`, `:209`, `:1668`) never pass `None`. `:127` can also receive
  a bare name, for example `project init foo`.
- `resolve_project_target`'s current-project name check (`:134`,
  `:149-156`). It matches a bare-name target against the project found by
  the physical walk only. So today `project working-dir show NAME` from
  the external tree falls through to `CHILD_PATH` (`<cwd>/NAME`), while
  `project working NAME` and `activate --print NAME` resolve through the
  registry.
- `resolve_project_target`'s explicit existing-path branch with
  `prefer_project_root=True` (`:165-181`), which walks only the physical
  parents of the target. Two callers reach it:
  - The path emitters (`_resolve_project_path_emitter_target`,
    `project_resolution.py:1662-1672`). These are `project working`,
    `project root`, and top-level `taurworks working`/`taurworks root`
    (`cli.py:109-114`, `cli.py:1207-1210`). They take a required PROJECT
    argument (`cli.py:614-618`), so `project working .` lands here.
  - `working-dir show` with an explicit path (`:1081-1085`).
  Today `project working .` from inside the external tree doesn't report
  "unresolved": it exits 0 and prints the external directory itself, which
  is wrong.
- `manager.find_current_project` (`:464-475`). It is reached through
  `project_resolution.resolve_global_activation_project` (`:187`), the
  no-target and current-name path for `project activate --print`,
  `project env show`/`set` (`:1262`, `:1360`), `project trust set`/`unset`
  (`:1439`, `:1514`) and `legacy inspect` (`legacy.py:174-176`). It returns
  `dict | None` today, so it can't carry ambiguity candidates.
- Not affected: `project_resolution._current_project_name` (`:773-790`),
  the nested same-name guard for `project create`. It keeps the physical
  walk only, so `project create` behaviour doesn't change.
- Not affected: path-like targets to `resolve_global_activation_project`
  (`:208-212`) use `prefer_project_root=False`. Today `project activate .`
  from a physical project subdirectory resolves to the subdirectory itself
  (`existing_path`). This work item leaves that branch unchanged.

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

- A single shared discovery function, starting from the cwd or from an
  explicit existing-directory target. It returns the project root, a stable
  `resolved_by` value, and any ambiguity candidates, applying the physical
  walk first and the working_dir reverse lookup second.
- All cwd-based call sites listed above use it, and so does the explicit
  existing-path branch.
- `resolved_by` / discovery-source diagnostics in `dev where`/`dev status`,
  `project where` and `project activate --print`.
- The `working-dir set` mapping through the link when discovery resolved by
  reverse lookup.
- Tests, and the `config_model.md` update.

## Required Changes

1. **Shared function.** Add a discovery function that takes a starting
   directory, for example `find_project_root_for_path(start) ->
   PathDiscovery(root, resolved_by, candidates)`. Callers pass the cwd, or
   the resolved explicit target. Put it at a layer that can see the
   registry and workspace without an import cycle: `manager.py` works, or
   a new `project_discovery.py`. `project_internals` must not import
   `manager`.
   - Step 1: `find_project_root_candidate(start.resolve())`, unchanged. If
     it finds a root, return it with `resolved_by` set to the physical walk.
   - Step 2: only if step 1 found nothing, iterate
     `manager.gather_global_projects()`. Consider only rows with a configured,
     existing, valid `resolved_working_dir`, and select those whose resolved
     working_dir equals or is an ancestor of the resolved start. Compare
     resolved paths component-wise, not by string prefix.
   - Choose the deepest match. On an exact tie (the same resolved
     working_dir), return no root, `resolved_by` set to ambiguous, and the
     candidate list.
   - Rows whose working_dir metadata is invalid are skipped silently.
     `classify_project_entry` already catches `ProjectConfigError`.
   - Ambiguity needs a carrier on the `resolve_project_target` path too. Add
     a `candidates` field to `project_internals.ProjectResolution`
     (defaulting to an empty tuple, so existing constructors are
     unaffected), plus an ambiguous `ResolutionReason` value (for example
     `WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS`).
2. **Callers.** Route every cwd-based call site in Problem / Context through
   the shared function. For `resolve_project_target`'s no-target branch,
   pass in the discovered root, or add a hook, so `project_internals` stays
   free of a registry dependency. Add a new `ResolutionReason` value (for
   example `WORKING_DIR_REVERSE_LOOKUP`).
   - The explicit existing-path branch with `prefer_project_root=True`
     changes too. When the existing target has no physical `.taurworks/`
     ancestor, apply the reverse lookup to the resolved target before
     falling back to today's `EXISTING_PATH` result. This makes the path
     emitters (`project working .`, `project root .`, `taurworks working
     .`, `taurworks root .`) and `project working-dir show .` work from
     inside the external tree.
   - When the lookup is ambiguous, `resolve_project_target` returns the
     ambiguous reason and candidates; it does **not** fall back to
     `EXISTING_PATH` or `DEFAULT_CURRENT_DIRECTORY`. Its callers (the path
     emitters and `working-dir show`) then fail (`ok=False`, non-zero exit,
     nothing printed to stdout by the path emitters), reporting the
     candidates and the guidance from Required Change 3.
   - The hook that supplies the discovered root to `resolve_project_target`
     also feeds its current-project name check (`:134`, `:149-156`). That
     makes `project working-dir show NAME` work from the external tree.
   - The `prefer_project_root=False` branch is unchanged. That includes
     path-like targets to `resolve_global_activation_project` (for example
     `project activate .`), so explicit-path precedence stays as it is.
   - `manager.find_current_project` (or a replacement that
     `resolve_global_activation_project` calls at `:187`) must return the
     discovery result with its `resolved_by` and ambiguity candidates, not
     only `dict | None`. That way activate, env, trust and legacy-inspect can
     report ambiguity as Required Change 3 requires. Update its other
     callers to match.
   - Name targets, registry and workspace resolution, and `--project` keep
     their current precedence, unchanged.
3. **Diagnostics.**
   - `dev where`/`dev status` gain a `resolved_by` (or `discovery_source`)
     field.
   - `project where` reports the reverse lookup as a discovery source and
     names the matched project.
   - `project activate --print` keeps reporting `resolved_by`.
   - An ambiguous result lists the candidate project roots, with guidance
     that depends on what the command can actually accept:
     - Commands that resolve a project name through the registry and
       workspace say to pass the project name or the path to its
       `project_root`: `project activate`, `project env show`/`set`,
       `project trust set`/`unset`, `legacy inspect`, `project working`,
       `project root`, and `taurworks working`/`taurworks root`.
     - `project working-dir show` resolves bare names relative to the cwd,
       not through the registry, so it says to pass the path to the chosen
       `project_root`.
     - Commands that take no project target (`dev ...`, `project where`,
       and `working-dir set`, whose argument is DIR) say to rerun from the
       chosen `project_root`, with a project-root-relative DIR for `set`.
4. **`working-dir set` mapping.** In `relative_working_dir`, or a wrapper
   used by the `set` diagnostics: when the physical cwd is not under the
   resolved `project_root` but is inside the project's resolved configured
   working_dir target, compute the stored value lexically. The prefix is the
   configured working_dir value plus the cwd's path relative to the resolved
   target. Apply `DIR` to that prefix with the same rules as PR #117.
   - The boundary is the last symlink component of the lexical
     `project_root`/prefix path. With configured `working_dir/sub`, where
     only `working_dir` is a link, the boundary is `working_dir`.
   - Every component after the boundary is symlink-free: the configured
     components below the link, plus the tail from the resolved cwd. So a
     lexical step up equals a physical one there.
   - A leading `..` may remove any of those components. A `..` that would
     remove the symlink component itself, or anything before it, is
     rejected with an escape-style error.
   - So from `<external>/sub` with configured `working_dir/sub`, `set ..`
     stores `working_dir`, and `set ../..` is rejected.
   - A `..` after any ordinary component is still rejected.
   - The usual lexical, symlink, and existence checks then run on the
     result.
5. **`dev` work directory inside a linked worktree** (amended during PR
   #119 review, with the user's approval). In `dev`'s work-directory guess:
   when the nearest git root (the checkout containing the cwd) is strictly
   inside the resolved working_dir *and* is a linked `git worktree`
   checkout, use it as the work directory.
   This applies whether the project was found by the physical walk or the
   reverse lookup. A checkout counts as a linked worktree when its `.git`
   is a file whose `gitdir:` path ends in `worktrees/<name>` and that
   directory contains a `commondir` file, which git always writes for linked
   worktrees and never for a submodule's git dir. Read the files directly,
   without running `git`. A `.git` directory (an independent
   clone), a submodule (`gitdir` ending in `modules/<name>`), and an
   unreadable or malformed `.git` file keep today's behaviour, where the
   configured working_dir wins. Tier 1 `[dev.commands]` still come from
   `project_root`; they run with the worktree as cwd.
6. **Unchanged.** Keep the physical-walk precedence, `tw activate`'s `cd`
   target, and the shell helper. Add no environment variable and no `$PWD`
   handling. Don't recursively scan the filesystem; only registered projects
   and immediate workspace children are considered, as `project list` does.
7. **Tests.**
   - (a) `dev where` from inside the external target, and from a nested
     subdirectory of it, finds the project with `resolved_by` set to the
     reverse lookup.
   - (b) `project activate --print` with no target, run from the external
     target, resolves the project.
   - (c) `working-dir set` from inside the external target:
     - With configured `working_dir`, no argument stores `working_dir`, and
       running it from `sub` stores `working_dir/sub`.
     - A leading `..` that would cross the link is rejected.
     - With configured `working_dir/sub` (only `working_dir` a link), `set ..`
       from `<external>/sub` stores `working_dir`, and `set ../..` is
       rejected.
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
   - (i) `taurworks project working .`, `project root .`, top-level
     `taurworks working .` and `project working-dir show .`, run from a
     subdirectory of the external target, resolve the project
     through the reverse lookup. Running from the target's root can't tell
     before from after, because the working_dir resolves to that same path.
     This is a regression test for the explicit-path branch. Also check
     that `project activate .` from a physical project subdirectory still
     resolves to that subdirectory (`existing_path`), unchanged.
   - (j) An ambiguous result from `dev where`, `project where` and
     `working-dir set` gives the "rerun from project_root" guidance, not
     "pass a target".
   - (k) An ambiguous no-target lookup through
     `resolve_global_activation_project` (`project activate --print`, and
     one of env, trust or legacy inspect) lists the candidates and says to
     pass the project name or path.
   - (l) An ambiguous lookup on the `resolve_project_target` path fails:
     `project working .` exits non-zero with nothing on stdout, never
     printing the external directory, and `project working-dir show` with
     no target fails. Each lists the candidates; `working-dir show`
     recommends passing the path to `project_root`.
   - (m) `project working-dir show NAME`, run from inside the external
     target, resolves the named current project (not `CHILD_PATH`), and
     `project create NAME`'s nested-name guard behaves as before.
   - (n) `dev test`/`dev where` from a linked worktree nested in the
     working_dir use the worktree, both inside a symlinked external target
     and inside a plain (physically discovered) project; from the main
     checkout the working_dir is still used.
   - (o) Parity with master for a plain project: `dev test` from inside a
     submodule (`.git` file pointing at `modules/<name>`) and from inside an
     independent nested clone (`.git` directory) still uses the working_dir.
   - (p) A malformed `.git` file inside the working_dir is not treated as a
     worktree, and neither is a submodule whose name puts `worktrees` next to
     last in its `gitdir` (`modules/worktrees/<name>`).
8. **Docs.** Update `config_model.md`'s "Working-dir containment and
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

## Implementer notes from review

These are non-blocking points from the final substitute review of PR #118
(`3b56d8f`). They were recorded at closeout so they get settled during
implementation rather than lost:

- **Ambiguity on the `dev` path.**
  - `gather_dev_where_diagnostics` falls back to the git root or cwd when
    no project root is found (`dev.py:88-99`). `resolve_dev_command` can
    then run `<guess>/scripts/<name>`, skipping both projects'
    `[dev.commands]` overrides.
  - Decide and document whether `dev where`/`dev status` (exit 0 today)
    exit non-zero on an ambiguous lookup.
  - Make `dev test` and the other workflow commands refuse to run a script
    fallback when discovery is ambiguous, as Acceptance Criterion 3's
    "never falls back to the cwd" requires.
  - Extend test (j) with a `dev test` ambiguity case.
- **Ambiguous cwd plus an explicit, non-matching target.** Both resolvers
  run cwd discovery before the name and path branches.
  - An ambiguous cwd must fall through, not fail early, when an explicit
    target doesn't match the current-project name. Examples:
    `working-dir show NAME`, `project activate .`,
    `project working /other/proj`.
  - This preserves Acceptance Criterion 2's "explicit path-like targets
    keep their current behaviour".
- **The ambiguous `ProjectResolution`.** Specify what `project_root` holds
  in an ambiguous result (for example the cwd as a placeholder, never used
  as a target). Make callers check the ambiguous `resolved_by` before
  using it. `gather_project_path_diagnostics` currently sets `ok=True`
  whenever `source == "path"`.
- **Inventory additions.** `legacy migrate` (which writes config with
  `--apply`) and `project activate --shell` (the path `tw activate` uses)
  both go through `resolve_global_activation_project`. They inherit the
  change, and belong in the command lists and the ambiguity guidance
  (registry-name group).
- **Wording.**
  - Today, no-target `project activate --print` from the external tree
    prints the cwd with `resolved_by: child_path` and exits 1. The design
    section's "reports `project_root: unresolved`" summary is loose.
  - Test (i)'s "can't tell before from after" applies to `working`, not
    `root`.
  - Update `project where`'s stale limitation text ("No workspace registry
    resolution is implemented yet").
  - The explicit-path branch also handles existing *files*, through their
    parent directory.

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
