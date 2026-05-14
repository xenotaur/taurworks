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

Status note: `taurworks project ...` now includes implemented discovery, scaffold, working-directory metadata, and read-only guidance commands (`where`, `list`, `refresh`, `create`, `working-dir show`, `working-dir set`, and `activate --print`). `taurworks dev ...` remains planned and is not implemented yet.
Implementation note: `taurworks project where`, `taurworks project list`, `taurworks project refresh`, and `taurworks project create` share consolidated internals for project resolution, discovery, and safe `.taurworks/` scaffolding behavior.
Design note: dogfooding confirmed the `project_root` (the directory containing `.taurworks/`) and `working_dir` (the default code/work directory, stored relative to `project_root`) model, but showed that the lifecycle semantics need refinement. The accepted design separates `project init` for existing/current roots from `project create` for new roots, centralizes target resolution diagnostics, makes working-directory creation explicit, and prevents accidental nested same-name projects. This sequence should be completed before adding `tw activate` or any shell wrapper that mutates the user shell. Full `taurworks dev ...`, automatic shell mutation, and multi-repo management remain out of scope.

The namespaced model is the active design direction. The currently shipped CLI remains compatibility-first and continues to support top-level lifecycle commands such as:

- `taurworks create`
- `taurworks refresh`
- `taurworks activate`
- `taurworks projects`

The scaffolded `project` namespace currently includes implemented discovery and safe scaffold commands:

- `taurworks project where` (implemented, read-only diagnostics)
- `taurworks project list` (implemented, read-only discovery listing)
- `taurworks project refresh [PATH_OR_NAME]` (implemented, safe idempotent metadata scaffolding repair)
- `taurworks project working-dir show` (implemented, project working-directory metadata display; target-aware `show [PATH_OR_NAME]` is planned)
- `taurworks project working-dir set [DIR]` (implemented, safe project working-directory metadata update; `set DIR --project PATH_OR_NAME` is the preferred planned target-aware shape)
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

Current implemented commands can be used from inside a Taurworks project:

```bash
taurworks project working-dir show
taurworks project working-dir set [DIR]
```

Accepted dogfood-resolution design:

- `taurworks project working-dir show [PATH_OR_NAME]` should accept an optional target and print the configured relative working directory or a clear unconfigured message.
- `taurworks project working-dir set DIR --project PATH_OR_NAME` is preferred over ambiguous positional overloads for target-aware mutation. A no-target form may continue to mean the current project.
- Working-directory paths remain relative to `project_root`; absolute paths and paths that escape `project_root` via `..` are rejected/deferred until a later design explicitly accepts them.
- Missing working directories are created only with explicit opt-in, such as `taurworks project create NAME --working-dir repo --create-working-dir` or `taurworks project working-dir set repo --create`.

`taurworks project activate [PATH_OR_NAME] --print` reads this metadata and prints activation guidance for the configured work directory. It should remain read-only and use the shared project target resolver. Shell mutation through `tw activate` or a shell wrapper remains a later slice.

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

## Shared project target resolution

Project lifecycle, working-directory, and read-only activation commands should use one shared resolver:

1. No input resolves the current project if present; otherwise the command may use its documented default.
2. Existing filesystem paths resolve as paths.
3. Input equal to the current project name resolves to the current project root.
4. Input equal to the current working-directory basename, when the current directory is or should be the target, resolves to the current directory for init-like behavior.
5. Otherwise, input is treated as a child path relative to the current working directory.

Outputs should make this choice inspectable, for example:

```text
- input: TestProject
- project_root: /path/to/TestProject
- resolved_by: current_project_name
```

## `taurworks project init` and `taurworks project create`

Accepted design distinguishes initialization from creation:

```bash
taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]
taurworks project create NAME [--working-dir DIR] [--create-working-dir] [--nested]
```

Behavior:

- `project init` initializes an existing/current project root; it is safe, idempotent, and should reuse refresh/config logic.
- `project create` creates a new project root directory, then delegates to init/refresh logic.
- `project create NAME` refuses accidental nested same-name creation when the current project or current directory already has the requested name unless `--nested` is supplied.
- when `--working-dir DIR` is omitted, commands do not invent `[paths].working_dir` metadata.
- when `--working-dir DIR` is provided, commands validate that `DIR` is relative, resolves safely inside `project_root`, and stores it as a relative `paths.working_dir` value.
- missing working directories are created only when explicitly requested with `--create-working-dir`.
- absolute working-directory paths and paths that escape `project_root` are rejected/deferred until later explicit design.
- commands never overwrite unrelated files or delete files.
- summaries should include resolver diagnostics such as `input`, `project_root`, and `resolved_by`, plus whether roots or working directories were created.

This design addresses dogfood findings where same-name input from inside a project could resolve to an unintended child path and where missing working-directory creation behavior was inconsistent.

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

This slice is intentionally non-mutating. Actual shell mutation through `tw activate` or another explicit shell wrapper/function remains a later slice. Inspect printed output before running any command manually.

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
