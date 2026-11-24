# Run clean/test/lint/build with `taurworks dev`

`taurworks dev` gives every project the same six verbs, whatever tooling sits
behind them:

```bash
tw dev test
```

The six are `clean`, `test`, `smoke`, `lint`, `format`, and `build`.

Taurworks contains no build, lint, or test logic of its own. Each verb
*delegates* to something your project provides.

## Provide a command

There are two ways. Taurworks checks them in this order.

### Option 1: configure it

In the project's `.taurworks/config.toml`:

```toml
[dev.commands]
test = "pytest -x"
lint = "ruff check src"
```

The string is split into arguments and run directly, not through a shell, so
pipes, `&&`, redirection, and variable expansion do not work. For anything
that needs a shell, put it in a script and use option 2, or point the entry at
the script.

### Option 2: add a script

Create an executable file named after the verb in a `scripts/` directory in
your working directory:

```text
repo/
  scripts/
    test
    lint
```

Then `tw dev test` runs `scripts/test`.

## Where it runs

The command always runs with its current directory set to the project's work
directory, whichever subdirectory you invoked it from. `[dev.commands]` is
read from the project root's `.taurworks/config.toml`; `scripts/<verb>` is
looked up in the work directory.

To see exactly which directory that is:

```bash
tw dev where
```

Look at `work_directory_guess`. It is, in order of preference: the checkout
you are in if that is a linked `git worktree` inside the configured working
directory; the configured working directory; the nearest Git root; the
project root; the current directory.

## Results and failures

- Output streams live, and the command's exit code becomes the exit code of
  `taurworks dev <verb>`, so it composes in scripts and CI.
- If neither option provides the verb, Taurworks names both places it looked
  and exits non-zero. It never silently does nothing.
- A malformed `[dev.commands]` entry is an error; Taurworks does not fall back
  to `scripts/` and run something you did not intend.

## Extra arguments

`taurworks dev <verb>` does not accept extra arguments to pass through. Put
arguments in the `[dev.commands]` entry or in the script.

## Diagnostics

| Command | Shows |
|---|---|
| `taurworks dev where` | detected project root, working directory, and the directory commands will run in |
| `taurworks dev status` | a shorter summary of the same |

Both are read-only and do not run `git`.
