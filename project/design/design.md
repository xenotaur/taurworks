# Design Overview

## Product model
Taurworks uses one executable, `taurworks`, with two namespaces:

- `taurworks project ...` for workspace/project lifecycle and activation concerns.
- `taurworks dev ...` for repo-local development workflow orchestration.

These namespaces are conceptually separate, but should share core services for discovery, configuration loading, diagnostics, and path normalization.

## CLI namespace model

### Project namespace
- `taurworks project init`
- `taurworks project activate`
- `taurworks project list`
- `taurworks project refresh`

### Dev namespace
- `taurworks dev init`
- `taurworks dev clean`
- `taurworks dev develop`
- `taurworks dev test`
- `taurworks dev smoke`
- `taurworks dev coverage`
- `taurworks dev lint`
- `taurworks dev format`
- `taurworks dev build`
- `taurworks dev update`
- `taurworks dev precommit`
- `taurworks dev publish`
- `taurworks dev sandbox`
- `taurworks dev version`
- `taurworks dev validate`

## Compatibility commands
Existing top-level commands such as `create`, `refresh`, `activate`, and `projects` remain documented compatibility commands until a migration plan is finalized.

## Dev command resolution model
For `taurworks dev <command>`, resolution should follow this order:

1. Explicit configured command
2. Project-local script (for example `scripts/test`)
3. Built-in default selected from project type/layout

This model preserves project intent while providing a reliable fallback path.

## Transparency and safety
- Command behavior should be explainable and inspectable.
- Dry-run, verbose, and doctor-style diagnostics should be supported where practical.
- Higher-risk commands (`clean`, `precommit`, `publish`, `update`, `sandbox`) should use conservative defaults and avoid implicit destructive behavior.

## Non-goals
- Do not replace standard tools with a new build/lint/test/package/release system.
- Do not split into unrelated init/discovery flows for project vs dev operations.
