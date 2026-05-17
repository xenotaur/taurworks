# taurworks

Taurworks is a command-line development framework for creating, switching to, and working in multiple development projects.

## User install and shell helper setup

For normal CLI use, prefer installing Taurworks with `pipx` so the
`taurworks` command is isolated from project environments:

```bash
pipx install taurworks
```

A regular `pip` install also exposes the Python CLI:

```bash
pip install taurworks
```

The `taurworks` executable is a Python command-line program. Like any normal
child process, it cannot mutate the parent shell, so
`taurworks project activate --print` remains read-only activation guidance. The
`tw` command is a shell function provided by a manually sourced helper; only
that explicit sourced layer may export declarative activation variables and
change the current shell directory.

Print the packaged helper with:

```bash
taurworks shell print
```

To install it manually without a source checkout, redirect the packaged helper
to a location you control and source it:

```bash
mkdir -p ~/.config/taurworks
taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
source ~/.config/taurworks/taurworks-shell.sh
```

You may add a `source ~/.config/taurworks/taurworks-shell.sh` line to your
shell startup file manually if you want `tw` in every new shell. Taurworks does
not automatically edit `.bashrc`, `.zshrc`, `.profile`, or other startup files,
and package installation does not install shell hooks.

```bash
tw activate [PATH_OR_NAME]
taurworks help
tw help
```

On success, `tw activate` validates the project activation config, applies
validated `[activation.exports]`, activates a configured Conda environment when
`[activation.environment]` is present, runs `cd` to the resolved destination in
the current shell, and prints `activation.message` when configured. The shell
mutation order is: export configured variables, run `conda activate <name>` when
configured, change directory to `[paths].working_dir` or the project root
fallback, print a concise changed-directory line, then print the configured
message. Name-based activation uses the user-global registry and configured
workspace root, so `tw activate NAME` works from outside the workspace and after
switching into another project's working directory. Normal activation failures
are concise and actionable; use `tw activate [PATH_OR_NAME] --verbose` or
`tw activate [PATH_OR_NAME] --debug` to print the full read-only diagnostic
block from `taurworks project activate [PATH_OR_NAME] --print`. That
`taurworks project activate --print` command remains safe to run directly when
you want activation details without changing directories, exporting variables,
or activating environments.

`taurworks help` is an alias for `taurworks --help`. Non-activation `tw ...`
commands delegate to `taurworks ...`; `tw help` is an alias for `tw --help`.
Only `tw activate ...` uses validated
`taurworks project activate --print` output to run `cd` in the current shell.
Future readiness messages, environment activation, trusted startup hooks, and
legacy `Admin/project-setup.source` migration are in-development topics documented
in `project/design/activation_extension.md`.

Declarative activation currently supports a readiness message, string environment-variable
exports, and Conda environment activation only. Virtualenv activation, Docker
activation, arbitrary user hooks/scripts, and legacy `Admin/project-setup.source`
migration remain deferred.

Configure Conda activation in `.taurworks/config.toml` with:

```toml
[activation.environment]
type = "conda"
name = "LCATS"
```

Only `type = "conda"` is supported initially, and `name` is required. Taurworks
validates Conda names conservatively, does not run `conda init`, does not create
or install Conda environments, and does not edit shell startup files. Your shell
must already provide a working `conda activate` command or function before you
run `tw activate`; if Conda activation is unavailable or `conda activate <name>`
fails, `tw activate` returns non-zero and avoids changing directory.
`taurworks project activate [PATH_OR_NAME] --print` remains read-only and only
reports environment fields such as `environment_configured`,
`environment_type`, and `environment_name`; Python does not perform activation.

## Developer setup

Use the repository script as the canonical setup path for local development, CI,
and Codex-style environments:

```bash
./scripts/develop
```

The script first checks whether the active environment already satisfies the
minimum build backend prerequisites required by `pyproject.toml`, installs
`setuptools>=64` and `wheel` only when needed, then performs the constrained
editable install with the `dev` extra. It intentionally uses
`--no-build-isolation` so setup can work in environments where build isolation
cannot download `setuptools` through a network proxy. Formatter and linter
versions are constrained in `constraints-dev.txt` instead of being hand-pinned
in CI; backend packages are not exact-pinned there so sufficient conda/Codex
bootstrap versions are not replaced unnecessarily.

After setup, run the standard checks from the repository root:

```bash
./scripts/lint
./scripts/test
```

Portability-sensitive tests can also be run with isolated global-config
locations:

```bash
./scripts/test-portability
```

This wrapper creates temporary `HOME`, `XDG_CONFIG_HOME`, and
`TAURWORKS_WORKSPACE` values before running the unittest suite, so local checks
do not read or write a developer's real `~/.config/taurworks/config.toml` or
`~/Workspace`. It is intended for macOS dogfooding as well as Linux validation.
macOS can canonicalize temporary paths such as `/var/folders/...` to
`/private/var/folders/...`; tests that inspect CLI diagnostics should parse
`key: value` output and compare path fields semantically with the shared test
helpers instead of matching raw path substrings. Python CI runs the standard
and portability test suites on both Ubuntu and macOS.

Formatting uses Black through the thin formatter wrapper. To check formatting
with a diff without rewriting files, run:

```bash
./scripts/format --check --diff
```

For Codex Cloud environment initialization, use `./scripts/develop` rather than
`python -m pip install -e ".[test]"`. The `test` extra is retained as an empty
compatibility extra because Taurworks tests currently use only the Python
standard-library `unittest` runner; use the `dev` extra, via `./scripts/develop`,
when formatter and linter tools are needed.

## Current command model (design-aligned)

Taurworks currently standardizes on one primary executable:

```bash
taurworks
```

The intended command model is namespaced:

- `taurworks config ...` for user-global configuration diagnostics.
- `taurworks workspace ...` for user-global workspace root defaults.
- `taurworks project ...` for project/workspace lifecycle operations.
- `taurworks dev ...` for repository/developer workflow operations.
- `taurworks shell ...` for printing explicit, sourceable shell integration.

These namespaces are expected to share a common configuration/discovery core where their responsibilities overlap.

### Implementation status and compatibility

Status note: `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH` now provide the first XDG-style user-global config slice. `taurworks project ...` now includes implemented discovery, scaffold, existing-root initialization, working-directory metadata, and read-only guidance commands (`where`, `list`, `register`, `unregister`, `registry list`, `refresh`, `init`, `create`, `working-dir show`, `working-dir set`, and `activate --print`). `taurworks dev ...` now exists as a minimal read-only diagnostics namespace for repository/developer workflow context (`where` and `status`); full workflow automation remains future work.
Implementation note: `taurworks project where`, `taurworks project list`, `taurworks project refresh`, `taurworks project init`, `taurworks project register NAME PATH`, `taurworks project unregister NAME`, `taurworks project registry list`, `taurworks project create`, `taurworks project working-dir show [PATH_OR_NAME]`, and `taurworks project activate [PATH_OR_NAME] --print` share consolidated internals for project resolution, discovery, and safe `.taurworks/` scaffolding behavior where appropriate.
Design note: dogfooding confirmed the `project_root` (the directory containing `.taurworks/`) and `working_dir` (the default code/work directory, stored relative to `project_root`) model. The accepted design separates `project init` for existing/current roots from `project create` for new roots, centralizes target resolution diagnostics, makes working-directory creation explicit, and prevents accidental nested same-name projects. `tw activate` is now the explicit opt-in shell-mutating wrapper for changing the current shell directory. Broad `taurworks dev ...` automation, automatic shell startup-file edits, virtualenv/Docker environment activation, and multi-repo management remain out of scope.

The namespaced model is the active design direction. The currently shipped CLI remains compatibility-first and continues to support top-level lifecycle commands such as:

- `taurworks create`
- `taurworks refresh`
- `taurworks activate`
- `taurworks projects`

The currently implemented namespaced commands are:

- `taurworks config where` (implemented, read-only global config path diagnostics)
- `taurworks workspace show` (implemented, read-only configured/inferred workspace root display)
- `taurworks workspace set PATH` (implemented, writes `[workspace].root` to user-global config; PATH must already exist)
- `taurworks project where` (implemented, read-only diagnostics)
- `taurworks project list` (implemented, read-only discovery listing)
- `taurworks project register NAME PATH` (implemented, writes `[projects.NAME].root` to user-global config)
- `taurworks project unregister NAME` (implemented, removes a registry entry without deleting project files)
- `taurworks project registry list` (implemented, read-only registry listing with path/config status and collision visibility)
- `taurworks project root PROJECT` (implemented, prints exactly one absolute registered/resolved project root path for shell composition)
- `taurworks project working PROJECT` (implemented, prints exactly one absolute preferred working-directory path for shell composition)
- `taurworks project refresh [PATH_OR_NAME]` (implemented, safe idempotent metadata scaffolding repair)
- `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` (implemented, safe idempotent initialization of an existing/current project root)
- `taurworks project working-dir show [PATH_OR_NAME]` (implemented, target-aware project working-directory metadata display)
- `taurworks project working-dir set [DIR]` (implemented, safe project working-directory metadata update; `set DIR --project PATH_OR_NAME` is the preferred planned target-aware shape)
- `taurworks project create NAME [--working-dir DIR]` (implemented, creates under the configured workspace root by default, then safely initializes metadata)
- `taurworks project create NAME --local [--working-dir DIR]` (implemented, explicit cwd-relative create behavior)
- `taurworks project create NAME --path PATH [--working-dir DIR]` (implemented, explicit target path creation; `PATH` basename must match `NAME`)
- `taurworks project activate [PATH_OR_NAME] --print` (implemented, read-only activation guidance output)
- `taurworks dev where` (implemented, read-only repository/workspace diagnostics)
- `taurworks dev status` (implemented, read-only summary that explicitly leaves detailed VCS automation for future work)
- `taurworks shell print` (implemented, prints the packaged sourceable `tw` shell helper)
- `tw root PROJECT` and `tw working PROJECT` after manually sourcing the printed helper (implemented, convenience aliases that delegate to the same path emitters)
- `tw activate [PATH_OR_NAME]` after manually sourcing the printed helper (implemented, explicit shell function that changes directory only)
- `tw activate [PATH_OR_NAME] --verbose` or `--debug` (implemented, prints detailed activation diagnostics on failure)
- `taurworks help` (implemented, alias for `taurworks --help`)
- `taurworks help COMMAND` (implemented for existing command namespaces, equivalent to `taurworks COMMAND --help`)
- `tw help` after manually sourcing the printed helper (implemented, alias for `tw --help`)

Quick namespace help:

```bash
taurworks help
taurworks config --help
taurworks workspace --help
taurworks project --help
taurworks dev --help
taurworks help project
taurworks help dev
taurworks help shell
```

## User-global config and workspace root

Taurworks stores user-level defaults in an XDG-style TOML config file:

```text
$XDG_CONFIG_HOME/taurworks/config.toml
```

When `XDG_CONFIG_HOME` is unset, Taurworks falls back to:

```text
~/.config/taurworks/config.toml
```

The first implemented global settings are the workspace root and an explicit project registry:

```toml
schema_version = 1

[workspace]
root = "/Users/example/Workspace"

[projects.HiddenProject]
root = "/Users/example/Workspace/TestProject/test_repo/HiddenProject"
```

Use `taurworks config where` to inspect the resolved config path, whether the file exists, which XDG source selected it, and that the command is read-only. Use `taurworks workspace show` to display the configured workspace root without creating any files. If no config file exists and `~/Workspace` already exists, `workspace show` may report that directory as `inferred`; inferred roots are informational only and are not silently written. Use `taurworks workspace set PATH` to explicitly persist a workspace root. The `PATH` must already exist, parent config directories are created as needed, and unrelated supported TOML keys are preserved.

The project registry is for projects that should be globally discoverable even when they live outside the configured workspace root, under nested/weird paths, or in locations that direct workspace child discovery should not scan recursively. Register a project with `taurworks project register NAME PATH`; Taurworks normalizes `PATH`, requires it to exist by default, stores it as `[projects.NAME].root`, warns when `.taurworks/config.toml` is missing, and refuses duplicate names unless `--force` is supplied. Use `--allow-missing` only when recording an intentional future path; existing paths must still be directories. Remove only the global entry with `taurworks project unregister NAME`; this command does not delete project files or project-local `.taurworks/config.toml`. Inspect the registry without mutation using `taurworks project registry list`, which reports root paths, whether those paths exist, whether project-local config exists, and whether a registry name collides with a direct child of the configured workspace root.

Registry entries differ from workspace discovery: workspace discovery remains direct and non-recursive in this phase, while the registry is an explicit allow-list of named roots. If a registry name matches a direct workspace child project name, registry commands and activation treat the explicit registry entry as authoritative. Broad project listing collapses duplicate registry/workspace roots into one row and marks the row as registered.

`taurworks dev where` reports the current directory, detected Taurworks project root, configured working directory, repository/work-directory guess, whether the current directory is inside that configured working directory, and that no mutation was performed. `taurworks dev status` reports a smaller read-only summary and states that detailed VCS workflow automation is future work; it does not shell out to `git`.

`taurworks project where` intentionally does not mutate files, environments, or shell state.
`taurworks project list` is also non-mutating and reports discoverable projects plus discovery limitations.
`taurworks help` delegates to top-level `taurworks --help`, and `taurworks help COMMAND` delegates to existing command help. All non-activation `tw ...` commands delegate to `taurworks ...`, so `tw dev where` and `tw dev status` use the same read-only diagnostics; `tw help` delegates to `taurworks --help`. Only `tw activate ...` has shell-mutating behavior, and detailed activation diagnostics stay available through `tw activate ... --verbose`, `tw activate ... --debug`, or direct `taurworks project activate ... --print`.

## `taurworks projects` / `tw projects` workspace statuses

The top-level `taurworks projects` command lists direct children of the configured global workspace root plus explicit global registry entries. If no global workspace is configured, it falls back to `TAURWORKS_WORKSPACE` and then `~/Workspace` for compatibility. `tw projects` delegates to the same command, so both outputs use the same status labels.

Statuses are intentionally descriptive rather than promises that every listed directory is immediately activatable:

- `initialized`: the directory contains `.taurworks/config.toml`. It is eligible for `tw activate` only when `[paths].working_dir` is configured in that file and the resolved working directory exists on disk.
- `workspace-only`: the directory exists in the workspace but does not contain `.taurworks/config.toml`. It is visible in workspace listings, but it is not currently eligible for `tw activate`. If `.taurworks/` exists without a readable `config.toml`, detailed output reports that partial metadata explicitly. Initialize it with `taurworks project init PATH --working-dir DIR` after choosing an existing work directory, or add `--create-working-dir` when Taurworks should create that work directory.
- `legacy-admin`: the directory contains `Admin/project-setup.source`, which Taurworks recognizes as a legacy Taurworks-style setup. Taurworks lists the project with this status for visibility, but `tw activate` does not source that file automatically. A future migration tool or script may convert legacy setups into `.taurworks/config.toml`; migration is not implemented in this slice.

Default output stays compact:

```text
Available projects:

- TestProject    initialized
- Taurworks      workspace-only
- EmbodiedAI     legacy-admin
```

Use `taurworks projects --details` when you need paths, metadata-directory presence, config presence, legacy setup presence, working-directory metadata, and activation-eligibility diagnostics. Classification is read-only: listing projects does not source scripts, activate environments, edit startup files, or create/migrate project metadata.

Breaking command removals/renames are intentionally deferred until a migration path is explicitly documented and implemented.


## Working-directory metadata

Taurworks now supports a minimal `.taurworks/config.toml` model that records the default work directory separately from the project metadata root:

```toml
schema_version = 1

[project]
name = "ExampleProject"

[paths]
working_dir = "repo-or-work-dir"
```

`project_root` is the directory containing `.taurworks/`. `working_dir` is the default code/work directory used for day-to-day development and is stored relative to `project_root` for portability.

Current implemented commands can be used from inside a Taurworks project:

```bash
taurworks project working-dir show [PATH_OR_NAME]
taurworks project working-dir set [DIR]
```

Implemented target-aware `working-dir show` behavior:

- no target resolves the current Taurworks project when the command is run inside one;
- an existing path inside a Taurworks project resolves to the enclosing project root for this read-only command;
- a target matching the current project name resolves to the current project root instead of an unintended child path;
- otherwise the target is treated as a child path relative to the current directory and fails safely if no `.taurworks/` metadata is present;
- output includes `input`, `project_root`, and `resolved_by` diagnostics.

`working-dir set` remains scoped to the current project in this slice. Working-directory paths remain relative to `project_root`; absolute paths and paths that escape `project_root` via `..` are rejected/deferred until a later design explicitly accepts them. `taurworks project init --working-dir DIR --create-working-dir` is the implemented explicit opt-in for creating a missing working directory during existing-root initialization; without that flag, missing working directories fail safely.

`taurworks project activate [PATH_OR_NAME] --print` reads this metadata, uses global registry/workspace-aware name resolution, and prints activation guidance. It remains read-only. `tw activate [PATH_OR_NAME]`, provided by the manually sourced helper from `taurworks shell print`, is the explicit shell-mutating layer that changes the current directory after validating Taurworks output. Default `tw activate` output is concise; add `--verbose` or `--debug` to a `tw activate` call when you want the full diagnostic block on failure.

Activation resolution for bare names is stable and global-first: explicit registry entry by name; direct initialized child of the configured workspace root; direct legacy-admin child of the configured workspace root; direct workspace-only child of the configured workspace root; current/enclosing project fallback when no name is provided or the name matches the current project; and explicit path-like inputs for local/path-oriented activation. Unresolved bare names do not silently scan the current directory recursively.

Activation behavior is intentionally safe. Initialized projects with `[paths].working_dir` change to that directory when it exists. Initialized projects without `working_dir` change to the project root and warn. Workspace-only projects also change to the project root and warn that the project is not initialized. Legacy-admin projects change to the project root and warn that `Admin/project-setup.source` exists but was not sourced. Registered projects first resolve their registry root, then use the same initialized/workspace-only/legacy-admin behavior. Taurworks still does not source scripts, activate Conda/venv/Docker environments, run hooks, edit shell startup files, or create missing working directories during activation.

## Script-friendly project path emitters

Use `taurworks project root PROJECT` when shell scripts need the registered/resolved project root directory, and use `taurworks project working PROJECT` when they need the preferred day-to-day working directory. The sourced `tw` helper provides convenience aliases: `tw root PROJECT` and `tw working PROJECT`.

These commands are designed for shell composition: on success they emit exactly one absolute path to stdout with a trailing newline and no labels or extra formatting. Diagnostics go to stderr and failures return a nonzero exit code with no stdout. Quote command substitutions so paths containing spaces remain safe:

```bash
pushd "$(tw working LogicalRoboticsHarness)"
git -C "$(tw project working LogicalRoboticsHarness)" status
code "$(tw root Taurworks)"
```

`taurworks project working PROJECT` currently uses `[paths].working_dir` when configured and falls back to the project root when no distinct working directory is configured. The preferred working directory may intentionally diverge from the project root over time.

## Dogfood workflows for init/create/activation guidance

Use `project create` when Taurworks should make a new project-root directory, then initialize metadata inside it. Bare project names now follow the user-global workspace model: after `taurworks workspace set ~/Workspace`, `taurworks project create TestProject` creates `~/Workspace/TestProject` even when the command is run from another directory. Add `--create-working-dir` only when Taurworks should also create a missing code/work directory:

```bash
taurworks workspace set ~/Workspace
cd /tmp/scratch
taurworks project create TestProject --working-dir test_repo --create-working-dir
taurworks project activate TestProject --print
```

Expected shape:

```text
~/Workspace/TestProject/
  .taurworks/
    config.toml
  test_repo/
```

Use `--local` to explicitly opt into the old cwd-relative behavior:

```bash
cd /tmp/scratch
taurworks project create LocalProject --local --working-dir repo --create-working-dir
```

Expected shape:

```text
/tmp/scratch/LocalProject/
  .taurworks/
    config.toml
  repo/
```

Use `--path PATH` for an explicit project root. When `NAME` is supplied, the basename of `PATH` must match `NAME` so the name is not silently ignored:

```bash
taurworks project create CustomProject --path /custom/path/CustomProject
```

Projects created outside the configured workspace root are not automatically registered; the create output warns that they will not appear in global project discovery unless registered with `taurworks project register NAME PATH`. If no workspace root is configured, bare `project create NAME` fails clearly and asks you to run `taurworks workspace set PATH` or use `taurworks project create NAME --local`. Path-like positional targets remain supported for compatibility, but `--path PATH` is the documented explicit path form. `--working-dir` is always interpreted relative to the resolved project root, and `--create-working-dir` creates only that validated in-root working directory. `--nested` still only bypasses the guard against accidental same-name cwd-relative nested projects.

Use `project init` when the project root already exists or when you are already inside it. Without `--create-working-dir`, the configured working directory must already exist:

```bash
mkdir -p ~/Workspace/TestProject/test_repo
cd ~/Workspace/TestProject
taurworks project init --working-dir test_repo
taurworks project activate --print
```

Use `working-dir set` from inside the project to change the default work directory after initialization. The directory must already exist in this slice:

```bash
cd ~/Workspace/TestProject
mkdir other_repo
taurworks project working-dir set other_repo
taurworks project working-dir show
taurworks project activate --print
```

Target-aware read-only commands accept either a path or the configured/current project name. From inside `TestProject`, naming `TestProject` resolves the current project root instead of creating or inspecting an accidental `TestProject/TestProject` child:

```bash
cd ~/Workspace
taurworks project working-dir show TestProject
taurworks project activate TestProject --print

cd ~/Workspace/TestProject
taurworks project activate TestProject --print
```

If you run `taurworks project create TestProject` from inside an existing/current `TestProject`, Taurworks refuses the likely accidental nested same-name project. Pass `--nested` only when `TestProject/TestProject` is intentional. `activate --print` is read-only throughout these workflows: it prints inspectable `cd ...` guidance but does not change your shell, create directories, write files, activate Conda, or source shell scripts. Use the explicitly sourced `tw activate` shell helper when you want Taurworks to change the current shell directory.

## `taurworks project where`

Use this command to inspect Taurworks project/config/discovery resolution without mutating anything:

```bash
taurworks project where
```

The output reports:

- current working directory
- nearest discovered project root candidate (based on `.taurworks/` metadata)
- discovery source
- XDG-style config path candidate and whether it currently exists (relative `XDG_CONFIG_HOME` values are ignored)
- whether project metadata was found
- current resolution limitations in plain language

## `taurworks project list`

Use this command to list discoverable Taurworks projects without mutating anything:

```bash
taurworks project list
```

Current output reports:

- current working directory
- discovery source used for this run
- number of discovered projects
- each discovered project name/path
- limitations of the current discovery stage

Current stage behavior:

- if the current directory (or one of its parents) contains `.taurworks/`, list that resolved project root
- otherwise, scan only direct child directories of the current working directory for `.taurworks/`
- if none are found, report zero projects with a clear no-projects-found line

This slice is intentionally minimal for now: it provides read-only diagnostics/discovery plus a safe repair/initialization refresh for Taurworks-owned metadata only.


## `taurworks project register`, `unregister`, and `registry list`

Use the global project registry for projects that intentionally live outside normal workspace discovery or in nested locations that should still be addressable by name later:

```bash
taurworks project register HiddenProject /path/to/HiddenProject
taurworks project registry list
taurworks project unregister HiddenProject
```

Behavior and safety:

- `project register NAME PATH` writes only the XDG global config entry `[projects.NAME].root` and preserves unrelated global config text.
- `PATH` is expanded and resolved before storage.
- `PATH` must exist and be a directory unless `--allow-missing` is supplied; `--allow-missing` is intended for deliberate future paths.
- registering a path without `.taurworks/config.toml` is allowed but reported as a warning so out-of-tree or not-yet-initialized projects remain visible.
- duplicate registry names fail clearly unless `--force` is supplied, in which case the entry is overwritten.
- `project unregister NAME` removes only the global registry entry, preserves unrelated global config text, and never deletes project files.
- `project registry list` is read-only and shows each registered root, whether that path exists, whether `.taurworks/config.toml` exists, and whether the name collides with a direct child of the configured workspace root.

Collision policy is intentionally simple for this phase: explicit registry commands and activation treat `[projects.NAME]` as the registry entry, and list/register output makes workspace-child name collisions visible. `taurworks projects` / `tw projects` include both workspace children and registered roots, but collapse duplicate roots into one row with a registered source marker.

## `taurworks project refresh`

Use this command to safely create missing Taurworks-owned project scaffolding:

```bash
taurworks project refresh [PATH_OR_NAME]
```

Behavior:

- with no argument, refreshes the current working directory
- with an argument, treats it as a path (or path-like name) rooted in the current directory when not already existing
- if the target directory does not exist, creates it so Taurworks metadata can be scaffolded there
- creates only missing Taurworks-owned scaffolding within the target (`.taurworks/` and `.taurworks/config.toml`)
- writes new configs with `schema_version = 1`, `[project].name` defaulting to the project-root directory name, and no `[paths].working_dir` until configured
- repairs legacy empty project names and missing/invalid schema versions when the config can be safely parsed and rewritten with Taurworks’ small supported TOML shape
- preserves supported unrelated scalar keys and one-level tables during repair rewrites, but warns and skips config updates for unsupported TOML shapes or keys rather than rewriting them incorrectly
- rejects future integer schema versions until an explicit migration path exists
- prints a truth-first summary of found, missing, created, updated, skipped, and warnings

This command is intentionally safe and idempotent: repeated runs should report no changes needed once minimal scaffolding exists.

## `taurworks project init`

Use this command to initialize an existing/current directory as a Taurworks project root:

```bash
taurworks project init
taurworks project init PATH
taurworks project init --working-dir repo
taurworks project init --working-dir repo --create-working-dir
```

Behavior:

- with no argument, initializes the current working directory;
- with `PATH`, initializes that existing directory;
- missing project roots fail clearly because `init` is for existing/current directories; use `taurworks project create` when a new project root should be created;
- delegates to the same safe refresh/config scaffolding used by `project refresh`, creating or repairing only Taurworks-owned `.taurworks/` metadata;
- is safe and idempotent: repeated runs do not duplicate files, preserve unrelated files, and repair safe legacy metadata such as empty project names;
- preserves existing `[paths].working_dir` metadata unless `--working-dir DIR` is provided;
- stores `--working-dir DIR` as a normalized path relative to `project_root`;
- rejects absolute working-directory paths and paths that escape the project root;
- requires `DIR` to exist by default;
- creates a missing `DIR` only when `--create-working-dir` is supplied;
- rejects `--create-working-dir` when `--working-dir` is omitted;
- resolves an explicit target through the shared project resolver so a current project name or current directory basename initializes the current project root instead of an accidental nested same-name child path.

The command prints a summary with `input`, `project_root`, `resolved_by`, `root_exists`, `root_created`, `config_path`, `changed`, `working_dir_requested`, `working_dir`, `working_dir_exists`, `working_dir_created`, and any `warnings`. Refresh warnings are reported separately from fatal init failures.

## Shared project target resolution

Existing project commands use shared target-resolution internals where appropriate. State-changing scaffold commands preserve their documented create/refresh behavior. `taurworks project activate --print`, `tw activate`, `taurworks projects`, and `tw projects` now use global registry/workspace-aware semantics:

1. A bare name matching `[projects.NAME]` resolves to the registered root.
2. A bare name matching a direct initialized child of the configured workspace root resolves to that child.
3. A bare name matching a direct legacy-admin child of the configured workspace root resolves to that child without sourcing legacy setup.
4. A bare name matching a direct workspace-only child of the configured workspace root resolves to that child with a warning.
5. The current/enclosing project is used as a fallback when no name is provided or the name matches the current project.
6. Explicit path-like inputs, such as `./Project`, `/path/to/Project`, or names containing path separators, use local path resolution.

State-changing scaffold commands keep path-only create/refresh target behavior. `taurworks project create NAME` remains cwd-relative in this focused PR; defaulting create to the configured workspace root is deferred rather than changed silently.

Outputs should make this choice inspectable, for example:

```text
- input: TestProject
- project_root: /path/to/TestProject
- resolved_by: current_project_name
```

## `taurworks project create`

Use this command to create a new project root directory, then initialize it with safe Taurworks metadata:

```bash
taurworks project create NAME
taurworks project create NAME --working-dir DIR
taurworks project create NAME --working-dir DIR --create-working-dir
taurworks project create NAME --nested
```

Command intent is deliberately split:

- `project init` initializes an existing/current directory.
- `project create` creates a new project root, then reuses the same safe refresh/config scaffolding used by init.

`project create NAME` remains cwd-relative in this phase. It does not silently default to the configured workspace root yet; cd to the workspace manually or pass an explicit path when you want creation somewhere else. A future focused change can add clearer `--local`, `--path PATH`, or `--register` creation behavior.

Behavior:

- `project create NAME` creates `./NAME` when it is missing and initializes `./NAME/.taurworks/` without overwriting unrelated files. Existing project roots are safely refreshed.
- `--working-dir DIR` records `paths.working_dir = "DIR"` after validating that `DIR` is relative and stays inside the project root. It does not create `DIR` by default.
- `--working-dir DIR --create-working-dir` creates the missing working directory inside the new project root after validation, then records the same metadata.
- `--create-working-dir` is rejected unless `--working-dir` is also supplied.
- absolute working-directory paths and paths that escape `project_root` are rejected.
- `project create NAME` refuses accidental `NAME/NAME` nesting when the current project name or current directory basename already equals `NAME`. Use `taurworks project init` to initialize or repair the current directory.
- `--nested` allows intentional nested same-name project creation after the same path and working-directory safety checks pass.
- `project create` with no `NAME` is preserved as a compatibility alias for current-directory initialization, but `taurworks project init` is preferred and documented for that use.

The command prints a summary with `project_root`, `root_created`, delegated refresh details, `working_dir_requested`, `working_dir`, `working_dir_exists`, `working_dir_created`, `working_dir_changed`, and any warnings.

## `taurworks project activate --print`

Use this command to resolve a project and print activation guidance only:

```bash
taurworks project activate [PATH_OR_NAME] --print
```

Behavior:

- with no argument, resolves from the current working directory
- with an argument, resolves the path/name using the same shared project-resolution internals as other `project` lifecycle commands
- reads `.taurworks/config.toml` and uses `[paths].working_dir` when it is configured
- validates that configured `working_dir` metadata is relative and resolves safely inside `project_root`
- prints `project_root`, configured `working_dir`, resolved absolute working-directory path, whether that path exists, and `shell_mutation: not performed`
- prints an inspectable command such as `cd /absolute/path/to/working_dir` only as guidance; Taurworks does not execute it
- reports a clear unconfigured diagnostic and suggests `taurworks project working-dir set [DIR]` when no `working_dir` is configured
- reports a missing configured working-directory path clearly and does not pretend activation is complete
- rejects invalid escaping or absolute `working_dir` config safely
- does not source scripts
- does not activate conda/virtualenv
- does not change your parent shell state
- does not write, refresh, create, or delete project files

This command remains intentionally non-mutating. Actual current-shell mutation is limited to the explicitly sourced `tw activate` shell function described below.

## `tw activate` shell helper

Use `tw activate` when you explicitly want Taurworks to change the current shell directory. A standalone executable cannot change its parent shell directory, so this helper is implemented as a sourceable shell function packaged with Taurworks. Print and source it manually:

```bash
mkdir -p ~/.config/taurworks
taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
source ~/.config/taurworks/taurworks-shell.sh
```

After it is sourced, `tw` behaves as follows:

- `tw activate [PATH_OR_NAME]` calls `taurworks project activate [PATH_OR_NAME] --shell`, consumes validated shell assignments generated by Taurworks, exports configured variables, and runs `cd -- "$resolved_working_dir"` only when the resolved working directory exists.
- `taurworks project activate [PATH_OR_NAME] --print` remains read-only human guidance. It reports whether an activation message and exports are configured, including export names and counts, but hides export values.
- `tw project where`, `tw project list`, `tw project create ...`, and other non-activation invocations delegate directly to `taurworks ...`.
- failures print Taurworks diagnostics and do not change directory or apply partial exports when export-name validation fails.

Project-local `.taurworks/config.toml` may include this safe declarative activation slice:

```toml
schema_version = 1

[project]
name = "Alpha"

[paths]
working_dir = "repo"

[activation]
message = "Ready for work on project Alpha"

[activation.exports]
NODE_OPTIONS = "--max-old-space-size=8192"
```

Then run:

```bash
tw activate Alpha
```

Activation export names must match `[A-Za-z_][A-Za-z0-9_]*`, and export
values must be strings. Taurworks shell-quotes generated export values before
the sourced helper evaluates them; values are exported literally, so `~` is not
expanded inside export values in this slice. Normal human output never prints
export values.

Basic dogfood workflow:

```bash
source ~/.config/taurworks/taurworks-shell.sh

taurworks workspace set ~/Workspace
cd /tmp/scratch
taurworks project create TestProject --working-dir test_repo --create-working-dir
tw activate TestProject
pwd
```

Expected result:

```text
~/Workspace/TestProject/test_repo
```

The shell helper intentionally does not edit `.bashrc`, `.zshrc`, `.profile`, or any other shell startup file; add a `source ...` line yourself only if you choose. It does not source arbitrary project files and does not activate Conda, virtualenv, or other environments. Bash is the primary supported shell for this first wrapper layer; the implementation uses portable shell-function features that are also expected to work when sourced by zsh.

## Safety and shell-integration guardrails

Taurworks documentation and command behavior should follow conservative shell safety:

- Do not silently mutate shell startup files (`.bashrc`, `.bash_profile`, etc.).
- Prefer commands that print shell instructions when parent-shell mutation is required.
- Keep environment activation explicit and inspectable (`source ...` performed by the operator).
- Make state-changing operations explicit; avoid implying hidden side effects.

## Phased roadmap status

Current phase work is focused on:

1. Documentation/design alignment.
2. Command-model clarification (`project` vs `dev`).
3. Shared configuration/discovery expectations.
4. Safety guardrails and migration-path clarity.

Out of scope for this phase:

- Immediate implementation of every planned `taurworks dev` command beyond the minimal read-only diagnostics scaffold.
- Breaking removals of compatibility commands.
- Broad refactors unrelated to command-model alignment.

See `project/roadmap/roadmap.md` and `project/design/unified_command_model.md` for detail.

## Python package development

For Python package and CLI development, use the repository's constrained developer setup from the repository root:

```bash
./scripts/develop
```

That script installs Taurworks in editable mode with the `dev` extra using the active environment's existing pip, then applies `constraints-dev.txt`, which is the canonical source of truth for exact developer-tool versions such as Black and Ruff. GitHub Actions intentionally uses the same setup path so local development, CI, and Codex-style environments resolve the same tooling without an unconditional pip-upgrade network dependency.

Then validate the package import and CLI entry point:

```bash
python -c "import taurworks; print(taurworks.__file__)"
taurworks --help
taurworks help
taurworks project --help
python -m taurworks.cli --help
```

The import package is provided from `src/taurworks/` using a standard `src/` layout.

## Legacy shell utility inventory (historical)

The repository still contains historical shell utilities under `bin/` and `sourceme/`. These artifacts remain available, but the command model and roadmap focus for Taurworks development is the `taurworks` executable and the documented namespaced direction above.

## Local quality commands

Use the repository scripts as CI entry points:

```bash
./scripts/develop
./scripts/format
./scripts/format --check --diff
./scripts/lint
./scripts/test
./scripts/smoke
```

GitHub Actions uses the same constrained setup path and quality-script entry points in `.github/workflows/python-ci.yml`. Codex Cloud agents should also start with `./scripts/develop` and should avoid ad-hoc commands such as `pip install black==... ruff==...`; exact developer-tool pins belong in `constraints-dev.txt`.
