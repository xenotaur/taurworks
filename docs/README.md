# Taurworks documentation

Taurworks keeps track of your development projects and gets a shell ready to
work in one of them: `tw activate ProjectName` activates the project's Conda
environment, exports its variables, and changes to its working directory.

The documentation is organized by what you are trying to do.

## Start here

- [Getting started](tutorials/getting-started.md) — install Taurworks, create
  a project, and activate it. About ten minutes.

## How-to guides

Recipes for a specific task. They assume you have finished the tutorial.

- [Install, update, and uninstall](how-to/install-and-update.md)
- [Activate a project with `tw activate`](how-to/activate-projects.md)
- [Create, initialize, and register projects](how-to/manage-projects.md)
- [Use `tl`, the break-glass fallback](how-to/use-tl-fallback.md)
- [Migrate a legacy `Admin/project-setup.source` project](how-to/migrate-legacy-projects.md)
- [Run clean/test/lint/build with `taurworks dev`](how-to/run-dev-commands.md)
- [Troubleshooting](how-to/troubleshooting.md)

## Reference

Look up an exact command, flag, key, or variable.

- [Command reference](reference/cli.md) — every `taurworks`, `tw`, and `tl`
  command.
- [Configuration reference](reference/configuration.md) — config files, keys,
  environment variables, and file locations.

## Explanation

Background on how and why Taurworks works the way it does.

- [Concepts](explanation/concepts.md) — the `taurworks` / `tw` / `tl` layers,
  project roots and working directories, name resolution, and the safety
  model.

## Working on Taurworks itself

- [Development guide](development.md) — developer setup, tests, and quality
  scripts for contributors.
- [Dogfood session review](dogfood/dogfood-session-review.md) — a maintainer
  walkthrough script for validating a release by hand.
- Design documents, the roadmap, and audits live in the project control plane
  under [`project/`](../project/), not here.
