# Taurworks Background (Agent-Facing)

## Purpose of This File

This document is intended to help an automated agent correctly interpret
the Taurworks repository and bootstrap an LRH-style `project/`
directory.

It prioritizes: - clarity over completeness - concrete signals over
abstraction - conservative inference over speculation

------------------------------------------------------------------------

## What Taurworks Is

Taurworks is:

-   A **personal Unix utility suite**
-   A **collection of Bash + Python tools**
-   An **emerging project bootstrap and environment management system**

It is transitioning from: \> ad-hoc utilities → structured
project/workspace system

------------------------------------------------------------------------

## Core Concept (IMPORTANT)

The central idea in Taurworks is:

> A **project = workspace directory + environment + metadata**

Each project includes: - a filesystem workspace - a Conda environment -
a `.taurworks/` metadata directory - a generated activation script
(`project-setup.source`)

This is the most important organizing principle.

------------------------------------------------------------------------

## Key Commands (Observed Behavior)

The `tw` CLI includes:

-   `projects` → list projects
-   `create` → create new project workspace
-   `refresh` → rebuild or update environment
-   `activate` → print shell command to activate project

IMPORTANT: - `activate` does NOT mutate the shell - it prints a `source`
command - user must explicitly run it

This is a deliberate design constraint.

------------------------------------------------------------------------

## Design Intent (Strong Signals)

The repository strongly suggests Taurworks is moving toward:

### 1. Project Bootstrap Tool

-   create projects in a consistent way
-   reduce manual setup
-   standardize environments

### 2. Environment Management

-   Conda-based environments
-   reproducible setup
-   script-driven configuration

### 3. Lightweight Philosophy

-   minimal abstraction
-   transparent scripts
-   user-visible behavior

------------------------------------------------------------------------

## Constraints (DO NOT VIOLATE)

When reasoning about Taurworks, assume:

-   DO NOT auto-activate environments
-   DO NOT silently modify user shell
-   DO NOT introduce hidden state
-   DO NOT rely on OS-specific hacks
-   MUST support MacOS and Linux

Prefer: - explicit commands - inspectable files - simple workflows

------------------------------------------------------------------------

## Known Gaps / Opportunities

These are likely areas for future work:

-   No formal project configuration schema
-   Limited metadata visibility for projects
-   No unified status or inspection command
-   Activation UX is indirect (manual `source`)
-   No plugin/extension model

Agents may propose these, but should NOT assume they already exist.

------------------------------------------------------------------------

## How to Bootstrap LRH project/

When creating a `project/` directory:

### Be Conservative

-   Use only information visible in the repo
-   Do not invent features
-   Mark uncertainty clearly

### Focus on These Interpretations

-   **Goal**: Taurworks as a project bootstrap + environment tool
-   **Design**: CLI + manager + workspace/env model
-   **Focus**: stabilizing project lifecycle (create/refresh/activate)
-   **Work Items**: UX improvements, config model, visibility,
    extensibility

### Handle Uncertainty Explicitly

Use phrases like: - "Appears to" - "Likely" - "Not fully specified in
repository"

------------------------------------------------------------------------

## Suggested LRH Interpretation (Lightweight)

This is a suggested mapping (do NOT treat as ground truth):

-   goal → bootstrap + environment management system
-   design → CLI (`tw`) + manager + filesystem + conda
-   focus → improving project lifecycle and usability
-   work_items → activation UX, config schema, project introspection
-   guardrails → explicit shell behavior, cross-platform support

------------------------------------------------------------------------

## Summary for Agent

If unsure, default to:

> Taurworks is an early-stage tool for creating and managing
> reproducible project workspaces using simple, explicit, script-driven
> mechanisms.

Do NOT over-generalize beyond that.
