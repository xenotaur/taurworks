# Development guide

For people changing Taurworks itself. To *use* Taurworks, start with
[Getting started](tutorials/getting-started.md).

## Repository layout

| Path | Contents |
|---|---|
| `src/taurworks/` | The tool: the Python package and the packaged shell resources. |
| `src/taurworks/resources/shell/taurworks-shell.sh` | The `tw` helper printed by `taurworks shell print`. |
| `src/taurworks/resources/sourceme/aliases.source` | The `tl` function, installed as `tl.source`. |
| `tests/` | Package tests (standard-library `unittest`). |
| `scripts/` | Canonical entry points for setup and quality checks. |
| `docs/` | User documentation. |
| `project/` | The project control plane: goals, roadmap, design, work items, audits. Managed with LRH; not user documentation. |

See [`AGENTS.md`](../AGENTS.md) for the architectural boundary between these
and [`STYLE.md`](../STYLE.md) for code style.

## Set up

From the repository root, in the Python environment you want to develop in:

```bash
./scripts/develop
```

This performs an editable install with the `dev` extra, constrained by
`constraints-dev.txt`, which is the single source of truth for formatter and
linter versions. CI uses the same script. Do not hand-install pinned tools
(`pip install black==...`); change `constraints-dev.txt` instead.

The script uses the environment's existing `pip` with `--no-build-isolation`,
installing `setuptools>=64` and `wheel` only if they are missing, so that it
works in offline and proxy-restricted environments.

The `test` extra is intentionally empty; tests need only the standard
library. Use `./scripts/develop`, not `pip install -e ".[test]"`, when you
need the formatter and linter.

To have your working copy also be the `taurworks` on your `PATH` across Conda
environments, see
[Install for developing Taurworks itself](how-to/install-and-update.md#install-for-developing-taurworks-itself).

## Check your work

| Script | Does |
|---|---|
| `./scripts/format` | Format with Black. |
| `./scripts/format --check --diff` | Check formatting without rewriting. |
| `./scripts/lint` | Check formatting with Black, then lint with Ruff. |
| `./scripts/test` | Run the unit tests. |
| `./scripts/smoke` | Run smoke tests. |
| `./scripts/test-portability` | Run the tests with temporary `HOME`, `XDG_CONFIG_HOME`, and `TAURWORKS_WORKSPACE`, so nothing reads or writes your real config or `~/Workspace`. |
| `./scripts/audit-side-effects` | Non-destructive helper for the side-effect audit. |
| `./scripts/version tools` | Print tool versions. |

GitHub Actions (`.github/workflows/python-ci.yml`) runs the standard and
portability suites on Ubuntu and macOS.

Since this repository is itself a Taurworks project, `taurworks dev test`,
`dev lint`, and so on delegate to the same scripts.

### Writing portable tests

macOS canonicalizes temporary paths (`/var/folders/...` becomes
`/private/var/folders/...`). Tests that inspect CLI diagnostics should parse
the `key: value` output and compare path fields with the shared helpers in
`tests/helpers.py`, not match raw path substrings.

## Verify an install

```bash
python -c "import taurworks; print(taurworks.__file__)"
```

```bash
taurworks --help
```

```bash
python -m taurworks.cli --help
```

## Side effects and safety

Command behavior that touches the filesystem, environment, or shell is
tracked in the [side-effect safety audit](../project/audits/side_effects.md).
A command's name is a promise about its risk: a safe-sounding command must
not perform a mutating or dangerous operation without an explicit flag. Read
the audit's safety baseline before adding or changing a command.

## Keeping documentation accurate

The user documentation describes behavior, so a change to a command, flag,
config key, or message usually needs a matching change in:

- [`docs/reference/cli.md`](reference/cli.md) or
  [`docs/reference/configuration.md`](reference/configuration.md);
- the relevant how-to guide;
- the command's own `--help` text in `src/taurworks/cli.py`.

## Process

- Prompt-driven changes follow [`PROMPTS.md`](../PROMPTS.md).
- Design documents are in [`project/design/`](../project/design/); the
  roadmap is [`project/roadmap/roadmap.md`](../project/roadmap/roadmap.md).
- [`docs/dogfood/`](dogfood/dogfood-session-review.md) has a manual
  walkthrough for validating a build end to end.

## History

The repository once contained a `bin/` directory of personal shell utilities
unrelated to the package. Those were split out, with history, into a separate
`taurscripts` repository.
