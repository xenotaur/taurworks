# Concepts

This page explains the ideas behind Taurworks: why there are three commands,
what a project is, how a name becomes a directory, and what Taurworks will
and will not do without being asked.

## Three layers: `taurworks`, `tw`, and `tl`

A program cannot change the shell that launched it. When `taurworks` runs, it
is a child process; it can print things and write files, but when it exits,
your shell is in the same directory, with the same variables and the same
Conda environment, as before. Activating a project means changing exactly
those things, so something has to run *inside* your shell. That is the reason
for the layers.

**`taurworks`** is the Python program. It holds all the logic: reading
config, resolving names, validating settings. With respect to your shell it
is read-only. Asked about activation, it can only describe what should
happen (`taurworks project activate NAME --print`).

**`tw`** is a shell function, defined by a helper file you source. For almost
every command it simply passes its arguments to `taurworks`, so `tw projects`
and `taurworks projects` are the same thing. The exception is `tw activate`:
it asks `taurworks` for the activation plan in a machine-readable form, then
carries the plan out in your shell — `conda activate`, `export`, `cd`. `tw`
decides nothing itself; it executes what the Python side has validated.

**`tl`** is a second, much smaller shell function with no connection to the
other two. It finds a setup script in a project and sources it. It exists
because the first two layers have a shared weak point: `tw` depends on being
able to run `taurworks`, and `taurworks` can disappear from `PATH` when you
switch Conda environments, or the `tw` function loaded in a long-lived shell
can be out of date. `tl` depends on neither, so it still works when they do
not. It is kept deliberately featureless so that it stays that reliable.

In normal use you type `tw`. `taurworks` is what you would call from a script
that does not source the helper. `tl` is for when something is wrong.

### Why the helper goes stale

The `tw` helper is a file generated from the installed package, and a shell
reads it once, when it is sourced. Updating Taurworks changes the package,
and reinstalling rewrites the file, but nothing can reach into shells that
are already running and redefine their `tw` function. `tw shell refresh`
regenerates the file and re-sources it in the shell where you run it. Other
open shells stay on the old version until they do the same or are restarted.

## Projects, roots, and working directories

A **project** is a directory that contains `.taurworks/config.toml`. That
directory is the **project root**.

The **working directory** is where you actually want your shell to be when
working on the project — usually a source checkout inside the project root.
It is recorded in the project config as a path relative to the root:

```text
~/Workspace/Alpha/          <- project root
  .taurworks/config.toml    <- [paths] working_dir = "alpha"
  alpha/                    <- working directory (a git checkout)
  notes/
  data/
```

Keeping the two apart lets a project hold more than one thing — a checkout,
notes, datasets, scratch space — while `tw activate` still drops you into the
code. A project whose root *is* the checkout sets `working_dir = "."`.

The path is stored relative so that a project can be moved or synced to
another machine without editing its config.

### Symlinked working directories

`working_dir` must be a relative path with no `..`, but a component may be a
symlink that points outside the project root. This supports keeping the
project's metadata in one place and its checkout on, say, a faster local
disk.

When you are inside such an external directory, there is no `.taurworks/`
above you for Taurworks to find. So as a second step it checks whether the
current directory lies inside the resolved working directory of any known
project, and if exactly one matches, uses it. If two match, it refuses to
guess.

Because that match is by containment, the link should point at the project's
own work tree. A `working_dir` linked to a broad directory such as `$HOME`
claims every directory beneath it that has no `.taurworks/` of its own:
`taurworks dev test` run in some unrelated checkout there would use that
project's `[dev.commands]`. (One exception: an unrelated checkout that is a
linked `git worktree` nested under the link still runs in the worktree.)

## The workspace root and the registry

Taurworks finds projects by name in two places.

The **workspace root** is one directory whose immediate children are
projects. Anything directly inside it is discoverable with no further setup.
Discovery is intentionally shallow: Taurworks does not walk the tree looking
for projects, which keeps lookups fast and predictable.

The **registry** is an explicit list, in your global config, of `name → path`
entries for projects that live anywhere else. It is how a project nested
several levels down, or on another volume, gets a name.

### How a project name is resolved

For `tw activate NAME` and the other name-aware commands, the first match
wins:

1. A registry entry named `NAME`.
2. An initialized project `NAME` directly under the workspace root.
3. A legacy project `NAME` (one with `Admin/project-setup.source`) directly
   under the workspace root.
4. Any other directory `NAME` directly under the workspace root.
5. The project containing the current directory, when no name is given or
   the name is that project's own.

Anything that looks like a path — `./Alpha`, `/abs/path`, a name containing a
slash — skips all of that and is resolved as a path.

Two properties follow. Activation by name gives the same answer from any
directory. And a bare name never silently matches some subdirectory of
wherever you happen to be; if it is not in the list above, activation fails
and says so.

The registry comes first so that you can deliberately override a
workspace directory of the same name.

Not every command is name-aware in this sense. Commands that create or
repair things (`project init`, `project refresh`, `project create` with a
path) treat their argument as a path, because guessing wrong would write
files in the wrong place.

## Project states

`tw projects` labels each entry:

- **initialized** — has `.taurworks/config.toml`.
- **legacy-admin** — has no Taurworks config but does have the older
  `Admin/project-setup.source` script.
- **workspace-only** — a directory in the workspace root with neither.

All three can be activated; what differs is how much happens. Only an
initialized project gets its environment, exports, and message. For the other
two, `tw activate` changes into the directory and tells you what is missing.

## Declarative activation, and legacy scripts

Activation is described by data, not code. A project's config can name a
Conda environment, a set of literal environment variables, a working
directory, and a message. Taurworks validates each (variable names, the
environment name, that the directory exists and stays inside the project)
before `tw` acts on any of it.

The earlier design had each project carry a shell script,
`Admin/project-setup.source`, that was sourced on activation. That is as
flexible as it gets, and it also means activating a project runs whatever
that file says. Declarative config trades away the flexibility for something
you can inspect, validate, and preview.

Legacy scripts are still supported, at arm's length:

- `taurworks legacy inspect` and `legacy migrate` read a script and translate
  the simple, literal parts into config. They never execute it.
- `tw activate` will source a legacy script only after two separate opt-ins:
  a global switch, and then consent for that script. Consent is either
  one-time — `--legacy`, or answering "source once" at the prompt, which
  runs the script for that activation and records nothing — or persistent
  per-project **trust**. Trust records the script's SHA-256 digest in your
  global config. Because the record lives outside the project, nothing
  arriving in a project directory can grant itself trust; because it is tied
  to content, an edited script must be reviewed and trusted again.
- `tl` sources a setup script unconditionally. That is its entire job, and
  why it is described as a break-glass tool rather than the normal path.

## The safety model

Taurworks is conservative about side effects, and tries to make a command's
name an honest signal of its risk.

- **It never edits shell startup files.** `taurworks setup` writes its own
  helper files and prints `source` lines; adding them is up to you.
- **Only sourced functions change your shell.** The `taurworks` program
  cannot; `tw activate`, `tw shell refresh`, and `tl` are the only things
  that do, and each only when invoked.
- **Reading is separated from writing.** Diagnostic commands (`where`,
  `show`, `list`, `--print`, `inspect`, a `migrate` dry run) change nothing
  and say so in their output. Commands that write say what they created,
  updated, and skipped.
- **Nothing is created implicitly.** A missing working directory is an error
  unless you pass `--create-working-dir`. A Conda environment is never
  created unless you pass `--create-env` to the legacy `create` command.
  Activation never creates directories or environments.
- **Existing content is preserved.** Metadata commands add missing pieces and
  do not overwrite your files; `legacy migrate` does not overwrite config
  values that are already set; `unregister` removes a registry entry and no
  files.
- **Project code is not run without consent.** See the previous section.
- **Exported values are not echoed.** Diagnostics show export names and
  counts, never values.

The project's full side-effect audit is in
[`project/audits/side_effects.md`](../../project/audits/side_effects.md).

## What Taurworks does not do

- Create or manage Conda environments as part of activation.
- Activate virtualenvs, containers, or anything other than Conda.
- Run arbitrary per-project hooks declared in config.
- Manage Git: `taurworks dev status` does not run `git`.
- Implement build, test, or lint logic. `taurworks dev` delegates to your
  project's own commands.

Planned directions are tracked in
[`project/roadmap/roadmap.md`](../../project/roadmap/roadmap.md).
