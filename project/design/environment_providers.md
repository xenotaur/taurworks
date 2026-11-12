# Development Environment Providers

## Status

Implemented for Host/no-environment, Conda, and Dev Container projects.

## Boundary

Taurworks is the host control plane. Project resolution owns project identity,
the host project root, and the relative working directory. The environment
provider owns validation, status, preparation, interactive entry,
noninteractive execution, leaving, and transition checks.

```text
project resolution
  -> EnvironmentContext
     -> HostEnvironmentProvider
     -> CondaEnvironmentProvider
     -> DevContainerEnvironmentProvider
```

Provider selection is centralized in `src/taurworks/environments.py`. Project
configuration parsing validates provider-specific fields once; activation and
`taurworks dev` do not contain independent type ladders.

## Shell and execution semantics

- Host: the sourced helper applies project exports and changes the host CWD;
  delegated commands are host subprocesses.
- Conda: the sourced helper preserves the established `conda activate NAME`,
  exports, and host-CWD behavior; delegated commands inherit that host shell.
- Dev Container: the host invokes the reference CLI. `up` prepares/reuses the
  environment and returns `remoteWorkspaceFolder`; `exec` enters a child shell
  or runs delegated argv inside the container. Project exports are passed as
  remote environment values, not written into the host shell.

The provider maps a Taurworks `working_dir = "backend"` as follows:

```text
host:      <project_root>/backend
container: <remoteWorkspaceFolder>/backend
```

Both Taurworks paths are validated as project-root-relative. The container
workspace is runtime truth returned by `devcontainer up`; Taurworks never
assumes it equals the host path.

## Transitions and active state

The helper records `TAURWORKS_ACTIVE_PROJECT`, `TAURWORKS_ENVIRONMENT_TYPE`,
`TAURWORKS_EXECUTION_ENVIRONMENT`, and the names of Taurworks-owned exports.
These markers describe control/execution context; they are not used as a
persistent registry and disappear with the shell.

Dev Container entry is a blocking child execution boundary. The user exits that
shell before selecting another project. After a successful return, the helper
cleans previous Taurworks exports, leaves a previously Taurworks-selected Conda
environment, changes to the Dev Container project's host working directory,
and marks host control state. A subsequent `taurworks dev` command re-enters the
configured container for noninteractive execution.

Nested control is rejected when `TAURWORKS_EXECUTION_ENVIRONMENT=devcontainer`.
This prevents Container A from launching Container B or activating host Conda
inside A. The supported sequences are therefore:

```text
Conda A -> tw activate Container B -> container shell -> exit -> host control
host control -> tw activate Conda B

Container A shell -> exit -> host control -> tw activate Container B
```

Provider preparation happens before host mutation. If validation, startup, or
interactive entry fails, the target is not marked active and the previous host
directory, Conda context, and Taurworks exports remain in place.

## Dev Container CLI contract

Taurworks uses argv-based subprocess calls only:

- `devcontainer up --workspace-folder HOST_ROOT --config CONFIG`
- `devcontainer exec --workspace-folder HOST_ROOT --config CONFIG ...`

The project `devcontainer.json` remains authoritative. Taurworks does not parse
or duplicate Dockerfiles, images, Features, mounts, ports, users, or lifecycle
commands, and it does not call Docker directly. Interactive exit does not
rebuild, stop, or remove the reusable development container.

The fixed `/bin/sh` wrapper used for execution only changes to the runtime
container working directory before `exec`-ing preserved argv boundaries. No
project/config value is interpolated into shell source.

## Intentional limits

- Switching projects from inside the child container shell is rejected; return
  to the host control shell first.
- Container stop/remove/rebuild commands are not added. They are not required
  for activation or delegated execution and remain available through the
  reference CLI.
- The optional real integration test requires explicit
  `TAURWORKS_RUN_DEVCONTAINER_INTEGRATION=1`; normal CI has no Docker/CLI
  prerequisite and uses a mocked external-tool boundary.
