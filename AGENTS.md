# AGENTS.md

This repository is the home of **Taurworks**.

Taurworks is intended to be a development framework for creating, switching to and doing development in multiple development projects.

## Mission

Build a command line utility that can:

1. Initialize projects for isolated development work.
2. List, manage and organize projects.
3. Switch between projects (and restore project state).
4. Run stereotyped development tasks including cleaning, building, testing.

## Architectural boundary

Keep clear separation between:

1. **the tool code** in `src/taurworks/`
2. **package tests** in `tests/`
3. **the project control plane** in `project/`

## Current implementation priority

Focus first on the most useful command line utility:

1. Create a global configuration following XDG standards.
2. Register existing project configurations with name, target directory, and conda environment.
3. Switch to those directories
4. Support at least one dev command such as test.
5. Improve as needed and add missing features.

## Repository conventions

### Project schema

Taurworks uses a Logical Robotics Harness (LRH) control-plane schema. This project control stack contains:

**Principles → Project Goal → Roadmap → Current Focus → Work Items → Evidence → Status**

Taurworks does not need to manage this state; it is run by the LRH command or the human user. LRH tooling is used to create and manage this state in the project directory.

## Engineering style

- Prefer readable, explicit Python.
- Prefer modular organization by concern.
- Avoid hidden magic in repo discovery.
- Keep formats stable and documented.

## Immediate task guidance

When asked to make progress in this repository, prefer work that advances the first validation path:

1. Create a global configuration following XDG standards.
2. Register existing project configurations with name, target directory, and conda environment.
3. Switch to those directories
4. Support at least one dev command such as test.
5. Improve as needed and add missing features.


## Prompt-driven work

When a task is driven by a generated prompt, follow `PROMPTS.md` for prompt IDs, execution records, rerun handling, and optional work-item traceability. Do not create prompt records for trivial or purely exploratory work unless asked.
