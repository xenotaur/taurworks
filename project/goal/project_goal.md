# Project Goal

## What Taurworks is (grounded)
Taurworks is a Unix utility repository that includes shell tooling (`bin/`), Python scripts, and a Python package exposing a CLI entry point (`taurworks=taurworks.cli:main`).

The current CLI provides project lifecycle commands:
- `projects` (list project environments)
- `create` (create project structure + Conda env)
- `refresh` (ensure structure/env are present)
- `activate` (print the shell command users should run)

## What it is trying to achieve (inferred conservatively)
Taurworks appears to be evolving from a personal utility collection into a lightweight project bootstrap + environment management tool.

Likely near-term objective:
- standardize project creation around a workspace directory,
- provision/update a Conda environment per project,
- keep activation explicit through a generated setup script.

## Fact vs inference
- **Fact:** The manager code creates project directories, `.taurworks/` metadata, Conda envs, and a `project-setup.source` script.
- **Inference:** The repository likely intends a reproducible, low-abstraction workflow for day-to-day project bootstrapping.
