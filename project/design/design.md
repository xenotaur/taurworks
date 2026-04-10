# Design Overview

## High-level architecture (from code)
1. **CLI layer** (`taurworks/cli.py`)
   - Parses subcommands and options.
   - Delegates to manager functions.

2. **Manager layer** (`taurworks/manager.py`)
   - Implements project operations:
     - create/refresh project filesystem structure
     - discover/create Conda environments
     - generate activation setup script
     - list projects with optional details

3. **Filesystem + environment model**
   - Workspace root from `TAURWORKS_WORKSPACE` (default `~/Workspace`).
   - Per-project directory.
   - Per-project `.taurworks/` admin directory.
   - Per-project activation script (`project-setup.source`).
   - Per-project Conda environment named after project.

## Primary flows
- **Create flow:** CLI `create` -> `create_project` -> workspace/project/admin dirs + conda env + repo dir + setup script.
- **Refresh flow:** CLI `refresh` -> `refresh_project` -> idempotent checks and creation of missing components.
- **Activate flow:** CLI `activate` -> `activate_project` -> prints `source <.../project-setup.source>` for manual execution.
- **List flow:** CLI `projects` -> `list_projects` -> enumerates workspace project directories and compares to Conda env list.

## Conservative interpretation
- Appears to prioritize explicit, inspectable behavior over hidden automation.
- Unclear from repository whether a formal long-term schema for project metadata is planned.
