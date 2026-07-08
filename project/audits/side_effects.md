# Taurworks side-effect safety audit

Prompt: `PROMPT(TAURWORKS_POST_MERGE_SIDE_EFFECT_SAFETY_AUDIT)[AUDIT/2026-05-17]`

Date: 2026-05-17

Scope: non-destructive post-merge audit of Taurworks command side effects after
declarative activation and Conda activation support. This document inventories
current behavior only; it does not change command behavior.

## Safety baseline

The intended policy for follow-up work is:

- `taurworks project activate --print` remains read-only activation guidance.
- `tw activate` is the explicit sourced shell-mutating helper; it may activate a
  configured environment, export configured variables, and change directory.
- `project create`, `project init`, and `project refresh` may create or repair
  Taurworks metadata and directories only when that behavior is explicit.
- Conda environment creation should require an explicit environment command or
  explicit flag.
- Conda environment activation should be explicit and normally happen only
  through sourced `tw activate`.
- User/project script sourcing should require explicit opt-in/trust
  configuration and should not happen by default.

## Side-effect taxonomy

| Category | Meaning |
| --- | --- |
| `READ_ONLY` | Prints or returns information only. |
| `GLOBAL_CONFIG_WRITE` | Writes the user-global Taurworks config. |
| `PROJECT_METADATA_WRITE` | Writes `.taurworks` metadata such as `.taurworks/config.toml`. |
| `FILESYSTEM_CREATE` | Creates project, working, metadata, or helper directories/files. |
| `FILESYSTEM_DELETE` | Deletes files or directories. |
| `SUBPROCESS_READ_ONLY` | Runs subprocesses expected not to mutate state. |
| `SUBPROCESS_MUTATING` | Runs subprocesses that may mutate state. |
| `ENVIRONMENT_CREATE` | Creates Conda, venv, or similar environments. |
| `ENVIRONMENT_ACTIVATE` | Activates Conda, venv, or similar environments. |
| `SHELL_MUTATION` | Mutates the current shell with `cd`, `export`, activation, or `eval`. |
| `SCRIPT_EXECUTION` | Sources or runs user/project scripts or broad shell commands. |

## Executive findings

1. The legacy top-level commands `taurworks create NAME`, `taurworks refresh NAME`,
   and shell-helper delegation such as `tw refresh NAME` still call the legacy
   `manager.refresh_project` path, which creates project directories, creates a
   Conda environment by default, creates a repository directory, and writes a
   `.taurworks/project-setup.source` file.
2. The newer `taurworks project refresh [PATH_OR_NAME]` path is metadata-only
   scaffolding/repair and does not call Conda.
3. Conda activation is implemented only in the sourced `tw activate` helper.
   `taurworks project activate --print` and `--shell` print data for inspection
   or helper consumption and do not activate Conda themselves.
4. Declarative activation exports are parsed and validated in Python, shell-quoted
   for the helper, and applied only by sourced `tw activate`.
5. Legacy `Admin/project-setup.source` is detected for classification/guidance but
   is not sourced by current Python CLI activation paths.
6. No `conda init`, `os.system`, or Python `shell=True` subprocess path was found
   in current source. The shell helper uses `eval` on Taurworks-generated shell
   assignments and generated export commands.

## Command-by-command inventory

### `taurworks config where`

Implementation: `src/taurworks/cli.py`, `src/taurworks/global_config.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Resolves and prints the XDG-style config path and does not create the config
  file.

Recommendation:

- Keep read-only.

### `taurworks workspace show`

Implementation: `src/taurworks/cli.py`, `src/taurworks/global_config.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Reads global config when present and may infer `~/Workspace` when no config
  exists; no writes are performed.

Recommendation:

- Keep read-only.

### `taurworks workspace set PATH`

Implementation: `src/taurworks/cli.py`, `src/taurworks/global_config.py`

Side effects observed:

- `GLOBAL_CONFIG_WRITE`
- `FILESYSTEM_CREATE` for the config parent directory when needed

Assessment:

- Command name is explicit about setting config. It writes the user-global config
  and creates the parent XDG config directory if needed.

Recommendation:

- Keep behavior, and continue documenting that this command writes global config
  but does not create the workspace directory itself.

### `taurworks project where`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Uses filesystem checks to discover a nearby `.taurworks` directory and prints
  diagnostics. It does not write config or metadata.

Recommendation:

- Keep read-only.

### `taurworks project list` / `taurworks projects`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`,
`src/taurworks/manager.py`

Side effects observed:

- `READ_ONLY`
- `SUBPROCESS_READ_ONLY` for legacy `taurworks projects --details` only

Assessment:

- Namespaced `taurworks project list` lists configured workspace children and
  registered project entries. It reads config and inspects directories but does
  not write files or run scripts. Legacy `taurworks projects --details` also
  calls `conda env list` to display whether similarly named Conda environments
  exist.

Recommendation:

- Keep read-only. Consider documenting or removing the Conda probe from legacy
  detailed listing if it is too surprising or slow.

### `taurworks project register NAME PATH`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_registry.py`,
`src/taurworks/global_config.py`

Side effects observed:

- `GLOBAL_CONFIG_WRITE`
- `FILESYSTEM_CREATE` for the config parent directory when needed

Assessment:

- Command name explicitly indicates registration. It writes `[projects.NAME]` in
  global config and does not create project-local metadata.

Recommendation:

- Keep behavior; continue requiring `--allow-missing` for missing paths.

### `taurworks project unregister NAME`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_registry.py`,
`src/taurworks/global_config.py`

Side effects observed:

- `GLOBAL_CONFIG_WRITE`

Assessment:

- Removes only the global registry entry. It does not delete project files.

Recommendation:

- Keep behavior.

### `taurworks project registry list`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_registry.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Reads global registry entries and performs path checks only.

Recommendation:

- Keep read-only.

### `taurworks project refresh [PATH_OR_NAME]`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`,
`src/taurworks/project_internals.py`

Side effects observed:

- `PROJECT_METADATA_WRITE`
- `FILESYSTEM_CREATE` for `.taurworks/` when missing

Assessment:

- New namespaced refresh delegates to `scaffold_project_metadata` and repairs
  Taurworks metadata. It does not call `conda create`, `conda env create`,
  `conda activate`, or legacy setup scripts.

Recommendation:

- Keep metadata-only by default.
- Clarify top-level `taurworks refresh` and `tw refresh` as legacy behavior until
  they are migrated or deprecated.

### `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir]`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`,
`src/taurworks/project_internals.py`

Side effects observed:

- `PROJECT_METADATA_WRITE`
- `FILESYSTEM_CREATE` for `.taurworks/`
- `FILESYSTEM_CREATE` for `--create-working-dir` only

Assessment:

- Initializes an existing project root. Missing working directories are recorded
  without being created unless `--create-working-dir` is supplied.

Recommendation:

- Keep working-directory creation behind the explicit flag.

### `taurworks project create NAME [--local|--path PATH] [--working-dir DIR] [--create-working-dir]`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`,
`src/taurworks/project_internals.py`

Side effects observed:

- `FILESYSTEM_CREATE` for project root
- `PROJECT_METADATA_WRITE`
- `FILESYSTEM_CREATE` for `.taurworks/`
- `FILESYSTEM_CREATE` for `--create-working-dir` only

Assessment:

- Namespaced create explicitly creates a project root and metadata. It does not
  create Conda environments.

Recommendation:

- Keep environment creation out of this command unless a future explicit flag is
  added and named clearly.

### `taurworks project working-dir show [PATH_OR_NAME]`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Resolves and prints working-directory metadata only.

Recommendation:

- Keep read-only.

### `taurworks project working-dir set DIR`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`,
`src/taurworks/project_internals.py`

Side effects observed:

- `PROJECT_METADATA_WRITE`

Assessment:

- Records a relative working directory in `.taurworks/config.toml`. It does not
  create missing directories.

Recommendation:

- Keep behavior; if creation is later added, require an explicit flag matching
  `project init/create --create-working-dir`.

### `taurworks project activate [PATH_OR_NAME] --print`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Reads activation config, validates export names and Conda environment names,
  hides export values in normal output, and prints that environment activation
  and shell mutation were not performed.

Recommendation:

- Keep read-only.

### `taurworks project activate [PATH_OR_NAME] --shell`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`

Side effects observed:

- `READ_ONLY` when run directly, because it only prints shell assignment data

Assessment:

- Intended for consumption by `tw activate`. It prints shell-quoted assignment
  data, including a quoted multi-line export-command payload. Running it directly
  does not mutate the parent shell.

Recommendation:

- Keep internal/helper-facing status clear in documentation. Consider warning in
  help text that export values are present in `--shell` output because the helper
  needs them.

### `taurworks shell print`

Implementation: `src/taurworks/cli.py`, `src/taurworks/shell_resources.py`,
`src/taurworks/resources/shell/taurworks-shell.sh`

Side effects observed:

- `READ_ONLY`

Assessment:

- Prints the packaged sourceable helper only. It does not install, source, or
  edit shell startup files.

Recommendation:

- Keep print-only.

### `tw activate [PATH_OR_NAME]`

Implementation: `src/taurworks/resources/shell/taurworks-shell.sh`, with data
from `taurworks project activate --shell`

Side effects observed:

- `SUBPROCESS_READ_ONLY` for calling `taurworks project activate --shell`
- `ENVIRONMENT_ACTIVATE` when `[activation.environment]` is configured with
  `type = "conda"`
- `SHELL_MUTATION` via `conda activate`, `export`, and `cd`

Assessment:

- This is the explicit shell-mutating layer. It checks that `conda` is available,
  runs `conda activate "$environment_name"` only for configured Conda
  activation, evaluates Taurworks-generated shell assignments, evaluates
  Taurworks-generated export commands, and changes directory to the resolved
  working directory.

Recommendation:

- Keep shell mutation limited to this sourced helper.
- Consider reducing `eval` surface in a follow-up if a portable safer shell data
  format is adopted.

### `tw help ...` and other `tw ...` commands

Implementation: `src/taurworks/resources/shell/taurworks-shell.sh`

Side effects observed:

- Delegates to the matching `taurworks ...` command

Assessment:

- The helper only special-cases `activate` and `help`. Therefore `tw refresh NAME`
  delegates to the legacy top-level `taurworks refresh NAME`, not the newer
  `taurworks project refresh [PATH_OR_NAME]`.

Recommendation:

- Add explicit `tw refresh` policy: either map it to metadata-only
  `taurworks project refresh` or deprecate/rename the legacy top-level command.

### Legacy top-level `taurworks create NAME`

Implementation: `src/taurworks/cli.py`, `src/taurworks/manager.py`

Side effects observed:

- `FILESYSTEM_CREATE`
- `PROJECT_METADATA_WRITE`
- `SUBPROCESS_READ_ONLY` via `conda env list`
- `SUBPROCESS_MUTATING`
- `ENVIRONMENT_CREATE`

Assessment:

- Delegates to `manager.create_project`. It can create a Conda environment with
  `conda create --name NAME python=3.11 -y` by default, or `conda env create
  --name NAME --file FILE` when `--file` is supplied. It also writes
  `.taurworks/project-setup.source`.

Recommendation:

- Move environment creation behind an explicit environment command or explicit
  flag.
- Prefer the namespaced `taurworks project create` path for project metadata.

### Legacy top-level `taurworks refresh NAME`

Implementation: `src/taurworks/cli.py`, `src/taurworks/manager.py`

Side effects observed:

- `FILESYSTEM_CREATE`
- `PROJECT_METADATA_WRITE`
- `SUBPROCESS_READ_ONLY` via `conda env list`
- `SUBPROCESS_MUTATING`
- `ENVIRONMENT_CREATE`

Assessment:

- This is the most surprising finding. The command name sounds idempotent/safe,
  but the legacy implementation creates the workspace/project/repository
  directories, creates a Conda environment if absent, and writes a sourceable
  setup script.

Recommendation:

- Make refresh metadata-only by default.
- Move Conda creation to an explicit environment command or explicit flag.
- Consider a compatibility warning or deprecation path for the legacy top-level
  command.

### Legacy top-level `taurworks activate NAME`

Implementation: `src/taurworks/cli.py`, `src/taurworks/manager.py`

Side effects observed:

- `READ_ONLY` from the Python process perspective

Assessment:

- Prints `source .../.taurworks/project-setup.source` guidance when the legacy
  setup script exists. It does not source the script and cannot mutate the parent
  shell.

Recommendation:

- Prefer `taurworks project activate --print` and `tw activate` in docs. Consider
  deprecating legacy activation guidance that points to generated setup scripts.

### `taurworks root PROJECT` / `taurworks working PROJECT`

Implementation: `src/taurworks/cli.py`, `src/taurworks/project_resolution.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Prints resolved paths for shell composition. It does not mutate the shell or
  filesystem.

Recommendation:

- Keep read-only.

### `taurworks dev where` / `taurworks dev status`

Implementation: `src/taurworks/cli.py`, `src/taurworks/dev.py`

Side effects observed:

- `READ_ONLY`

Assessment:

- Performs Python filesystem/config inspection only. No workflow tools or git
  subprocesses are run.

Recommendation:

- Keep read-only until future dev automation commands are named and gated
  explicitly.

## Required audit answers

### Conda creation

1. Commands that can call `conda create`:
   - `taurworks refresh NAME` through `manager.refresh_project` and
     `manager.create_conda_environment`.
   - `taurworks create NAME` through `manager.create_project`.
   - `tw refresh NAME` and `tw create NAME` because the helper delegates unknown
     commands to `taurworks ...`.
2. Commands that can create or update Conda environments:
   - The same legacy top-level create/refresh paths can create environments.
   - With `--file`, they call `conda env create`; otherwise they call
     `conda create`.
   - No command was found that updates an existing Conda environment in place.
3. `taurworks project refresh` does not create Conda environments, but legacy
   `taurworks refresh` and therefore `tw refresh` can still create Conda
   environments by default.
4. Yes. Legacy `refresh` sounds safe/idempotent but can create a Conda
   environment.
5. The legacy CLI exposes `--python`, `--packages`, and `--file`, but environment
   creation is not explicit because it happens by default when the environment is
   missing.

### Conda activation

1. Commands that can call `conda activate`:
   - `tw activate [PATH_OR_NAME]` through the sourced shell helper when the
     activation config has `[activation.environment] type = "conda"`.
   - Generated legacy `.taurworks/project-setup.source` files contain
     `conda activate NAME`, but Taurworks does not source them itself.
2. Conda activation in current Taurworks execution is limited to the sourced
   `tw activate` helper.
3. `taurworks project activate --print` remains read-only and prints
   `environment_activation: not performed` and `shell_mutation: not performed`.
4. No Python CLI path can mutate the parent shell. Python activation paths print
   guidance or shell data only.
5. No `conda init` call was found.

### Environment variables

1. Commands that export environment variables:
   - Only sourced `tw activate` applies configured exports.
   - `taurworks project activate --shell` prints export commands for helper
     consumption but does not export into the parent shell.
2. Exports are limited to the explicit shell-mutating helper layer in normal use.
3. Export variable names are validated against a conservative shell variable
   pattern before output.
4. Export values are shell-quoted with `shlex.quote` before being placed in the
   helper payload.
5. Normal `--print` output hides export values. `--shell` necessarily includes
   export values for the helper and should be treated as machine-readable shell
   data rather than normal user-facing diagnostics.

### Scripts and shell commands

1. Taurworks detects legacy `Admin/project-setup.source` for classification and
   activation guidance, but current source does not source it.
2. No current code was found that sources `.taurworks/activate.source` or another
   user script by default.
3. Current Taurworks code does not run arbitrary user shell scripts by default.
   Legacy refresh writes a `.taurworks/project-setup.source` file, and legacy
   activate prints a command for the user to source it manually.
4. Python subprocess calls are narrow and explicit: `conda env list`,
   `conda create`, and `conda env create` in legacy manager code. Legacy
   `taurworks projects --details` also uses `conda env list` as a read-only
   environment existence probe.
5. No Python `shell=True`, `os.system`, or broad Python `eval` pattern was found.
   The sourced shell helper uses `eval` for Taurworks-generated shell assignment
   data and export commands.

### Filesystem and config mutation

1. Commands that write global config:
   - `taurworks workspace set PATH`
   - `taurworks project register NAME PATH`
   - `taurworks project unregister NAME`
2. Commands that write project-local `.taurworks/config.toml`:
   - `taurworks project refresh [PATH_OR_NAME]`
   - `taurworks project init [PATH] ...`
   - `taurworks project create NAME ...`
   - `taurworks project working-dir set DIR`
   - Legacy top-level create/refresh write legacy `.taurworks/project-setup.source`
     and create `.taurworks/`; they do not use the current TOML metadata writer
     for `.taurworks/config.toml`.
3. Commands that create directories:
   - `taurworks workspace set PATH`, `project register`, and `project unregister`
     may create the XDG config parent directory while writing global config.
   - `taurworks project refresh`, `project init`, and `project create` create
     `.taurworks/` metadata directories as appropriate.
   - `taurworks project create` creates the project root.
   - `taurworks project init/create --create-working-dir` creates the requested
     working directory.
   - Legacy top-level create/refresh create workspace, project, metadata, and
     repository directories.
4. No current source path was found that deletes files/directories as part of a
   Taurworks command. The audit helper scans for deletion patterns so future
   changes are easier to spot.
5. Most mutations are consistent with command names/flags. The main exception is
   legacy top-level `refresh` and `tw refresh`, where Conda creation and setup
   script creation are surprising.

## Follow-up recommendations

1. Migrate or deprecate legacy top-level `taurworks refresh` so refresh is
   metadata-only by default.
   **Status: partially addressed by `WI-LEGACY-CONDA-GATING-0001`.** Conda
   environment creation is now gated behind an explicit `--create-env` flag
   (see recommendation #2), but legacy `refresh`/`create` still create the
   workspace/project/repository directories and write
   `.taurworks/project-setup.source` unchanged. Making legacy `refresh`/`create`
   fully metadata-only (this recommendation in full) is a larger,
   compatibility-sensitive change left as potential future work — see that work
   item's Open Questions.
2. Move Conda creation behind an explicit command such as `taurworks env create`
   or an explicit flag such as `--create-env`; do not create environments from a
   read-only-looking or repair-looking command.
   **Status: resolved by `WI-LEGACY-CONDA-GATING-0001`.** Legacy top-level
   `taurworks create NAME` / `taurworks refresh NAME` (and therefore `tw create`
   / `tw refresh`) now require an explicit `--create-env` flag before calling
   `conda create` or `conda env create`; the default path no longer creates a
   Conda environment.
3. Keep Conda activation limited to `tw activate` or another explicitly sourced
   shell-mutating helper.
   **Status: already satisfied.** Per the command-by-command inventory above,
   Conda activation in current Taurworks execution is limited to sourced
   `tw activate`; no other path was found to call `conda activate`.
4. Do not source `Admin/project-setup.source`, `.taurworks/activate.source`, or
   other user scripts by default. If script hooks are added later, require an
   explicit trust/opt-in model.
   **Status: already satisfied; trusted-hooks model is future work.** No
   current code sources these scripts by default. Designing an explicit
   trust/opt-in model for user-script hooks is out of scope for
   `WI-LEGACY-CONDA-GATING-0001` (see that item's Non-Goals) and is tracked
   under `WI-ACTIVATION-CONFIG-0001` slice 6.
5. Treat `taurworks project activate --shell` output as sensitive when activation
   exports include secrets; normal `--print` output should continue hiding values.
   **Status: already satisfied by current behavior.** `--print` output hides
   export values and `--shell` output is documented above as machine-readable
   data intended for helper consumption rather than normal diagnostics.
6. Reduce shell `eval` surface in `tw activate` if a future portable assignment
   protocol can avoid it without making the helper brittle.
   **Status: reviewed by `WI-LEGACY-CONDA-GATING-0001`; decision is to keep
   as-is.** Both `eval` calls in `taurworks-shell.sh` operate only on
   Taurworks-generated data: one reads structured `KEY=value` shell assignments
   produced by `taurworks project activate --shell`, and the other runs export
   commands whose variable names are validated against a conservative pattern
   and whose values are `shlex.quote`-escaped before being emitted (see the
   "Environment variables" answers above). Replacing `eval` with a safer parser
   would be a larger change to the activation data protocol, and this work
   item's Risk Notes flag it as risking breakage of Conda/export activation if
   not carefully retested. Deferred as potential future work rather than
   attempted here.
7. Add CI or developer checks around side-effect-sensitive patterns if command
   behavior expands.
   **Status: partially satisfied.** `scripts/audit-side-effects` (see "Audit
   helper" below) already exists as a best-effort, non-destructive scanner;
   wiring it into CI as an enforced gate remains open.

## Audit helper

`scripts/audit-side-effects` is a best-effort, non-destructive scanner for
side-effect-sensitive implementation patterns. It is not a policy gate or a full
static analyzer; it is intended to speed up future reviews by showing locations
that mention subprocess calls, Conda commands, shell mutation, config writes, and
filesystem deletion/creation patterns.
