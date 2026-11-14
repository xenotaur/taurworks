# Use `tl`, the break-glass fallback

`tl` ("Taurworks Legacy") activates a project by sourcing a shell script that
lives in the project. It is the emergency route for when `tw activate` cannot
be used.

```bash
tl ProjectName
```

## When to use it

Use `tw activate` normally. Reach for `tl` when:

- **`taurworks` has vanished from `PATH`** — typically after `conda activate`
  into an environment that does not have it. `tw` prints
  ``tw: `taurworks` is not on $PATH`` and stops; `tl` still works.
- **Your loaded `tw` is stale or broken** and you do not want to stop and
  repair it mid-task.
- **The project has only a legacy setup script** and you have not migrated it
  yet.

`tl` works in these situations because it is a few lines of pure shell. It
never runs the `taurworks` program and never calls `tw`.

## What it does

`tl NAME` looks for a setup script in two places, in order, and sources the
first one it finds into your current shell:

1. `<workspace>/NAME/Admin/project-setup.source`
2. `<workspace>/NAME/.taurworks/project-setup.source`

```text
tl: sourcing /home/you/Workspace/Alpha/Admin/project-setup.source
```

That is all. Whatever the script contains — `conda activate`, `export`, `cd` —
runs in your shell exactly as if you had typed `source <that file>`.

If neither file exists, `tl` prints both paths it checked and returns 1.

## How `tl` differs from `tw activate`

| | `tw activate NAME` | `tl NAME` |
|---|---|---|
| Needs the `taurworks` program | yes | no |
| Driven by | `.taurworks/config.toml` | a `project-setup.source` shell script |
| Workspace location | global config, then `$TAURWORKS_WORKSPACE`, then `~/Workspace` | `$TAURWORKS_WORKSPACE`, else `~/Workspace` |
| Finds registered projects | yes | no |
| Accepts paths, flags | yes | no — exactly one project name |
| Runs arbitrary project shell code | only with explicit trust | always |

Two consequences to be aware of:

- **`tl` does not read Taurworks' config.** If your workspace root is set with
  `taurworks workspace set` to something other than `~/Workspace`, also
  `export TAURWORKS_WORKSPACE=/that/path` in your startup file, or `tl` will
  look in the wrong place. Projects that are only in the registry are
  invisible to `tl`.
- **`tl` runs the script without asking.** Only use it on projects whose setup
  script you trust.

## Make a project work with `tl`

`tl` needs a setup script. A project created with `taurworks project create`
does not have one, so `tl` reports `no setup script found` for it until you
add one. If you want `tl` available as a fallback for a project, write
`.taurworks/project-setup.source` that reproduces its activation by hand:

```bash
# ~/Workspace/Alpha/.taurworks/project-setup.source
conda activate alpha
export NODE_OPTIONS="--max-old-space-size=8192"
cd ~/Workspace/Alpha/repo
echo "Ready for work on Alpha"
```

Use the `.taurworks/` location rather than `Admin/`: `tw activate` only reacts
to a script at `Admin/project-setup.source`, so a script under `.taurworks/`
serves `tl` without `tw activate` warning about it or offering to source it.

Keep this script in step with `config.toml` yourself; nothing does it for you.

## Get `tl` without `taurworks setup`

`taurworks setup` writes `tl.source` next to the `tw` helper and prints the
`source` line for it. If you cannot run `taurworks` at all, source the
packaged file directly from a checkout:

```bash
source <path-to-checkout>/src/taurworks/resources/sourceme/aliases.source
```

## Why `tl` has no features

`tl` deliberately has no flags, no listing, no completion, and no awareness of
`tw`. A fallback is only useful if it keeps working when the main tool does
not, and every feature would be another thing that could break. If `tl` seems
to need a feature, the fix belongs in `tw`. `tl` is permanent; it is not being
phased out.
