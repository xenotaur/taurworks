# Configuration reference

Taurworks reads two TOML config files — one per user, one per project — and a
handful of environment variables.

## File locations

| File | Location | Created by |
|---|---|---|
| Global config | `<config dir>/taurworks/config.toml` | `workspace set`, `project register`, `config legacy-sourcing`, `project trust set` |
| `tw` helper | `<helper dir>/taurworks-shell.sh` | `taurworks setup`, `tw shell refresh` |
| `tl` source file | `<helper dir>/tl.source` | `taurworks setup` |
| Project config | `<project root>/.taurworks/config.toml` | `project create`, `project init`, `project refresh` |
| Legacy setup script | `<project root>/Admin/project-setup.source` | you |
| `tl`-only setup script | `<project root>/.taurworks/project-setup.source` | you |

**`<config dir>`** is `$XDG_CONFIG_HOME` when that is set to an absolute path,
otherwise `~/.config`. A relative `XDG_CONFIG_HOME` is ignored.

**`<helper dir>`** is resolved in this order:

1. If `TAURWORKS_SHELL_HELPER_PATH` is set, the helper is written to exactly
   that file (a relative value is taken relative to the current directory; a
   leading `~` stored in the variable is not expanded), and `tl.source` goes
   in the same directory.
2. Otherwise `<config dir>/taurworks/`.

`taurworks setup` and `tw shell refresh` use the same rules, so they always
agree on the file.

Check the resolved global config path with `taurworks config where`.

## Global config

One per user. Normally you change it through commands rather than by hand.

```toml
schema_version = 1

[workspace]
root = "/home/you/Workspace"

[projects.HiddenProject]
root = "/data/experiments/HiddenProject"

[activation]
legacy_sourcing = false

[trust.OldProject]
path = "/home/you/Workspace/OldProject/Admin/project-setup.source"
digest = "31a4ed8d..."
```

| Key | Type | Meaning | Set with |
|---|---|---|---|
| `schema_version` | integer | Config format version. Must be `1`. | written automatically |
| `[workspace].root` | string, absolute path | The workspace root. | `taurworks workspace set PATH` |
| `[projects.NAME].root` | string, absolute path | Registry entry: project `NAME` lives at this path. | `taurworks project register` / `unregister` |
| `[activation].legacy_sourcing` | boolean | Whether `tw activate` may ever source a legacy setup script. Default `false`. | `taurworks config legacy-sourcing enable` / `disable` |
| `[trust.NAME].path` | string | Path of a trusted legacy setup script. | `taurworks project trust set` / `unset` |
| `[trust.NAME].digest` | string | SHA-256 digest of the trusted content. | as above |

Commands that write this file preserve the other content in it.

## Project config

One per project, at `.taurworks/config.toml` in the project root.

```toml
schema_version = 1

[project]
name = "Alpha"

[paths]
working_dir = "repo"

[activation]
message = "Ready for work on Alpha"

[activation.environment]
type = "conda"
name = "alpha"

[activation.exports]
NODE_OPTIONS = "--max-old-space-size=8192"
ALPHA_MODE = "development"

[dev.commands]
test = "pytest -x"
lint = "ruff check src"
```

### `schema_version`

Integer. Must be `1`. Written automatically; a missing value is repaired by
`project refresh` / `project init`. Commands that write the project config
refuse a different integer version and leave the file unchanged. Commands
that only read it — activation, `taurworks dev` — do not check the version.

### `[project]`

| Key | Type | Meaning |
|---|---|---|
| `name` | string | The project's name. Defaults to the project root's directory name. |

### `[paths]`

| Key | Type | Meaning |
|---|---|---|
| `working_dir` | string | Default working directory, relative to the project root. Optional. |

Rules for `working_dir`:

- Must be relative. Absolute paths are rejected.
- Must not contain `..`.
- `"."` means the project root itself.
- A component may be a symlink to a directory outside the project root. A
  dangling or looping symlink is rejected.
- When unset, activation uses the project root and prints a warning.
- When set but missing on disk, activation fails.

Set with `taurworks project working-dir set`, or `--working-dir` on
`project create` / `project init`.

### `[activation]`

| Key | Type | Meaning |
|---|---|---|
| `message` | string | Printed by `tw activate` after a successful activation. Optional. |

### `[activation.environment]`

Optional. When present, `tw activate` runs `conda activate <name>` first.

| Key | Type | Meaning |
|---|---|---|
| `type` | string | Must be `"conda"`. No other type is supported. |
| `name` | string | Conda environment name. Required. Must start with a letter or digit and contain only letters, digits, `_`, `.`, and `-`. |

Set with `taurworks project env set`, or `--env` on `project create` /
`project init`. Taurworks records the name only; it does not check that the
environment exists.

### `[activation.exports]`

Optional. Each entry is exported into the shell by `tw activate`, after Conda
activation and before the directory change.

- **Names** must match `[A-Za-z_][A-Za-z0-9_]*`.
- **Values** must be strings.
- Values are exported literally. No `~`, variable, or command expansion is
  performed.
- Values are never shown in diagnostic output.

An invalid name or a non-string value fails activation before anything is
exported.

### `[dev.commands]`

Optional. Maps a `taurworks dev` verb to a command line.

| Key | Type |
|---|---|
| `clean`, `test`, `smoke`, `lint`, `format`, `build` | string |

The string is split into arguments using shell quoting rules and executed
directly, without a shell: quoting works; pipes, redirection, `&&`, and
variable expansion do not. Always read from the project root's config, and
run in the project's work directory.

### Hand-editing

You can edit a project config by hand, but two things happen when a
Taurworks command later rewrites it (`project env set`, `project
working-dir set`, `project init`, `legacy migrate --apply`, and so on):

- **Comments and formatting are not preserved.** The file is regenerated
  from its parsed contents, so `#` comments and custom layout are dropped.
- **Only string, integer, and boolean values can be rewritten**, in plain
  keys or tables. If the file contains any other value type — an array, a
  float, a date — the command fails with `unsupported config value type for
  safe writer` and leaves the file unchanged, rather than risk rewriting it
  incorrectly. Remove or re-express the value, or make the change by hand.

Reading is unaffected: activation and `taurworks dev` parse the file as
ordinary TOML.

## Environment variables

### Read by Taurworks

| Variable | Used by | Meaning |
|---|---|---|
| `XDG_CONFIG_HOME` | `taurworks`, `tw shell refresh` | Base directory for the global config and helper files, when absolute. Default `~/.config`. |
| `TAURWORKS_SHELL_HELPER_PATH` | `taurworks setup`, `tw shell refresh` | Exact file path for the `tw` helper. Export it in your startup file so both commands always see it. |
| `TAURWORKS_WORKSPACE` | see below | A workspace directory. Default `~/Workspace`. |
| `TAURWORKS_DEBUG` | top-level `taurworks create` / `refresh` | Enables step narration. Any value other than empty, `0`, `false`, or `no` (case-insensitive) is true. `--debug` takes precedence. |
| `CONDA_DEFAULT_ENV` | `tw` | Only read to make the "`taurworks` is not on `$PATH`" diagnostic more specific. |

### Which workspace does a command use?

There are two sources — the configured root in the global config, and
`TAURWORKS_WORKSPACE` — and commands differ in which they consult.

| Command | Workspace used |
|---|---|
| `tw activate NAME`, `tw projects`, `project list`, `tw root`/`working`, other name lookups | configured root; else `$TAURWORKS_WORKSPACE`; else `~/Workspace` |
| `taurworks project create NAME` | configured root only; otherwise an error |
| `taurworks workspace show` | configured root; else, only when the global config file does not exist, reports an existing `~/Workspace` as `inferred`; otherwise `none` |
| top-level `taurworks create` / `refresh` | `$TAURWORKS_WORKSPACE`; else `~/Workspace` |
| `tl NAME` | `$TAURWORKS_WORKSPACE`; else `~/Workspace` |

To keep everything consistent when your workspace is not `~/Workspace`, do
both:

```bash
taurworks workspace set /path/to/workspace
```

```bash
export TAURWORKS_WORKSPACE=/path/to/workspace
```

with the `export` in your shell startup file.

### Set by Taurworks

`tw activate` exports the variables listed in the project's
`[activation.exports]`, and nothing else. Variables set by a previous
activation are not unset when you activate a different project.
