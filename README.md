# taurworks

Taurworks is a command-line development framework for creating, switching to, and working in multiple development projects.

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

Status note: `taurworks project ...` now includes implemented discovery, scaffold, working-directory metadata, and read-only guidance commands (`where`, `list`, `refresh`, `create`, `working-dir show`, `working-dir set`, and `activate --print`). `taurworks dev ...` remains planned and is not implemented yet.
Implementation note: `taurworks project where`, `taurworks project list`, `taurworks project refresh`, and `taurworks project create` share consolidated internals for project resolution, discovery, and safe `.taurworks/` scaffolding behavior.
Design note: dogfooding showed that Taurworks must distinguish `project_root` (the directory containing `.taurworks/`) from `working_dir` (the default code/work directory, stored relative to `project_root`) before shell activation can be useful. This slice implements the metadata commands; later work will update `taurworks project activate --print` guidance to use configured `working_dir`. Full `taurworks dev ...`, automatic shell mutation, and multi-repo management remain out of scope.

The namespaced model is the active design direction. The currently shipped CLI remains compatibility-first and continues to support top-level lifecycle commands such as:

- `taurworks create`
- `taurworks refresh`
- `taurworks activate`
- `taurworks projects`

The scaffolded `project` namespace currently includes implemented discovery and safe scaffold commands:

- `taurworks project where` (implemented, read-only diagnostics)
- `taurworks project list` (implemented, read-only discovery listing)
- `taurworks project refresh [PATH_OR_NAME]` (implemented, safe idempotent metadata scaffolding repair)
- `taurworks project working-dir show` (implemented, project working-directory metadata display)
- `taurworks project working-dir set [DIR]` (implemented, safe project working-directory metadata update)
- `taurworks project create [PATH_OR_NAME] [--working-dir DIR]` (implemented, safe idempotent create wrapper around refresh with optional working-directory metadata)
- `taurworks project activate [PATH_OR_NAME] --print` (implemented, read-only activation guidance output)

Quick namespace help:

```bash
taurworks project --help
```

`taurworks project where` intentionally does not mutate files, environments, or shell state.
`taurworks project list` is also non-mutating and reports discoverable projects plus discovery limitations.

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

Use these commands from inside a Taurworks project:

```bash
taurworks project working-dir show
taurworks project working-dir set [DIR]
```

Behavior:

- `show` prints the configured relative working directory or a clear unconfigured message.
- `set DIR` resolves `DIR` from the current directory, requires it to be an existing directory inside `project_root`, and stores it relative to `project_root`.
- `set` with no `DIR` stores the current directory relative to `project_root`.
- absolute working-directory paths are rejected until a later design explicitly accepts them.
- paths that escape `project_root` via `..` are rejected.

Actual activation behavior will be updated in a later PR. Shell mutation through `tw activate` or a shell wrapper remains a later slice.

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

## `taurworks project create`

Use this command to ensure a target directory exists and then delegate to refresh:

```bash
taurworks project create [PATH_OR_NAME]
taurworks project create PROJECT --working-dir DIR
```

Behavior:

- with no argument, creates/refreshes in the current working directory
- with an argument, treats it as a path (or path-like name) rooted in the current directory when not already existing
- creates the target project root directory when missing
- delegates scaffolding work to `taurworks project refresh` instead of duplicating refresh/scaffold logic
- writes new configs with `[project].name` defaulting to the project-root directory name unless existing config metadata already provides a non-empty name
- when `--working-dir DIR` is omitted, does not invent `[paths].working_dir` metadata
- when `--working-dir DIR` is provided, validates that `DIR` is relative, resolves safely inside `project_root`, and stores it as a relative `paths.working_dir` value
- rejects absolute working-directory paths and paths that escape `project_root`
- records the working-directory metadata only; it does not create `DIR`, and the summary reports whether that directory currently exists
- never overwrites unrelated files or deletes files
- prints a summary including the project root, whether the root was created, refresh delegation details, configured working directory, and created/skipped/warning items

This command is intentionally safe and idempotent: after first successful scaffolding, repeated runs behave like refresh, preserve existing unrelated files, and keep the same relative `working_dir` metadata.

## `taurworks project activate --print`

Use this command to resolve a project and print activation guidance only:

```bash
taurworks project activate [PATH_OR_NAME] --print
```

Behavior:

- with no argument, resolves from the current working directory
- with an argument, resolves the path/name using the same shared project-resolution internals as other `project` lifecycle commands
- prints read-only activation diagnostics and (when available) a manual command hint
- does not source scripts
- does not activate conda/virtualenv
- does not change your parent shell state
- does not write, refresh, create, or delete project files

This slice is intentionally non-mutating. Actual shell mutation will require an explicit shell wrapper/function in a later slice. Inspect printed output before running any command manually.

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

For Python package and CLI development, install Taurworks in editable mode from the repository root:

```bash
python -m pip install -e .
```

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
./scripts/format
./scripts/lint
./scripts/test
./scripts/smoke
```

These same commands are used by GitHub Actions in `.github/workflows/python-ci.yml`.
