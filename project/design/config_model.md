# Configuration and State Model

## Precedence order
For developer workflow behavior (for example `taurworks dev ...` command resolution), configuration should resolve in this order (highest to lowest):

1. Command-line options
2. Repo-local workflow configuration (`taurdev.toml`)
3. Optional Python integration (`[tool.taurdev]` in `pyproject.toml`)
4. Visible project/workspace metadata (`.taurworks/`)
5. XDG-style global user configuration/state/cache
6. Built-in defaults

This precedence keeps repository-defined dev behavior authoritative while still allowing user defaults when repository config is absent.

## Global model (user scope)
Use XDG-style directories for user-level settings and registries, including workspace/project registration and user defaults.


## Global config and workspace root (Phase 1a)

Implementation status: implemented minimal foundation. Taurworks now supports XDG-style global config path diagnostics plus explicit workspace root show/set commands.

Taurworks should introduce a user-global configuration file using XDG-style conventions:

```text
$XDG_CONFIG_HOME/taurworks/config.toml
```

When `XDG_CONFIG_HOME` is unset, Taurworks should fall back to:

```text
~/.config/taurworks/config.toml
```

The minimal global config should be explicit and stable:

```toml
schema_version = 1

[workspace]
root = "/Users/example/Workspace"
```

Implemented commands:

```bash
taurworks config where
taurworks workspace show
taurworks workspace set PATH
```

Discovery stance:

- `taurworks config where` reports the resolved path, whether the file exists, the XDG source, and that the command is read-only.
- Taurworks may infer `~/Workspace` only as a non-mutating first-run convenience when no config exists and that directory already exists.
- `taurworks workspace set PATH` requires an existing directory, creates config parent directories as needed, stores a normalized absolute root, and preserves unrelated supported TOML fields.
- Taurworks should require explicit configuration before persisting workspace state, registering projects, or treating an inferred path as authoritative.
- If no global config exists and `~/Workspace` does not exist, workspace-aware commands show an unconfigured workspace root rather than recursively scanning from the current directory.
- Registry-backed project listing and activation resolution (Phase 1b/1c) are implemented; see below.

## Global project registry (Phase 1b)

Implementation status: implemented. `taurworks project register/unregister` and `taurworks project registry list` write and read `[projects.NAME]` entries in the global config.

Taurworks supports explicit registration of projects that are outside normal workspace discovery or intentionally nested in unusual locations. The registry lives in the user-global config so activation and listing can resolve projects from anywhere without recursive scans.

Example config shape:

```toml
[projects.HiddenProject]
root = "/Users/example/Workspace/TestProject/test_repo/HiddenProject"
```

Implemented commands:

```bash
taurworks project register NAME PATH
taurworks project unregister NAME
taurworks project registry list
```

Registry rules:

- A registered project name is explicit user intent and should be preferred over workspace discovery when names collide.
- Registered roots may point to intentionally weird or nested locations.
- Taurworks should not recursively scan the workspace by default to find those locations.
- Registry listing should make stale or missing paths visible without silently deleting entries.
- The registry resolves project roots; normal project status handling still decides whether the target is initialized, legacy-admin, or workspace-only.

## Workspace and registry resolution (Phase 1c)

Implementation status: implemented.

`tw projects` and `taurworks projects` merge these sources into a single status-aware view:

1. registered projects;
2. immediate children of the configured workspace root;
3. initialized projects;
4. legacy-admin projects;
5. workspace-only projects.

The listing should avoid recursive discovery by default. Registered projects cover nested or unusual locations that immediate-child workspace discovery intentionally does not find.

`tw activate NAME` resolves from anywhere using a stable order:

1. explicit registered project by name;
2. initialized project under the configured workspace root;
3. legacy-admin project under the configured workspace root;
4. workspace-only directory under the configured workspace root;
5. local/enclosing project fallback;
6. child path relative to the current directory only for explicitly local commands.

After the canonical priority list selects a candidate project, activation fallback semantics should be conservative:

```text
initialized with working_dir
  cd to working_dir

initialized without working_dir
  cd to project root with warning

workspace-only
  cd to project root with warning

legacy-admin
  cd to project root with warning; do not source legacy script by default

registered
  selected first by the priority list; resolve root by registry, then apply normal project status behavior
```

The guiding principle for this phase is: find projects reliably first, then activate them richly.

## Project/workspace metadata (filesystem-visible)
Keep project/workspace operational metadata visible and inspectable under `.taurworks/`.

## Project-root and working-directory metadata
A Taurworks project needs two distinct path concepts before activation can become useful:

- `project_root` is the directory containing `.taurworks/`. It is the owner of Taurworks-visible project metadata.
- `working_dir` is the default code/work directory for day-to-day development. It is stored relative to `project_root` so project metadata remains portable across machines and checkout locations.

Dogfooding showed that the previous command slice can create, refresh, discover, and print activation guidance, but it still treats the project root as the effective work target. Legacy projects often used an `Admin/` directory for setup guidance beside a local repository; Taurworks should instead place owned metadata in `.taurworks/` and point to the intended repository or work tree through `working_dir`.

Minimal `.taurworks/config.toml` schema:

```toml
schema_version = 1

[project]
name = "ExampleProject"

[paths]
working_dir = "repo-or-work-dir"
```

Accepted path and command rules for the dogfood-resolution slice:

- `paths.working_dir` should be relative by default and interpreted from `project_root`.
- Absolute `working_dir` values should be rejected or deferred until an explicit design covers them. (This is about the literal config string; see "Working-dir containment and symlinked work trees" below for how a relative `working_dir` whose on-disk target is a symlink is handled.)
- Empty project names in existing configs are legacy/underspecified metadata and are repaired to the project-root directory name when the config can be safely parsed and updated.
- `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` initializes the existing/current project root safely and idempotently, reusing refresh/config logic.
- `taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` creates a new project root, then delegates to init/refresh logic. It refuses accidental nested same-name creation when the current project/directory name already equals `NAME` unless `--nested` is supplied.
- `taurworks project working-dir show [PATH_OR_NAME]` displays the configured relative `paths.working_dir` or a clear unconfigured message for the selected project.
- `taurworks project working-dir set DIR --project PATH_OR_NAME` is the preferred mutation shape because it avoids ambiguous positional overloads. A no-target form may continue to mean the current project.
- `taurworks project create NAME --working-dir repo --create-working-dir` and `taurworks project working-dir set repo --create` are the explicit opt-ins for creating a missing working directory. Missing work directories should not be created silently.
- `taurworks project activate [PATH_OR_NAME] --print` reads configured `paths.working_dir`, validates it lexically (relative, no `..`; see "Working-dir containment and symlinked work trees" below), prints the absolute target path and a manual `cd` guidance command, uses the shared target resolver, and still performs no shell mutation.


Shared target resolution should be centralized across `project init`, `project create`, `project working-dir show/set`, and `project activate --print`. It should report diagnostics such as `input`, selected `project_root`, and `resolved_by` so dogfood failures like resolving `TestProject` from inside `TestProject` to `TestProject/TestProject` are visible and preventable.

### Working-dir containment and symlinked work trees

Implementation status: implemented via `WI-WORKING-DIR-SYMLINK-ESCAPE-0001` (`project_internals.relative_working_dir`, `relative_working_dir_metadata`, and the shared `check_working_dir_symlinks`).

Some projects keep `project_root` (and the non-code metadata it owns —
`.taurworks/`, archival material, other non-Git-tracked assets) on a
Google-Drive-synced `Workspace` location, while the actual Git-tracked work
tree that `working_dir` should point at lives elsewhere (for example an
SSD-local `Tempspace`, to avoid sync churn from active builds, tests, and
`git worktree` usage). The on-disk pattern is a same-named symlink:
`project_root/working_dir` is a symlink whose target is an identically-named
path under the external location, e.g.
`~/Workspace/Project/working_dir -> ~/Tempspace/.../Project/working_dir`.

`working_dir` containment must be a **lexical** check against the
configured value, not a check against the fully resolved (symlink-followed)
path:

- `paths.working_dir` must still be relative and must not contain an
  absolute path or **any** `..` component, evaluated against the literal,
  unresolved config value — a synced or shared `.taurworks/config.toml`
  must never be able to redirect activation via `..` or an absolute path.
  This is a deliberate **tightening**, not unchanged behavior: today both
  helpers resolve first and then check containment, so an in-root value
  such as `repo/../repo` is accepted. Under lexical containment it must be
  rejected, because once components are no longer resolved, a `..` that
  follows a symlink (`link/..`) would refer to the parent of the symlink's
  *target* — potentially outside `project_root` — while still looking
  lexically in-root. Rejecting every `..` is the simplest rule that stays
  safe; an existing config whose `working_dir` contains `..` will need to
  be rewritten to its plain relative form (the error message should say
  so). The rule applies to the stored `paths.working_dir` value and to the
  project-root-relative `--working-dir` argument of `project init`/`project
  create`. For `taurworks project working-dir set [DIR]`, whose `DIR` is
  interpreted relative to the current directory, the rule applies to the
  *derived stored value*, mapped as follows (decided with
  `WI-WORKING-DIR-SYMLINK-ESCAPE-0001`):
  - The current directory is the **physical** (resolved) cwd, as for every
    other `taurworks project` command — project discovery already uses it.
    A resolved path contains no symlinks, so the cwd's position under the
    resolved `project_root` is a plain, symlink-free relative prefix.
  - Leading `..` components of `DIR` step up within that prefix (safe,
    because popping a component of a symlink-free path is the same lexically
    and physically). Stepping above `project_root` is rejected as an escape,
    so `working-dir set ../sibling` from `project_root/docs` still stores
    `sibling`.
  - A `..` that follows any ordinary component of `DIR` (e.g. `link/..`,
    `repo/../repo`) is rejected, because that component might be a symlink
    and the `..` would then refer to the parent of its target.
  - The remaining components are appended unresolved, so `working-dir set
    working_dir` run from `project_root` stores `working_dir` even when that
    entry is a symlink to an external work tree.
  - With no `DIR`, the stored value is the physical cwd relative to the
    resolved `project_root`. When the shell's cwd is *inside* the external
    work tree, the physical cwd is outside `project_root`, so project
    discovery does not find the project at all (unchanged behavior). The
    logical `$PWD` is deliberately not consulted, since honoring it would
    change project discovery semantics; run `taurworks project working-dir
    set working_dir` from `project_root` instead. (Planned change: see
    "Discovery from inside a symlinked work tree" below, which adds a
    working_dir reverse lookup and maps `set` through the link.)
- The joined path (`project_root` + `working_dir`) is no longer required to
  stay under `project_root` *after following symlinks*. A `working_dir`
  component may itself be a symlink whose real target lies outside
  `project_root` — that is accepted, because the risk this rule guards
  against (a config value that lexically escapes the root) is unaffected:
  the config still only ever names a plain relative child path.
- Existence is still checked with the ordinary directory check, which
  already follows symlinks transparently. Each caller's ordinary
  missing-directory policy is unchanged: `project working-dir set` still
  requires an existing directory; `project create --working-dir` still
  records a missing path, while `project init --working-dir` still rejects
  one unless `--create-working-dir` is supplied; `--create-working-dir`
  still creates it for either command; `project activate --print` and `dev where`/`status`
  still report `working_dir_exists: False` without failing (`tw activate`,
  which runs the same diagnostics via `activate --shell`, still refuses to `cd`); `taurworks
  project working`/`taurworks working` still fail; project classification
  still marks the project not eligible for `tw activate`; legacy migration
  still sends it to manual review. (`project working-dir show` echoes the
  raw config value and performs no working_dir validation at all, so this
  design does not change it.) The work item carries the full call-site
  inventory.
- An **invalid symlink** is distinguished from an ordinary missing path: if
  any component of the lexical `project_root`/`working_dir` path is a
  symlink that is dangling or loops, both validation helpers raise the same
  `ProjectConfigError` they already raise for an absolute or escaping
  value, instead of reporting the path as missing. This rule is stated at
  the helper level deliberately: every caller keeps its existing handling of
  that error, unchanged. A command that fails on an escaping value today
  fails the same way on an invalid symlink, and a caller that already
  degrades gracefully on invalid metadata keeps doing so (for example `dev
  where`/`status` reports the configured working dir as unreadable and falls
  back to its git-root guess). In particular, `--create-working-dir` must
  never create a directory through such a symlink — `mkdir(parents=True)` on
  a resolved dangling link would otherwise silently create the external
  target, a case today's resolved-path containment check only blocks
  incidentally. A *valid* symlink component followed by a missing tail
  (`working_dir/missing`, where `working_dir` links to an existing external
  directory) is not invalid: `--create-working-dir` creates the missing
  tail inside the link's external target. That is consistent with the
  rest of this design — the external target is where the work tree lives —
  and the config value still names only a plain relative child path.
- Legacy migration's normalization of an *absolute* legacy `cd` target to a
  project-root-relative value is a separate, resolved-path check
  (`legacy._normalize_cd_target`) that this design does not change: an
  absolute legacy `cd` target reached through the symlink still resolves
  outside `project_root` and goes to manual review. Relative legacy `cd`
  targets go through the shared helpers and get the lexical rule.

This keeps the original portability/safety intent of this section (tightened, per the `..` note above) —
`paths.working_dir` can never redirect activation outside `project_root`
through the config value itself — while letting the symlink, which is a
machine-local filesystem detail never written into the committed config
value, point anywhere. No new config field, global allowlist, or trust-gate
is introduced for this: the risk this project's existing Tier 1/Tier 2
legacy-script trust model (`taurworks config legacy-sourcing`, `taurworks
project trust`) guards against is arbitrary code execution
(`project-setup.source` sourcing); a `working_dir` symlink only changes a
`cd` target, a materially smaller blast radius that doesn't warrant
equivalent gating. A name-mismatch warning (e.g. the symlink's name not
matching its target's basename) was considered and rejected as a check tied
to this change: it would be noisy for legitimate git-worktree layouts where
a workstream/worktree directory is deliberately named differently from the
project it belongs to.

### Discovery from inside a symlinked work tree

Implementation status: not yet implemented; planned via `WI-WORKING-DIR-REVERSE-DISCOVERY-0001`.

With a symlinked `working_dir` (see the section above), `tw activate` `cd`s
to the link's resolved target, outside `project_root`. Today every
cwd-based command run from there reports `project_root: unresolved`:
`taurworks dev where`/`status`/`test`, `project where`, `project working`,
`project activate --print` and `working-dir show`/`set` with no explicit
target. The cause is that discovery walks only the physical cwd's parents
for `.taurworks/`. A terminal, IDE, or agent session opened directly in the
external tree (including git worktrees created under it) fails the same
way.

Decision: cwd-based discovery becomes an ordered chain with one shared
implementation:

1. **Physical walk.** Unchanged and always first. The nearest `.taurworks/`
   in the physical cwd or its physical parents wins.
2. **Working-dir reverse lookup.** Runs only when step 1 finds nothing.
   - Among the already-known projects (registered projects plus immediate
     children of the workspace root, the same set `taurworks project list`
     shows), select the one whose resolved `paths.working_dir` contains the
     physical cwd.
   - The deepest resolved working_dir wins. An exact tie, two projects
     sharing one target, is reported as ambiguous with the candidates listed,
     and discovery stays unresolved. It never guesses.
   - Projects whose working_dir is unconfigured, missing, or invalid are
     skipped.

Diagnostics report which step resolved the project (`resolved_by` /
discovery source, naming the matched project for the reverse lookup). This
keeps the fallback inspectable rather than hidden, as AGENTS.md's "avoid
hidden magic in repo discovery" requires. The lookup reads one config file
per known project, and only on fallback, so non-symlinked layouts pay
nothing. It never scans the filesystem recursively.

`taurworks project working-dir set [DIR]` run from inside the external tree
maps the cwd back through the link. The prefix is the configured
`working_dir` value plus the cwd's path relative to the resolved target, so
running it from `<target>/sub` stores `working_dir/sub`. `DIR` then applies
with the rules above. A leading `..` may only remove components below the
link boundary; a `..` that would remove the link component itself is
rejected, because a lexical and a physical step up disagree exactly there.
This replaces the earlier "run it from `project_root` instead" guidance.

Rejected or deferred alternatives:
- **A logical `$PWD` walk (deferred).** It would be validated by the POSIX
  `pwd -L` rule: an absolute path naming the current directory, with no `.`
  or `..` components. But it only helps when the user navigated through the
  link. It fails right after `tw activate`, which `cd`s to the physical
  path, and in sessions opened at physical paths, so it would be a second
  mechanism with little added coverage. It remains a candidate if symlinks
  other than `working_dir` inside a project need discovery later.
- **Exporting `TAURWORKS_PROJECT_ROOT` from `tw activate` (rejected).**
  Shell state that goes stale on `cd` and leaks into subshells is hidden
  discovery magic.
- **Making `tw activate` `cd` to the logical `project_root/working_dir`
  path (not adopted).** It isn't needed once the reverse lookup exists, and
  it would be a visible behaviour change.

A synced project config can't steer this lookup by itself. The config names
only a relative path, and the symlink that makes the target external is a
machine-local filesystem detail. The lookup only decides which known
project the cwd belongs to; it never executes anything.

## Repo-local workflow configuration
Use `taurdev.toml` as the primary repo-local workflow configuration surface.

Optional Python projects may also provide `[tool.taurdev]` in `pyproject.toml` when that integration is preferred.

The `taurdev` naming is intentional: it identifies repository-local developer workflow orchestration settings used by `taurworks dev ...` commands.

## Why standalone `taurdev.toml` matters
A standalone `taurdev.toml` is necessary because:

- Non-Python repositories may not have `pyproject.toml`.
- Some Python projects prefer not to place developer workflow metadata in `pyproject.toml`.
- Multi-repo workspaces may need separate workflow configuration per repository.

## Design intent
This model keeps global state standardized, project/workspace state inspectable, and repo workflow behavior explicit while preserving sensible defaults.
