# Project Context (Human-Oriented)

## One-line Description
- Taurworks is a command-line utility suite that currently includes a project lifecycle tool for creating, refreshing, listing, and activating development project environments.

## Overview
- The repository combines legacy Unix utilities (`bin/`) with an installable Python CLI (`taurworks=taurworks.cli:main`).
- Current lifecycle operations are centered in `taurworks/cli.py` and `taurworks/manager.py`.
- Lifecycle behavior is explicit and inspectable: directories and scripts are created on disk; activation is printed for manual sourcing.

## Goals and Direction
- Goal: Provide a practical CLI for project creation and common lifecycle tasks.
- Near-term focus: Stabilize and clarify current lifecycle operations and documentation while preserving explicit behavior.

## Design Snapshot
- CLI parses subcommands and delegates to manager operations.
- Manager coordinates filesystem scaffolding, Conda environment discovery/creation, and setup script generation.
- Workspace is rooted at `TAURWORKS_WORKSPACE` (default `~/Workspace`).

## Current Status Snapshot
- Health appears **yellow**: core behavior exists and is usable, but governance/roadmap/contributor/evidence structure was incomplete before this bootstrap completion.

## Known Unknowns
- Whether non-Conda backends are in scope.
- Whether formal project metadata/config schema will be introduced.
- Long-term boundary between legacy utility scripts and lifecycle manager functionality.

## Notes
- Derived summary only (non-authoritative).
