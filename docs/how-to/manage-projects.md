# Create, initialize, and register projects

A Taurworks project is a directory containing `.taurworks/config.toml`. This
guide covers the ways to get one, and how to make it findable by name.

All commands here can be run as `taurworks ...` or `tw ...`.

## Set the workspace root

The workspace root is the directory whose immediate subdirectories are your
projects. Set it once:

```bash
taurworks workspace set ~/Workspace
```

The directory must already exist. Check the current value with
`taurworks workspace show`.

## Create a new project

```bash
taurworks project create NAME --working-dir repo --create-working-dir
```

This creates `<workspace root>/NAME`, its `.taurworks/config.toml`, and the
`repo` working directory, regardless of your current directory.

| To create... | Use |
|---|---|
| under the workspace root (default) | `taurworks project create NAME` |
| under the current directory | `taurworks project create NAME --local` |
| at an exact path | `taurworks project create NAME --path /some/where/NAME` |
| and record a Conda environment | add `--env ENV_NAME` |

Notes:

- With `--path`, the last component of the path must equal `NAME`.
- Without `--create-working-dir`, `--working-dir` records the name but does
  not create the directory; activation will fail until it exists.
- `--working-dir` is always relative to the project root. Absolute paths and
  `..` are rejected.
- `--env` only records the environment name. It does not create a Conda
  environment.
- If no workspace root is configured, a bare `project create NAME` fails and
  asks you to set one or use `--local`.
- A project created outside the workspace root (`--local`, `--path`) is not
  findable by name until you [register it](#register-a-project-that-lives-elsewhere).

## Turn an existing directory into a project

If the directory already exists — a checkout you have been working in, say —
use `init` instead of `create`:

```bash
cd ~/Workspace/Existing
```

```bash
taurworks project init --working-dir repo
```

Or name the directory without changing into it:

```bash
taurworks project init ~/Workspace/Existing --working-dir repo
```

`init` only adds `.taurworks/` metadata; your files are not touched. It is
safe to re-run. `--working-dir` must already exist unless you add
`--create-working-dir`. If the directory *is* the place you work, use
`--working-dir .`.

`init` refuses a directory that does not exist; that is what `create` is for.

## Register a project that lives elsewhere

Projects directly under the workspace root are found automatically. For a
project anywhere else — another disk, a nested path — add it to the registry:

```bash
taurworks project register NAME /path/to/project
```

Now `tw activate NAME` works from anywhere.

| Task | Command |
|---|---|
| See registered projects | `taurworks project registry list` |
| Remove an entry | `taurworks project unregister NAME` |
| Replace an existing entry | `taurworks project register NAME PATH --force` |
| Register a path that does not exist yet | add `--allow-missing` |

Unregistering removes only the registry entry. It never deletes project files.

If a registered name is the same as a directory under the workspace root, the
registry entry wins.

## List projects

```bash
tw projects
```

```text
Available projects:

- Demo         initialized     workspace
- OldThing     legacy-admin    workspace
- Scratch      workspace-only  workspace
```

| Status | Meaning |
|---|---|
| `initialized` | Has `.taurworks/config.toml`. |
| `workspace-only` | A directory in the workspace with no Taurworks config. `tw activate` only changes into it. Fix with `taurworks project init`. |
| `legacy-admin` | Has an old `Admin/project-setup.source` script and no Taurworks config. See [Migrate a legacy project](migrate-legacy-projects.md). |

Use `tw projects --details` for paths, config presence, and working
directory. Two things to know about the detailed listing:

- Its `Conda Env Exists` line checks for an environment with the same name
  as the *project*, not the environment the project is configured to
  activate. A project whose environment has a different name shows
  `missing` even when activation works. Use `taurworks project env show
  NAME` for the configured environment.
- It counts files and total size by walking each project's whole directory
  tree, so it can be slow on large projects.

## Change the working directory

From inside the project:

```bash
taurworks project working-dir set other_repo
```

The directory must exist and be inside the project root. With no argument, the
current directory is used. Check the result with
`taurworks project working-dir show`.

`working-dir set` always acts on the project containing the current
directory. `working-dir show` also accepts a path; unlike `tw activate`, it
does not look names up in the workspace or registry, so from outside the
project give a path (`taurworks project working-dir show ~/Workspace/Demo`).

### Working directories outside the project root

The stored `working_dir` is always a relative path, but a component of it may
be a symlink to a directory elsewhere — useful when the code lives on a
different disk:

```bash
ln -s /fast-disk/alpha-checkout ~/Workspace/Alpha/repo
```

```bash
taurworks project init ~/Workspace/Alpha --working-dir repo
```

Commands run from inside `/fast-disk/alpha-checkout` still find the `Alpha`
project. Link to the project's own work tree, not to a broad directory such
as `$HOME` — see
[the caution in Concepts](../explanation/concepts.md#symlinked-working-directories).

## Change or inspect the Conda environment

```bash
taurworks project env set ENV_NAME --project PATH_OR_NAME
```

```bash
taurworks project env show PATH_OR_NAME
```

Omit `--project` / the argument to act on the project containing the current
directory.

## Repair project metadata

```bash
taurworks project refresh PATH
```

`refresh` creates a missing `.taurworks/config.toml` and repairs an empty
project name or missing schema version. It never overwrites other files, and
reports exactly what it found, created, and skipped.

> **`project refresh` creates the target directory if it does not exist.**
> Check the path before running it. To add metadata to a directory you
> already have, prefer `taurworks project init`, which refuses a missing
> directory.

## Diagnose what Taurworks sees

| Question | Command |
|---|---|
| Which project am I in? | `taurworks project where` |
| Where is the global config? | `taurworks config where` |
| What would activation do? | `taurworks project activate NAME --print` |
