# taurworks

Taurworks is a command-line development framework for creating, switching to, and working in multiple development projects.

## Current command model (design-aligned)

Taurworks currently standardizes on one primary executable:

```bash
taurworks
```

The intended command model is namespaced:

- `taurworks project ...` for project/workspace lifecycle operations.
- `taurworks dev ...` for repository/developer workflow operations.

Both namespaces are expected to share a common configuration/discovery core.

### Implementation status and compatibility

Status note: `taurworks project ...` now includes implemented read-only discovery/diagnostic commands (`where`, `list`) while additional project lifecycle commands remain planned. `taurworks dev ...` remains planned and is not implemented yet.

The namespaced model is the active design direction. The currently shipped CLI remains compatibility-first and continues to support top-level lifecycle commands such as:

- `taurworks create`
- `taurworks refresh`
- `taurworks activate`
- `taurworks projects`

The scaffolded `project` namespace currently includes two implemented read-only commands:

- `taurworks project where` (implemented, read-only diagnostics)
- `taurworks project list` (implemented, read-only discovery listing)

`taurworks project where` intentionally does not mutate files, environments, or shell state.
`taurworks project list` is also non-mutating and reports discoverable projects plus discovery limitations.

Breaking command removals/renames are intentionally deferred until a migration path is explicitly documented and implemented.


## `taurworks project where`

Use this command to inspect Taurworks project/config/discovery resolution without mutating anything:

```bash
taurworks project where
```

The output reports:

- current working directory
- nearest discovered project root candidate (based on `.taurworks/` metadata)
- discovery source
- XDG-style config path candidate and whether it currently exists (relative `XDG_CONFIG_HOME` values are ignored)
- whether project metadata was found
- current resolution limitations in plain language

## `taurworks project list`

Use this command to list discoverable Taurworks projects without mutating anything:

```bash
taurworks project list
```

Current output reports:

- current working directory
- discovery source used for this run
- number of discovered projects
- each discovered project name/path
- limitations of the current discovery stage

Current stage behavior:

- if the current directory (or one of its parents) contains `.taurworks/`, list that resolved project root
- otherwise, scan only direct child directories of the current working directory for `.taurworks/`
- if none are found, report zero projects with a clear no-projects-found line

## Safety and shell-integration guardrails

Taurworks documentation and command behavior should follow conservative shell safety:

- Do not silently mutate shell startup files (`.bashrc`, `.bash_profile`, etc.).
- Prefer commands that print shell instructions when parent-shell mutation is required.
- Keep environment activation explicit and inspectable (`source ...` performed by the operator).
- Make state-changing operations explicit; avoid implying hidden side effects.

## Phased roadmap status

Current phase work is focused on:

1. Documentation/design alignment.
2. Command-model clarification (`project` vs `dev`).
3. Shared configuration/discovery expectations.
4. Safety guardrails and migration-path clarity.

Out of scope for this phase:

- Immediate implementation of every planned `taurworks dev` command.
- Breaking removals of compatibility commands.
- Broad refactors unrelated to command-model alignment.

See `project/roadmap/roadmap.md` and `project/design/unified_command_model.md` for detail.

## Python package development

For Python package and CLI development, install Taurworks in editable mode from the repository root:

```bash
python -m pip install -e .
```

Then validate the package import and CLI entry point:

```bash
python -c "import taurworks; print(taurworks.__file__)"
taurworks --help
taurworks project --help
python -m taurworks.cli --help
```

The import package is provided from `src/taurworks/` using a standard `src/` layout.

## Legacy shell utility inventory (historical)

The repository still contains historical shell utilities under `bin/` and `sourceme/`. These artifacts remain available, but the command model and roadmap focus for Taurworks development is the `taurworks` executable and the documented namespaced direction above.
