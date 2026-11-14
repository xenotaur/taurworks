# Install, update, and uninstall Taurworks

Taurworks is not published to PyPI. Every install starts from a local checkout
of the repository.

## Install (recommended)

From the checkout:

```bash
scripts/install
```

This runs `pipx install . --force` and then `taurworks setup`. It works from
any current directory, because the script locates the checkout from its own
path.

Then add the two `source` lines that `taurworks setup` prints to your shell
startup file (`~/.bashrc` or `~/.zshrc`). Taurworks never edits startup files
itself.

Requirements: Python 3.11+, pipx, and pipx's app directory (default
`~/.local/bin`) on your `PATH`.

### Why pipx

pipx puts `taurworks` in its own isolated environment with a launcher in
`~/.local/bin`. The command then stays on `PATH` whichever Conda environment
is active. Installing with plain `pip` puts `taurworks` inside one
environment only, and it disappears — `taurworks: command not found` — as soon
as you activate a different one.

## Install the shell helpers only

If `taurworks` is already installed some other way, write the helpers with:

```bash
taurworks setup
```

`taurworks setup` is idempotent. It writes two files, reports each as
`created`, `updated`, or `unchanged`, and prints the `source` lines:

| File | Provides |
|---|---|
| `taurworks-shell.sh` | the `tw` shell function |
| `tl.source` | the `tl` break-glass function |

Both go in the same directory. See
[file locations](../reference/configuration.md#file-locations) for how that
directory is chosen.

## Install the `tw` helper by hand

To put the helper somewhere you control without running `taurworks setup`:

```bash
mkdir -p ~/.config/taurworks
```

```bash
taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
```

```bash
source ~/.config/taurworks/taurworks-shell.sh
```

`taurworks shell print` only prints the `tw` helper. To get `tl` as well, run
`taurworks setup`, or source it straight from a checkout — see
[Use `tl`](use-tl-fallback.md#get-tl-without-taurworks-setup).

## Keep the helper in a custom location

Set `TAURWORKS_SHELL_HELPER_PATH` in your startup file, before running
`taurworks setup`, so that both `taurworks setup` and `tw shell refresh` use
that location every time:

```bash
export TAURWORKS_SHELL_HELPER_PATH=~/dotfiles/taurworks-shell.sh
```

`tl.source` is written next to it. If the path is a symlink (for example into
a dotfiles checkout), `tw shell refresh` writes through to the link's target
and leaves the link in place.

## Update

1. Update your checkout (`git pull`).
2. Reinstall:

   ```bash
   scripts/install
   ```

3. In **each shell that is already open**, reload the `tw` function:

   ```bash
   tw shell refresh
   ```

Step 3 matters. The helper file is a snapshot, and a shell reads it once when
it is sourced, exactly like `.bashrc`. `scripts/install` updates the file on
disk, but shells that are already open keep running the old `tw` function,
silently, until you refresh them or open a new shell.

`tw shell refresh` regenerates the helper file from the installed package and
re-sources it in the current shell. It cannot reach other open shells; run it
in each one, or just open new ones.

If `tw shell refresh` reports an unknown command, your loaded `tw` is older
than that feature. Reload it once by hand:

```bash
source ~/.config/taurworks/taurworks-shell.sh
```

`tw shell refresh` does not update `tl.source`. `scripts/install` and
`taurworks setup` do; `tl` changes rarely by design.

## Install for developing Taurworks itself

For code changes to take effect without reinstalling, use an editable install:

```bash
pipx install --editable <path-to-checkout>
```

```bash
taurworks setup
```

An editable install depends on the checkout staying where it is. The
non-editable install from `scripts/install` is a self-contained snapshot and
does not. For the contributor toolchain (formatter, linter, tests), see the
[development guide](../development.md).

## Uninstall

```bash
pipx uninstall taurworks
```

Then remove the two `source` lines from your startup file. Optionally delete
the helper files and the global config
(`~/.config/taurworks/` by default). Project directories and their
`.taurworks/` metadata are not touched by any of this.
