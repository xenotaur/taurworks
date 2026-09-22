"""Development-environment providers for Taurworks-managed projects.

Taurworks remains the host-side control plane.  Providers describe how a
project is entered and where its delegated commands execute; they do not own
project discovery or the environment's native configuration.
"""

from __future__ import annotations

import abc
import dataclasses
import json
import os
import pathlib
import shutil
import subprocess
from typing import Callable, Mapping, Sequence


class EnvironmentError(RuntimeError):
    """Raised when a development environment cannot be used safely."""


@dataclasses.dataclass(frozen=True)
class EnvironmentSpec:
    """Validated provider selection and provider-owned Taurworks metadata."""

    type: str
    name: str | None = None
    config: str | None = None


@dataclasses.dataclass(frozen=True)
class EnvironmentContext:
    """Project paths and exports needed by an environment provider."""

    project_name: str
    project_root: pathlib.Path
    host_working_dir: pathlib.Path
    relative_working_dir: pathlib.Path
    environment: EnvironmentSpec
    exports: Mapping[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class EnvironmentStatus:
    """Provider availability without changing external state."""

    available: bool
    detail: str


@dataclasses.dataclass(frozen=True)
class PreparedEnvironment:
    """Runtime details returned after a provider prepares an environment."""

    container_workspace: str | None = None
    container_working_dir: str | None = None


RunFunction = Callable[..., subprocess.CompletedProcess]


class EnvironmentProvider(abc.ABC):
    """Lifecycle and execution boundary for one environment type."""

    type_name: str
    shell_action: str

    @abc.abstractmethod
    def validate(self, context: EnvironmentContext) -> None:
        """Validate provider prerequisites without changing external state."""

    @abc.abstractmethod
    def status(self, context: EnvironmentContext) -> EnvironmentStatus:
        """Return read-only provider availability."""

    @abc.abstractmethod
    def prepare(self, context: EnvironmentContext) -> PreparedEnvironment:
        """Create or start reusable provider state when required."""

    @abc.abstractmethod
    def enter(self, context: EnvironmentContext) -> int:
        """Enter an interactive project environment and return its exit code."""

    @abc.abstractmethod
    def execute(self, context: EnvironmentContext, argv: Sequence[str]) -> int:
        """Execute argv in the project's execution environment."""

    def leave(self, context: EnvironmentContext) -> None:
        """Leave transient provider state without destroying reusable state."""

    def transition(
        self,
        previous: EnvironmentContext | None,
        target: EnvironmentContext,
    ) -> None:
        """Validate a transition before target state is made active."""

        self.validate(target)


class HostEnvironmentProvider(EnvironmentProvider):
    """Host/no-environment behavior."""

    type_name = "host"
    shell_action = "host"

    def validate(self, context: EnvironmentContext) -> None:
        if not context.host_working_dir.is_dir():
            raise EnvironmentError(
                f"host working directory does not exist: {context.host_working_dir}"
            )

    def status(self, context: EnvironmentContext) -> EnvironmentStatus:
        return EnvironmentStatus(
            context.host_working_dir.is_dir(), "commands execute on the host"
        )

    def prepare(self, context: EnvironmentContext) -> PreparedEnvironment:
        self.validate(context)
        return PreparedEnvironment()

    def enter(self, context: EnvironmentContext) -> int:
        self.prepare(context)
        return 0

    def execute(self, context: EnvironmentContext, argv: Sequence[str]) -> int:
        self.validate(context)
        return subprocess.run(list(argv), cwd=context.host_working_dir).returncode


class CondaEnvironmentProvider(HostEnvironmentProvider):
    """Conda execution preserves Taurworks' existing current-shell behavior."""

    type_name = "conda"
    shell_action = "conda"

    def status(self, context: EnvironmentContext) -> EnvironmentStatus:
        return EnvironmentStatus(
            True,
            "Conda activation is performed by the sourced tw helper in the host shell",
        )

    def enter(self, context: EnvironmentContext) -> int:
        raise EnvironmentError(
            "Conda activation must be performed by the sourced `tw activate` helper"
        )


class DevContainerEnvironmentProvider(EnvironmentProvider):
    """Dev Container provider backed exclusively by the reference CLI."""

    type_name = "devcontainer"
    shell_action = "devcontainer"
    executable = "devcontainer"

    def __init__(
        self,
        *,
        run: RunFunction = subprocess.run,
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self._run = run
        self._which = which

    def _tool_path(self) -> str:
        tool_path = self._which(self.executable)
        if tool_path is None:
            raise EnvironmentError(
                "Dev Container CLI is unavailable; install `@devcontainers/cli` "
                "and ensure `devcontainer` is on PATH"
            )
        return tool_path

    def _config_path(self, context: EnvironmentContext) -> pathlib.Path:
        root = context.project_root.resolve()
        if context.environment.config is not None:
            raw_path = pathlib.Path(context.environment.config)
            if raw_path.is_absolute():
                raise EnvironmentError(
                    "activation.environment.config must be relative to the project root"
                )
            config_path = (root / raw_path).resolve()
            try:
                config_path.relative_to(root)
            except ValueError as error:
                raise EnvironmentError(
                    "activation.environment.config may not escape the project root"
                ) from error
            if not config_path.is_file():
                raise EnvironmentError(
                    f"Dev Container configuration does not exist: {config_path}"
                )
            return config_path

        candidates = (
            root / ".devcontainer" / "devcontainer.json",
            root / ".devcontainer.json",
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise EnvironmentError(
            "Dev Container configuration was not found; expected "
            ".devcontainer/devcontainer.json or .devcontainer.json"
        )

    def validate(self, context: EnvironmentContext) -> None:
        self._tool_path()
        self._config_path(context)
        if not context.host_working_dir.is_dir():
            raise EnvironmentError(
                f"host working directory does not exist: {context.host_working_dir}"
            )
        if os.environ.get("TAURWORKS_EXECUTION_ENVIRONMENT") == "devcontainer":
            raise EnvironmentError(
                "unsafe nested environment transition: exit the current Dev Container "
                "shell and run `tw activate` from the host control shell"
            )

    def status(self, context: EnvironmentContext) -> EnvironmentStatus:
        try:
            self.validate(context)
        except EnvironmentError as error:
            return EnvironmentStatus(False, str(error))
        return EnvironmentStatus(True, "Dev Container CLI and configuration are ready")

    def _base_args(self, context: EnvironmentContext, command: str) -> list[str]:
        return [
            self._tool_path(),
            command,
            "--workspace-folder",
            str(context.project_root.resolve()),
            "--config",
            str(self._config_path(context)),
        ]

    @staticmethod
    def _failure_detail(result: subprocess.CompletedProcess) -> str:
        stderr = (result.stderr or "").strip()
        if stderr:
            return stderr.splitlines()[-1]
        stdout = (result.stdout or "").strip()
        if stdout:
            return stdout.splitlines()[-1]
        return f"external command exited with status {result.returncode}"

    @staticmethod
    def _up_result(stdout: str) -> dict[str, object]:
        for line in reversed(stdout.splitlines()):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and "outcome" in value:
                return value
        raise EnvironmentError(
            "Dev Container startup did not return a recognizable JSON result"
        )

    def _exec_args(
        self,
        context: EnvironmentContext,
        command: Sequence[str],
    ) -> list[str]:
        args = self._base_args(context, "exec")
        remote_env = {
            **context.exports,
            "TAURWORKS_ACTIVE_PROJECT": context.project_name,
            "TAURWORKS_ENVIRONMENT_TYPE": self.type_name,
            "TAURWORKS_EXECUTION_ENVIRONMENT": self.type_name,
        }
        for name, value in sorted(remote_env.items()):
            args.extend(("--remote-env", f"{name}={value}"))
        args.extend(command)
        return args

    def prepare(self, context: EnvironmentContext) -> PreparedEnvironment:
        self.validate(context)
        result = self._run(
            self._base_args(context, "up"),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise EnvironmentError(
                "Dev Container startup failed: " + self._failure_detail(result)
            )
        payload = self._up_result(result.stdout or "")
        if payload.get("outcome") != "success":
            raise EnvironmentError(
                "Dev Container startup failed: "
                + str(payload.get("message", payload.get("outcome", "unknown error")))
            )
        remote_workspace = payload.get("remoteWorkspaceFolder")
        if not isinstance(remote_workspace, str) or not remote_workspace.startswith(
            "/"
        ):
            raise EnvironmentError(
                "Dev Container startup succeeded but its workspace path could not be determined"
            )
        relative = context.relative_working_dir.as_posix()
        container_working_dir = remote_workspace.rstrip("/")
        if relative != ".":
            container_working_dir += "/" + relative

        check_result = self._run(
            self._exec_args(context, ("test", "-d", container_working_dir)),
            capture_output=True,
            text=True,
            check=False,
        )
        if check_result.returncode != 0:
            raise EnvironmentError(
                "Dev Container working directory is unavailable: "
                f"{container_working_dir}"
            )
        return PreparedEnvironment(remote_workspace, container_working_dir)

    def enter(self, context: EnvironmentContext) -> int:
        prepared = self.prepare(context)
        command = (
            "/bin/sh",
            "-lc",
            'cd -- "$1" && exec "${SHELL:-/bin/sh}" -l',
            "taurworks",
            str(prepared.container_working_dir),
        )
        result = self._run(self._exec_args(context, command), check=False)
        return result.returncode

    def execute(self, context: EnvironmentContext, argv: Sequence[str]) -> int:
        prepared = self.prepare(context)
        container_argv = list(argv)
        if container_argv:
            executable = pathlib.Path(container_argv[0])
            if executable.is_absolute():
                try:
                    relative_executable = executable.resolve().relative_to(
                        context.project_root.resolve()
                    )
                except ValueError:
                    pass
                else:
                    container_argv[0] = (
                        str(prepared.container_workspace).rstrip("/")
                        + "/"
                        + relative_executable.as_posix()
                    )
        command = [
            "/bin/sh",
            "-c",
            'cd -- "$1" && shift && exec "$@"',
            "taurworks",
            str(prepared.container_working_dir),
            *container_argv,
        ]
        return self._run(self._exec_args(context, command), check=False).returncode


_PROVIDERS: dict[str, EnvironmentProvider] = {
    "host": HostEnvironmentProvider(),
    "conda": CondaEnvironmentProvider(),
    "devcontainer": DevContainerEnvironmentProvider(),
}


def provider_for(environment: EnvironmentSpec) -> EnvironmentProvider:
    """Return the registered provider for a validated environment spec."""

    try:
        return _PROVIDERS[environment.type]
    except KeyError as error:
        raise EnvironmentError(
            f"unsupported development environment type: {environment.type!r}"
        ) from error


def spec_from_metadata(metadata: Mapping[str, str] | None) -> EnvironmentSpec:
    """Convert validated project metadata into a provider-neutral spec."""

    if metadata is None:
        return EnvironmentSpec("host")
    return EnvironmentSpec(
        type=metadata["type"],
        name=metadata.get("name"),
        config=metadata.get("config"),
    )
