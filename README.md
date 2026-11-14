# taurworks

Taurworks is a command-line tool for creating, switching between, and working
in multiple development projects.

```bash
tw activate MyProject
```

From any directory, that one command activates the project's Conda
environment, exports its environment variables, and changes to its working
directory.

## Quick start

Taurworks is installed from a checkout; it is not on PyPI. You need bash,
Python 3.11+, and [pipx](https://pipx.pypa.io/).

```bash
scripts/install
```

Add the two `source` lines it prints to your `~/.bashrc` (Taurworks never
edits startup files itself) and open a new shell. Then:

```bash
tw workspace set ~/Workspace
```

```bash
tw project create Demo --working-dir repo --create-working-dir
```

```bash
tw activate Demo
```

The [getting started tutorial](docs/tutorials/getting-started.md) walks
through this step by step.

## The three commands

| Command | What it is | Use it for |
|---|---|---|
| `tw` | A shell function. Passes everything to `taurworks`, and can change your current shell. | Day-to-day use. `tw activate NAME` is the main event. |
| `taurworks` | The Python program behind `tw`. Cannot change your shell. | Scripts, and read-only previews such as `taurworks project activate NAME --print`. |
| `tl` | A tiny standalone shell function: `tl NAME` sources the project's `project-setup.source` script. | Emergencies — when `taurworks` has dropped off your `PATH` after a Conda switch, or `tw` is broken — and projects not yet migrated from legacy setup scripts. |

Why there are three: [Concepts](docs/explanation/concepts.md).

## Common tasks

| I want to... | Command | Guide |
|---|---|---|
| Switch to a project | `tw activate NAME` | [Activate projects](docs/how-to/activate-projects.md) |
| See my projects | `tw projects` | [Manage projects](docs/how-to/manage-projects.md) |
| Create a project | `tw project create NAME --working-dir DIR --create-working-dir` | [Manage projects](docs/how-to/manage-projects.md) |
| Adopt an existing directory | `tw project init PATH --working-dir DIR` | [Manage projects](docs/how-to/manage-projects.md) |
| Name a project outside my workspace | `tw project register NAME PATH` | [Manage projects](docs/how-to/manage-projects.md) |
| Set a project's Conda environment | `tw project env set ENV --project NAME` | [Activate projects](docs/how-to/activate-projects.md) |
| Run a project's tests | `tw dev test` | [Run dev commands](docs/how-to/run-dev-commands.md) |
| Activate when `tw` is broken | `tl NAME` | [Use `tl`](docs/how-to/use-tl-fallback.md) |
| Convert an old `Admin/project-setup.source` project | `taurworks legacy migrate NAME` | [Migrate legacy projects](docs/how-to/migrate-legacy-projects.md) |
| Update Taurworks | `scripts/install`, then `tw shell refresh` | [Install and update](docs/how-to/install-and-update.md) |
| Fix an error | | [Troubleshooting](docs/how-to/troubleshooting.md) |

## Documentation

- **[Documentation home](docs/README.md)**
- [Getting started](docs/tutorials/getting-started.md) (tutorial)
- [Command reference](docs/reference/cli.md)
- [Configuration reference](docs/reference/configuration.md)
- [Concepts](docs/explanation/concepts.md)

Built-in help is always available: `tw help`, `tw help project`,
`taurworks project create --help`.

## Safety

Taurworks is deliberately conservative: it never edits shell startup files,
only explicitly sourced shell functions change your shell, read-only commands
say that they are read-only, and project shell scripts are not run without
your explicit consent. See
[the safety model](docs/explanation/concepts.md#the-safety-model) and the
[side-effect safety audit](project/audits/side_effects.md).

## Contributing

See the [development guide](docs/development.md) for setup, tests, and
quality scripts. Design documents and the roadmap live under
[`project/`](project/).

## License

See [LICENSE](LICENSE).
