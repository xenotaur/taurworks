# Troubleshooting

Find the message or symptom you are seeing.

## `tw: command not found`

The `tw` shell function is not loaded in this shell.

- Not set up yet: run `taurworks setup` and add the printed `source` lines to
  your startup file. See [Install](install-and-update.md).
- Set up, but this shell did not read the startup file: source the helper
  directly.

  ```bash
  source ~/.config/taurworks/taurworks-shell.sh
  ```

`tw` is a shell function, not a program. It exists only in shells that have
sourced the helper, and it is not visible to scripts unless they source it
too.

## ``tw: `taurworks` is not on $PATH``

`tw` is loaded, but the `taurworks` program it calls cannot be found. Almost
always this follows `conda activate` into an environment where Taurworks is
not installed, because Taurworks was installed with `pip` into a different
environment.

- **Right now:** use [`tl ProjectName`](use-tl-fallback.md), or switch back to
  the environment that has Taurworks.
- **Permanently:** install with pipx so the command survives environment
  switches.

  ```bash
  scripts/install
  ```

  Then confirm `~/.local/bin` (pipx's app directory) is on your `PATH`.

## `taurworks: command not found`

Same cause as above, without the `tw` helper loaded to explain it. Check
`pipx list` and that pipx's app directory is on `PATH`.

## `tw` behaves like an old version after updating

Each open shell keeps the `tw` function it loaded when it started. Reload it:

```bash
tw shell refresh
```

If that subcommand is not recognized, the loaded `tw` predates it. Re-source
the helper file once, or open a new shell.

## `tw activate: activation failed for NAME`

The second line gives the reason. For the full picture:

```bash
tw activate NAME --verbose
```

Common reasons:

- **"Project name was not found..."** — `NAME` is not a registered project,
  not a directory directly under your workspace root, and not the current
  project. Check `tw projects` and `taurworks workspace show`. Names are
  case-sensitive. For a project elsewhere, give a path or
  [register it](manage-projects.md#register-a-project-that-lives-elsewhere).
- **Working directory does not exist** — the configured `working_dir` is
  missing on disk. Create it, or change it with
  `taurworks project working-dir set DIR`.

## `tw activate: conda activation is unavailable in this shell`

The project configures a Conda environment, but this shell has no `conda`
command or function. Initialize Conda for your shell (`conda init`, then a new
shell). Taurworks does not do this for you.

## `tw activate: failed to activate Conda environment: NAME`

Conda is available but `conda activate NAME` failed — usually the environment
does not exist. Check `conda env list`. Either create the environment or fix
the name:

```bash
taurworks project env set CORRECT_NAME --project PROJECT
```

Nothing was exported and your directory was not changed.

## `tw activate` only changed directory

Look for a warning line in the output:

- **Project is not initialized** — no `.taurworks/config.toml`. Run
  `taurworks project init PATH --working-dir DIR`.
- **Legacy `Admin/project-setup.source` exists but was not sourced** — see
  [Migrate a legacy project](migrate-legacy-projects.md).
- Only a `note:` about no Conda environment — the project simply has no
  environment, exports, or message configured. See [Set what activation does](activate-projects.md#set-what-activation-does).

## `tw activate: --legacy requires legacy sourcing to be enabled`

`--legacy` does nothing until the global switch is on:

```bash
taurworks config legacy-sourcing enable
```

## `tl: no setup script found for project 'NAME'`

`tl` prints the two paths it checked. Either:

- the project has no `project-setup.source` script — projects made with
  `taurworks project create` do not, see
  [Make a project work with `tl`](use-tl-fallback.md#make-a-project-work-with-tl); or
- `tl` is looking in the wrong workspace. `tl` uses `$TAURWORKS_WORKSPACE` or
  `~/Workspace` and ignores `taurworks workspace set`. Export
  `TAURWORKS_WORKSPACE` to match.

## `tl: command not found`

`tl.source` is not sourced. `taurworks setup` prints the line to add. The
`tw` helper and `tl` are separate files with separate `source` lines.

## A project is missing from `tw projects`

`tw projects` lists immediate subdirectories of the workspace root, plus
registered projects. It does not search deeper. For a project nested further
down or outside the workspace:

```bash
taurworks project register NAME /path/to/project
```

Also confirm the workspace root is what you expect:
`taurworks workspace show`.

## `project create NAME` says no workspace root is configured

`taurworks project create NAME` requires an explicitly configured workspace
root, even when `~/Workspace` exists and is shown as `inferred`:

```bash
taurworks workspace set ~/Workspace
```

Or use `--local` to create under the current directory.

## `taurworks dev test`: no delegation target found

The project provides neither a `[dev.commands].test` entry nor a
`scripts/test` file where Taurworks looked. The message names both locations.
See [Run dev commands](run-dev-commands.md). If the locations are not the
ones you expected, check `taurworks dev where`.

## A command picked up the wrong project

```bash
taurworks project where
```

shows which project the current directory belongs to and how it was found.
If `resolved_by` in `taurworks dev where` is `working_dir_reverse_lookup`,
the match came from a symlinked working directory; see
[Symlinked working directories](../explanation/concepts.md#symlinked-working-directories).
If Taurworks reports the lookup is ambiguous, two projects' working
directories both contain the current directory; narrow one of them.

## Step-by-step output from `create` / `refresh`

The top-level `taurworks create` and `taurworks refresh` commands print only
their result by default. For narration of each step:

```bash
taurworks --debug create NAME
```

or set `TAURWORKS_DEBUG=1`. This is unrelated to `tw activate --debug`.
