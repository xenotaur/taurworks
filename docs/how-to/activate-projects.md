# Activate a project with `tw activate`

`tw activate` gets your current shell ready to work on a project. It needs the
`tw` shell function loaded — see
[Install](install-and-update.md) if `tw` is not found.

## Activate by name

```bash
tw activate ProjectName
```

This works from any directory. Taurworks looks the name up in your project
registry and workspace root (see
[how names are resolved](../explanation/concepts.md#how-a-project-name-is-resolved)),
then, in this order:

1. runs `conda activate <env>`, if the project configures a Conda environment;
2. exports the project's configured environment variables;
3. changes directory to the project's working directory (or the project root,
   if no working directory is configured);
4. prints the project's activation message, if it has one.

If any step fails, `tw activate` stops there and returns non-zero. In
particular, if Conda activation fails, nothing is exported and your directory
does not change.

## Other ways to pick the project

| Command | Activates |
|---|---|
| `tw activate` | the project that contains the current directory |
| `tw activate ./some/dir` | the project whose root is that directory |
| `tw activate /abs/path/Project` | the project whose root is that directory |

A path must name the project root itself. Taurworks does not walk up from a
path to find the enclosing project: `tw activate .` from a subdirectory of a
project treats that subdirectory as an uninitialized project and stays put.
From inside a project, use `tw activate` with no argument.

A bare name is never searched for recursively under the current directory. To
activate a project in a nearby directory that is not in your workspace or
registry, give a path (`./Project`), or
[register it](manage-projects.md#register-a-project-that-lives-elsewhere).

## Preview without changing anything

```bash
taurworks project activate ProjectName --print
```

This prints everything activation would do — resolved project root, working
directory, environment name, how many variables would be exported — and
changes nothing. Exported values are never shown.

## Set what activation does

Activation is driven by the project's `.taurworks/config.toml`. You can edit
the file directly; two settings also have commands.

**Working directory** — run inside the project:

```bash
taurworks project working-dir set repo
```

**Conda environment:**

```bash
taurworks project env set my-env --project ProjectName
```

**Exports and message** — edit `.taurworks/config.toml`:

```toml
[activation]
message = "Ready for work on Alpha"

[activation.exports]
NODE_OPTIONS = "--max-old-space-size=8192"
```

Export values are literal strings. `~` and `$VARS` inside a value are not
expanded. See the
[configuration reference](../reference/configuration.md#project-config) for
all keys and their rules.

### Conda requirements

Taurworks runs `conda activate <name>` and nothing more. It does not run
`conda init`, and `tw activate` never creates an environment. Your shell must
already have a working `conda activate`, and the environment must already
exist.

## See why activation failed

Failures print a short reason. For the full diagnostic block:

```bash
tw activate ProjectName --verbose
```

`--debug` is a synonym for `--verbose`.

## Understand the warnings and notes

`tw activate` still succeeds in these cases, but tells you it could do less
than a full activation:

| Message mentions | Meaning | Fix |
|---|---|---|
| `note:` "no Conda activation environment is configured" | Informational. Everything else was applied; there is simply no environment to activate. Printed on every activation of a project without one. | `taurworks project env set ENV --project NAME`, or ignore it |
| "not initialized" | The directory has no `.taurworks/config.toml`. Only `cd` to the project root happened. | `taurworks project init PATH --working-dir DIR` |
| no working directory configured | The directory change went to the project root instead. The Conda environment, exports, and message were still applied. | `taurworks project working-dir set DIR` |
| "Legacy Admin/project-setup.source exists" | The project has an old-style setup script and no Taurworks config. Only `cd` to the project root happened; the script was not run. | [Migrate it](migrate-legacy-projects.md), or use [`tl`](use-tl-fallback.md) |

## Legacy setup scripts

For projects that still have an `Admin/project-setup.source` script,
`tw activate` accepts two more flags:

| Flag | Effect |
|---|---|
| `--legacy` | Source the legacy script once, for this activation. |
| `--no-legacy` | Do not source it, even if it is trusted. |

Both only matter after you have turned legacy sourcing on. See
[Migrate a legacy project](migrate-legacy-projects.md).

## Get paths for scripts

To use a project's location in a script or one-liner without activating it:

```bash
cd "$(tw working ProjectName)"
```

```bash
code "$(tw root ProjectName)"
```

`tw root` prints the project root; `tw working` prints the working directory
(falling back to the project root). Each prints exactly one absolute path on
stdout, or nothing on stdout and a non-zero exit on failure. Quote the
substitution so paths with spaces survive.
