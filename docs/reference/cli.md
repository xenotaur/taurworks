# Command reference

Every command provided by Taurworks. For task-oriented instructions, see the
[how-to guides](../README.md#how-to-guides).

Conventions used on this page:

- `[ARG]` is optional; `ARG` is required.
- **Writes** states what a command changes. "Nothing" means the command is
  read-only.
- `PATH_OR_NAME` accepts a path or a project name. Unless noted otherwise,
  names are looked up
  [globally](../explanation/concepts.md#how-a-project-name-is-resolved)
  (registry, then workspace root), and omitting the argument means the
  project containing the current directory.

## The three entry points

| Command | What it is | Provided by |
|---|---|---|
| `taurworks` | Python program | the installed package |
| `tw` | shell function wrapping `taurworks` | sourcing `taurworks-shell.sh` |
| `tl` | standalone shell function | sourcing `tl.source` |

## `tw`

`tw ARGS...` runs `taurworks ARGS...`, with these exceptions, which `tw`
handles itself:

| Command | Behavior |
|---|---|
| `tw activate [PATH_OR_NAME] [flags]` | Activates a project in the current shell. See below. |
| `tw shell refresh` | Regenerates the helper file and re-sources it. See below. |
| `tw help [COMMAND...]` | Same as `taurworks [COMMAND...] --help`. |

Before doing anything, `tw` checks that a `taurworks` executable is on `PATH`.
If not, it prints a diagnostic and returns 1.

### `tw activate [PATH_OR_NAME] [--verbose|--debug] [--legacy] [--no-legacy]`

Activates the resolved project in the current shell. With no argument,
activates the project containing the current directory.

Steps, in order; a failure stops the sequence and returns non-zero:

1. Resolve the project and validate its config (via
   `taurworks project activate --shell`).
2. `conda activate NAME`, if `[activation.environment]` is configured.
3. Export each `[activation.exports]` variable.
4. `cd` to the working directory, or the project root when none is
   configured.
5. Print `[activation].message`, if configured.
6. Handle a legacy `Admin/project-setup.source`, if present and legacy
   sourcing is enabled (see flags).

| Flag | Effect |
|---|---|
| `--verbose`, `--debug` | On failure, print the full diagnostic block instead of a summary. |
| `--legacy` | Source the legacy setup script for this activation. Requires legacy sourcing to be enabled. |
| `--no-legacy` | Do not source the legacy setup script, even if trusted. |
| `--` | End of flags; the next argument is the project. |

Legacy script handling when legacy sourcing is enabled and `--no-legacy` is
not given:

| Situation | Result |
|---|---|
| Script is trusted and unchanged | sourced |
| `--legacy` given | sourced |
| Untrusted or changed, interactive terminal | prompt: source once / trust and source / skip |
| Untrusted or changed, non-interactive | not sourced; a note is printed |

Exit status: 0 on success; 2 for an unexpected extra argument; otherwise
non-zero.

**Writes:** current shell's environment, Conda environment, and directory.
No files (except a trust record if you choose "trust" at the prompt).

### `tw shell refresh`

Runs `taurworks shell print`, replaces the helper file at its
[resolved location](configuration.md#file-locations) atomically, and sources
it in the current shell. If the location is a symlink, writes to the link's
target. Takes no arguments. Does not update `tl.source`.

**Writes:** the helper file; the current shell's `tw` function.

## `tl`

### `tl PROJECT_NAME`

Sources the first of these that exists, in the current shell:

1. `$TAURWORKS_WORKSPACE/PROJECT_NAME/Admin/project-setup.source`
2. `$TAURWORKS_WORKSPACE/PROJECT_NAME/.taurworks/project-setup.source`

`$TAURWORKS_WORKSPACE` defaults to `~/Workspace`. `tl` does not read Taurworks
config files or the registry and does not invoke `taurworks`.

Exit status: the sourced script's status; 1 if no script was found; 2 if not
given exactly one argument.

**Writes:** whatever the sourced script does.

## `taurworks`

### Global options

| Option | Effect |
|---|---|
| `-h`, `--help` | Show help. Works after any command or namespace. |
| `--debug` | Step-by-step narration for the top-level `create` and `refresh` commands. Must come before the command name. Also enabled by `TAURWORKS_DEBUG`. |

`taurworks help` is the same as `taurworks --help`, and
`taurworks help COMMAND...` the same as `taurworks COMMAND... --help`.

### Setup and shell integration

#### `taurworks setup`

Writes the `tw` helper (`taurworks-shell.sh`) and the `tl` source file
(`tl.source`) to their [resolved location](configuration.md#file-locations),
reports each as created, updated, or unchanged, and prints the `source` lines
to add to a shell startup file. Idempotent.

**Writes:** those two files. Never edits startup files.

#### `taurworks shell print`

Prints the packaged `tw` helper to stdout.

**Writes:** nothing.

### `taurworks config`

#### `taurworks config where`

Reports the resolved global config path, whether it exists, and which rule
selected it.

**Writes:** nothing.

#### `taurworks config legacy-sourcing show|enable|disable`

Shows or sets the global switch that permits `tw activate` to source legacy
setup scripts. Off by default. Enabling it does not by itself cause any
script to be sourced; that also requires `--legacy`, a prompt answer, or
per-project trust.

**Writes:** `enable`/`disable` set `[activation].legacy_sourcing` in the
global config. `show` writes nothing.

### `taurworks workspace`

#### `taurworks workspace show`

Reports the configured workspace root. If none is configured and
`~/Workspace` exists, reports it as `inferred`.

**Writes:** nothing.

#### `taurworks workspace set PATH`

Records `PATH` as the workspace root. `PATH` must be an existing directory.

**Writes:** `[workspace].root` in the global config, creating the config file
and its directory if needed.

### `taurworks project`

#### `taurworks project create [NAME] [--local | --path PATH] [--working-dir DIR] [--create-working-dir] [--env ENV] [--nested]`

Creates a project root if missing and initializes its metadata.

| Argument / option | Effect |
|---|---|
| `NAME` | Bare name: create `<workspace root>/NAME`. Requires a configured workspace root. A path-like value is used as the target path. Omitted: initialize the current directory (prefer `project init`). |
| `--local` | Create `NAME` under the current directory. |
| `--path PATH` | Create at `PATH`. Its last component must equal `NAME`. Mutually exclusive with `--local`. |
| `--working-dir DIR` | Record `DIR` (relative to the project root) as the working directory. |
| `--create-working-dir` | Also create `DIR` if missing. Requires `--working-dir`. |
| `--env ENV` | Record `ENV` as the Conda environment to activate. Does not create it. |
| `--nested` | Permit creating `NAME` inside a project or directory already named `NAME`. |

**Writes:** the project root directory, `.taurworks/config.toml`, and the
working directory when requested. Does not register the project.

#### `taurworks project init [PATH] [--working-dir DIR] [--create-working-dir] [--env ENV]`

Initializes an existing directory (default: the current directory) as a
project root. Fails if the directory does not exist. Idempotent; existing
`working_dir` and environment settings are kept unless the corresponding
option is given. `DIR` must exist unless `--create-working-dir` is given.

**Writes:** `.taurworks/config.toml`; the working directory when requested.

#### `taurworks project refresh [PATH]`

Creates missing project metadata and repairs an empty project name or missing
schema version. Default target: the current directory. The argument is
treated as a path relative to the current directory, not a global name.

**Writes:** `.taurworks/config.toml`. **Creates the target directory if it
does not exist.**

#### `taurworks project activate [PATH_OR_NAME] --print | --shell`

Describes activation for the resolved project. Exactly one of the two options
is required.

| Option | Output |
|---|---|
| `--print` | Human-readable diagnostics. Export values are hidden. |
| `--shell` | Shell variable assignments consumed by `tw activate`. Not a stable interface for other use. |

**Writes:** nothing. Does not change the shell.

#### `taurworks project root PROJECT` / `taurworks project working PROJECT`

Prints one absolute path to stdout: the project root, or the working
directory (the project root if none is configured). On failure prints nothing
to stdout, diagnostics to stderr, and exits 1.

Also available as `taurworks root PROJECT` and `taurworks working PROJECT`.

**Writes:** nothing.

#### `taurworks project working-dir show [PATH]`

Shows the working-directory setting for the current project, or for the
project containing `PATH`. The argument may also be the current project's own
name; other names are not looked up globally.

**Writes:** nothing.

#### `taurworks project working-dir set [DIR]`

Sets the working directory of the project containing the current directory.
`DIR` is resolved from the current directory, must exist, must be inside the
project root, and is stored relative to it. Default: the current directory.

**Writes:** `[paths].working_dir` in the project config.

#### `taurworks project env show [PATH_OR_NAME]`

Shows the project's configured activation environment.

**Writes:** nothing.

#### `taurworks project env set ENV_NAME [--project PATH_OR_NAME]`

Records `ENV_NAME` as the project's Conda environment, replacing any existing
value. Does not create or check for the environment.

**Writes:** `[activation.environment]` in the project config.

#### `taurworks project register NAME PATH [--force] [--allow-missing]`

Adds a registry entry. `PATH` is made absolute. It must be an existing
directory unless `--allow-missing` is given. A duplicate `NAME` is an error
unless `--force` is given. A path with no `.taurworks/config.toml` is
accepted with a warning.

**Writes:** `[projects.NAME].root` in the global config.

#### `taurworks project unregister NAME`

Removes a registry entry.

**Writes:** the global config. Deletes no project files.

#### `taurworks project registry list`

Lists registry entries, with whether each path and its project config exist
and whether the name also matches a workspace directory.

**Writes:** nothing.

#### `taurworks project list`

Lists discoverable projects (workspace root children plus registry entries)
with status, in diagnostic format.

**Writes:** nothing.

#### `taurworks project where`

Reports which project the current directory belongs to and how that was
determined. Exits 1 if the lookup is ambiguous.

**Writes:** nothing.

#### `taurworks project trust set [PATH_OR_NAME]`

Records the current SHA-256 digest of the project's
`Admin/project-setup.source` as trusted, replacing any existing record.

**Writes:** `[trust.NAME]` in the global config.

#### `taurworks project trust unset [PATH_OR_NAME]`

Removes the project's trust record. Exits 1 if there was none.

**Writes:** the global config.

#### `taurworks project trust list`

Lists trust records, with whether each script still exists and still matches
its recorded digest.

**Writes:** nothing.

### `taurworks legacy`

#### `taurworks legacy inspect [PROJECT]`

Reads the project's `Admin/project-setup.source` and classifies each line as
a supported pattern (`conda activate`, `export`, `cd`, `echo`/`printf`) or
unsupported. Export values are redacted. Never executes the script.

**Writes:** nothing.

#### `taurworks legacy migrate [PROJECT] [--apply]`

Proposes project config fields for the supported patterns found by `inspect`.
Without `--apply` this is a dry run. Existing config values are never
overwritten. The legacy script is not modified or removed.

**Writes:** with `--apply`, the project's `.taurworks/config.toml`.

### `taurworks dev`

#### `taurworks dev where` / `taurworks dev status`

Report the detected project root, working directory, and the directory in
which dev commands would run (`work_directory_guess`). `status` is a shorter
summary. Neither runs `git`.

**Writes:** nothing.

#### `taurworks dev clean|test|smoke|lint|format|build`

Runs the project's own command for that verb. Resolution:

1. `[dev.commands].<verb>` in the project root's `.taurworks/config.toml`,
   split into arguments and run without a shell.
2. Otherwise `scripts/<verb>` in the work directory.

The command runs in the work directory. Its output streams through and its
exit status is returned. If neither source provides the verb, or the config
entry is malformed, an error is printed and the exit status is 1. No extra
arguments are accepted.

**Writes:** whatever the delegated command does.

### Top-level project commands

These predate the `project` namespace and remain for compatibility.

#### `taurworks projects [-l | --details]`

Lists projects: immediate subdirectories of the workspace root plus registry
entries, each with a status (`initialized`, `workspace-only`, `legacy-admin`)
and source. `--details` adds paths, config and working-directory state, a
file count and total size (computed by walking each project's directory tree
recursively), and whether a Conda environment with the same name as the
project exists (which runs `conda`). That check does not consult
`[activation.environment]`, so a project configured with a differently named
environment is reported as `missing`.

**Writes:** nothing.

#### `taurworks activate PROJECT_NAME`

Prints the `tw activate` command to run. Activates nothing.

**Writes:** nothing.

#### `taurworks create PROJECT_NAME [--create-env] [--python VER] [--packages LIST] [--file YAML]`

Creates `PROJECT_NAME/` with `.taurworks/config.toml` and a working directory
also named `PROJECT_NAME`, and records a Conda environment named
`PROJECT_NAME`. Fails if the project directory already exists.

Unlike `taurworks project create`, the location is
`$TAURWORKS_WORKSPACE` (default `~/Workspace`); the workspace root set by
`taurworks workspace set` is not consulted.

| Option | Effect |
|---|---|
| `--create-env` | Create the Conda environment. Without it, no environment is created, and `tw activate` will fail until one with that name exists. |
| `--python VER` | Python version for the new environment. Default `3.11`. |
| `--packages LIST` | Comma-separated extra packages to install into it. |
| `--file YAML` | Create the environment from a Conda environment file. |

**Writes:** project directories and config; with `--create-env`, a Conda
environment.

#### `taurworks refresh PROJECT_NAME [--create-env] [--python VER] [--packages LIST] [--file YAML]`

Ensures the same layout as `taurworks create` exists for `PROJECT_NAME`,
creating whatever is missing (the working directory is named in snake case,
for example `my_project` for `MyProject`). Existing config values are not
overwritten. Options and location as for `taurworks create`.

**Writes:** as `taurworks create`.

For new work, prefer `taurworks project create` and `taurworks project init`.
