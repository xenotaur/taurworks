# taurworks

Taurworks is a command-line development framework for creating, switching to, and working in multiple development projects.

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

- `taurworks project ...` for project/workspace lifecycle operations.
- `taurworks dev ...` for repository/developer workflow operations.

Both namespaces are expected to share a common configuration/discovery core.

### Implementation status and compatibility

Status note: `taurworks project ...` now includes implemented discovery, scaffold, existing-root initialization, working-directory metadata, and read-only guidance commands (`where`, `list`, `refresh`, `init`, `create`, `working-dir show`, `working-dir set`, and `activate --print`). `taurworks dev ...` remains planned and is not implemented yet.
Implementation note: `taurworks project where`, `taurworks project list`, `taurworks project refresh`, `taurworks project init`, `taurworks project create`, `taurworks project working-dir show [PATH_OR_NAME]`, and `taurworks project activate [PATH_OR_NAME] --print` share consolidated internals for project resolution, discovery, and safe `.taurworks/` scaffolding behavior where appropriate.
Design note: dogfooding confirmed the `project_root` (the directory containing `.taurworks/`) and `working_dir` (the default code/work directory, stored relative to `project_root`) model. The accepted design separates `project init` for existing/current roots from `project create` for new roots, centralizes target resolution diagnostics, makes working-directory creation explicit, and prevents accidental nested same-name projects. `tw activate` is now the explicit opt-in shell-mutating wrapper for changing the current shell directory. Full `taurworks dev ...`, automatic shell startup-file edits, environment activation, and multi-repo management remain out of scope.

The namespaced model is the active design direction. The currently shipped CLI remains compatibility-first and continues to support top-level lifecycle commands such as:

- `taurworks create`
- `taurworks refresh`
- `taurworks activate`
- `taurworks projects`

The scaffolded `project` namespace currently includes implemented discovery and safe scaffold commands:

- `taurworks project where` (implemented, read-only diagnostics)
- `taurworks project list` (implemented, read-only discovery listing)
- `taurworks project refresh [PATH_OR_NAME]` (implemented, safe idempotent metadata scaffolding repair)
- `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]` (implemented, safe idempotent initialization of an existing/current project root)
- `taurworks project working-dir show [PATH_OR_NAME]` (implemented, target-aware project working-directory metadata display)
- `taurworks project working-dir set [DIR]` (implemented, safe project working-directory metadata update; `set DIR --project PATH_OR_NAME` is the preferred planned target-aware shape)
- `taurworks project create [PATH_OR_NAME] [--working-dir DIR]` (implemented, safe idempotent create wrapper around refresh with optional working-directory metadata)
- `taurworks project activate [PATH_OR_NAME] --print` (implemented, read-only activation guidance output)
- `tw activate [PATH_OR_NAME]` after `source taurworks-shell.sh` (implemented, explicit shell function that changes directory only)

Quick namespace help:

```bash
taurworks project --help
```

`taurworks project where` intentionally does not mutate files, environments, or shell state.
`taurworks project list` is also non-mutating and reports discoverable projects plus discovery limitations.
All non-activation `tw ...` commands delegate to `taurworks ...`; only `tw activate ...` has shell-mutating behavior.

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

`taurworks project activate [PATH_OR_NAME] --print` reads this metadata, uses the shared project target resolver, and prints activation guidance for the configured work directory. It remains read-only. `tw activate [PATH_OR_NAME]`, provided by the manually sourced `taurworks-shell.sh` helper, is the explicit shell-mutating layer that changes the current directory after validating Taurworks output.

## Dogfood workflows for init/create/activation guidance

Use `project create` when Taurworks should make a new project-root directory, then initialize metadata inside it. Add `--create-working-dir` only when Taurworks should also create a missing code/work directory:

```bash
cd ~/Workspace
taurworks project create TestProject --working-dir test_repo --create-working-dir
taurworks project activate TestProject --print
```

Expected shape:

```text
TestProject/
  .taurworks/
    config.toml
  test_repo/
```

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

Existing project commands use shared target-resolution internals where appropriate. State-changing scaffold commands preserve their documented create/refresh behavior, while read-only commands such as `working-dir show` and `activate --print` prefer resolving inside an existing Taurworks project root:

1. No input resolves the current project if present; otherwise the command may use its documented default.
2. Input equal to the current project name resolves to the current project root before accepting an accidental same-name relative child path. This fixes same-name activation from inside a project, such as `taurworks project activate TestProject --print`.
3. Input equal to the current working-directory basename, when the current directory is or should be the target, resolves to the current directory for init-like behavior.
4. Existing filesystem paths resolve as paths.
5. Otherwise, input is treated as a child path relative to the current working directory.

For read-only project commands, existing paths inside a Taurworks project are reported as the enclosing project root unless the command explicitly requires the exact path. State-changing scaffold commands keep path-only create/refresh target behavior.

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

Use `tw activate` when you explicitly want Taurworks to change the current shell directory. A standalone executable cannot change its parent shell directory, so this helper is implemented as a sourceable shell function:

```bash
source /path/to/taurworks-shell.sh
```

After it is sourced, `tw` behaves as follows:

- `tw activate [PATH_OR_NAME]` calls `taurworks project activate [PATH_OR_NAME] --print`, reads the stable `working_dir_configured`, `resolved_working_dir`, and `working_dir_exists` diagnostic fields, and runs only `cd -- "$resolved_working_dir"` in the current shell when the working directory is configured and exists.
- `tw project where`, `tw project list`, `tw project create ...`, and other non-activation invocations delegate directly to `taurworks ...`.
- failures print Taurworks diagnostics and do not change directory.

Basic dogfood workflow:

```bash
source /path/to/taurworks-shell.sh

cd ~/Workspace
taurworks project create TestProject --working-dir test_repo --create-working-dir
tw activate TestProject
pwd
```

Expected result:

```text
~/Workspace/TestProject/test_repo
```

The shell helper intentionally does not edit `.bashrc`, `.zshrc`, `.profile`, or any other shell startup file. It does not source arbitrary project files and does not activate Conda, virtualenv, or other environments. Bash is the primary supported shell for this first wrapper layer; the implementation uses portable shell-function features that are also expected to work when sourced by zsh.

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

- Immediate implementation of every planned `taurworks dev` command.
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
