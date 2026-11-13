import dataclasses
import enum
import errno
import os
import pathlib
import re
import stat
import tomllib
from collections.abc import Callable
from typing import Any

PROJECT_SCHEMA_VERSION = 1
BARE_TOML_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
ENVIRONMENT_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CONDA_ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
SUPPORTED_ACTIVATION_ENVIRONMENT_TYPES = {"conda"}


class ProjectConfigError(ValueError):
    """Raised when Taurworks project config cannot be safely updated."""


class ResolutionReason(enum.StrEnum):
    """Stable reasons for project target resolution."""

    CURRENT_PROJECT = "current_project"
    EXISTING_PATH = "existing_path"
    EXISTING_PATH_PROJECT_ROOT = "existing_path_project_root"
    CURRENT_PROJECT_NAME = "current_project_name"
    CURRENT_DIRECTORY_BASENAME = "current_directory_basename"
    CHILD_PATH = "child_path"
    DEFAULT_CURRENT_DIRECTORY = "default_current_directory"
    REGISTERED_PROJECT = "registered_project"
    WORKSPACE_INITIALIZED_PROJECT = "workspace_initialized_project"
    WORKSPACE_LEGACY_ADMIN_PROJECT = "workspace_legacy_admin_project"
    WORKSPACE_ONLY_PROJECT = "workspace_only_project"
    WORKING_DIR_REVERSE_LOOKUP = "working_dir_reverse_lookup"
    WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS = "working_dir_reverse_lookup_ambiguous"


@dataclasses.dataclass(frozen=True)
class ProjectResolution:
    """Inspectable result of resolving a project path or name.

    When `resolved_by` is `WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS`,
    `project_root` is only a placeholder (the directory discovery started
    from, which never contains `.taurworks/`) and must not be used as a
    target; `candidates` lists the competing project roots.
    """

    input: str
    project_root: pathlib.Path
    resolved_by: ResolutionReason
    candidates: tuple[pathlib.Path, ...] = ()

    @property
    def ambiguous(self) -> bool:
        """Return whether discovery matched several projects equally well."""
        return self.resolved_by is ResolutionReason.WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS


class DiscoverySource(enum.StrEnum):
    """How cwd/path-based project discovery resolved (see config_model.md)."""

    PHYSICAL_WALK = "physical_walk"
    WORKING_DIR_REVERSE_LOOKUP = "working_dir_reverse_lookup"
    WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS = "working_dir_reverse_lookup_ambiguous"
    NONE = "none"


@dataclasses.dataclass(frozen=True)
class PathDiscovery:
    """Result of discovering the project that contains a directory.

    `root` is set for `PHYSICAL_WALK` and `WORKING_DIR_REVERSE_LOOKUP`; it is
    `None` for `NONE` and for an ambiguous lookup, whose `candidates` list
    the competing project roots.
    """

    root: pathlib.Path | None
    source: DiscoverySource
    matched_project: str | None = None
    candidates: tuple[pathlib.Path, ...] = ()

    @property
    def ambiguous(self) -> bool:
        """Return whether the reverse lookup matched several projects."""
        return self.source is DiscoverySource.WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS


AMBIGUITY_GUIDANCE = {
    "target": ("pass the project name, or the path to its project_root, to choose one"),
    "path": (
        "pass the path to the chosen project_root (bare names here resolve "
        "relative to the current directory)"
    ),
    "rerun": "rerun from the chosen project_root",
    "rerun_working_dir_set": (
        "rerun from the chosen project_root, passing DIR relative to that "
        "project_root"
    ),
}


def ambiguous_discovery_message(
    candidates: tuple[pathlib.Path, ...], guidance_kind: str
) -> str:
    """Explain an ambiguous working_dir reverse lookup and how to recover."""
    listed = ", ".join(str(candidate) for candidate in candidates)
    return (
        "This directory is inside the working_dir of more than one known "
        f"project ({listed}); Taurworks will not guess. To proceed, "
        f"{AMBIGUITY_GUIDANCE[guidance_kind]}."
    )


def physical_discovery(start: pathlib.Path) -> PathDiscovery:
    """Discover a project by walking the physical parents of `start` only."""
    root = find_project_root_candidate(start.resolve())
    if root is None:
        return PathDiscovery(root=None, source=DiscoverySource.NONE)
    return PathDiscovery(root=root, source=DiscoverySource.PHYSICAL_WALK)


def project_name_from_path(project_root: pathlib.Path) -> str:
    """Return a stable project display name from a project root path."""
    return project_root.name


def find_project_root_candidate(cwd: pathlib.Path) -> pathlib.Path | None:
    """Find the nearest directory that contains `.taurworks`."""
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".taurworks").is_dir():
            return candidate
    return None


def config_path_candidate() -> pathlib.Path:
    """Return the XDG-style Taurworks config path candidate."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        candidate_base_dir = pathlib.Path(xdg_config_home).expanduser()
        if candidate_base_dir.is_absolute():
            base_dir = candidate_base_dir
        else:
            base_dir = pathlib.Path.home() / ".config"
    else:
        base_dir = pathlib.Path.home() / ".config"
    return base_dir / "taurworks" / "config.toml"


def discover_projects_from_context(
    cwd: pathlib.Path,
) -> tuple[list[pathlib.Path], str, str]:
    """Discover projects using current-context-first behavior for `project list`."""
    project_root = find_project_root_candidate(cwd)
    if project_root is not None:
        return (
            [project_root],
            "current context (.taurworks found in current/parent path)",
            "Global registry/workspace scanning is not implemented yet; reporting current context.",
        )

    discovered_projects = sorted(
        (
            child
            for child in cwd.iterdir()
            if child.is_dir() and (child / ".taurworks").is_dir()
        ),
        key=lambda path: path.name,
    )
    return (
        discovered_projects,
        "cwd child-directory scan for .taurworks metadata",
        "Only current working directory and direct children are scanned in this stage.",
    )


def project_name_from_config(project_root: pathlib.Path) -> str:
    """Return configured project name, falling back to the root basename."""
    try:
        config = read_project_config(project_root)
    except (OSError, ProjectConfigError, tomllib.TOMLDecodeError):
        return project_name_from_path(project_root)

    project_table = config.get("project")
    if not isinstance(project_table, dict):
        return project_name_from_path(project_root)

    project_name = project_table.get("name")
    if not isinstance(project_name, str) or not project_name.strip():
        return project_name_from_path(project_root)
    return project_name


def _path_candidate(path_or_name: str, cwd: pathlib.Path) -> pathlib.Path:
    raw_path = pathlib.Path(path_or_name).expanduser()
    if raw_path.is_absolute():
        return raw_path
    return cwd / raw_path


def _may_be_current_project_name(path_or_name: str) -> bool:
    """Return whether a target could match the current project's name."""
    return len(pathlib.PurePath(path_or_name).parts) == 1 and path_or_name not in {
        ".",
        "..",
    }


def resolve_project_target(
    path_or_name: str | None,
    cwd: pathlib.Path,
    *,
    prefer_project_root: bool = False,
    discover: Callable[[pathlib.Path], PathDiscovery] | None = None,
) -> ProjectResolution:
    """Resolve a project target with stable, inspectable precedence rules.

    `discover` finds the project containing a directory. It defaults to
    `physical_discovery`; callers that can see the registry and workspace
    pass `manager.find_project_root_for_path` so that a directory inside a
    symlinked working_dir target is attributed to its project. It is used
    for the no-target case, the current-project name check, and (with
    `prefer_project_root`) existing path targets. An ambiguous lookup is
    returned as such, never replaced by a fallback resolution -- except that
    an ambiguous cwd does not block an explicit target, which falls through
    to the path rules below.
    """
    discover = discover or physical_discovery
    resolved_cwd = cwd.resolve()
    display_input = path_or_name or "(current working directory)"
    cwd_discovery: PathDiscovery | None = None
    if path_or_name is None or _may_be_current_project_name(path_or_name):
        cwd_discovery = discover(resolved_cwd)

    if path_or_name is None:
        if cwd_discovery.root is not None:
            reason = ResolutionReason.CURRENT_PROJECT
            if cwd_discovery.source is DiscoverySource.WORKING_DIR_REVERSE_LOOKUP:
                reason = ResolutionReason.WORKING_DIR_REVERSE_LOOKUP
            return ProjectResolution(
                input=display_input,
                project_root=cwd_discovery.root,
                resolved_by=reason,
            )
        if cwd_discovery.ambiguous:
            return ProjectResolution(
                input=display_input,
                project_root=resolved_cwd,
                resolved_by=ResolutionReason.WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS,
                candidates=cwd_discovery.candidates,
            )
        return ProjectResolution(
            input=display_input,
            project_root=resolved_cwd,
            resolved_by=ResolutionReason.DEFAULT_CURRENT_DIRECTORY,
        )

    if cwd_discovery is not None and cwd_discovery.root is not None:
        current_project_name = project_name_from_config(cwd_discovery.root)
        if path_or_name == current_project_name:
            return ProjectResolution(
                input=display_input,
                project_root=cwd_discovery.root,
                resolved_by=ResolutionReason.CURRENT_PROJECT_NAME,
            )

    if resolved_cwd.name == path_or_name and (resolved_cwd / ".taurworks").is_dir():
        return ProjectResolution(
            input=display_input,
            project_root=resolved_cwd,
            resolved_by=ResolutionReason.CURRENT_DIRECTORY_BASENAME,
        )

    candidate = _path_candidate(path_or_name, resolved_cwd)
    if candidate.exists():
        resolved_candidate = candidate.resolve()
        if prefer_project_root:
            search_base = resolved_candidate
            if not search_base.is_dir():
                search_base = search_base.parent
            discovery = discover(search_base)
            if discovery.root is not None:
                reason = ResolutionReason.EXISTING_PATH_PROJECT_ROOT
                if discovery.source is DiscoverySource.WORKING_DIR_REVERSE_LOOKUP:
                    reason = ResolutionReason.WORKING_DIR_REVERSE_LOOKUP
                return ProjectResolution(
                    input=display_input,
                    project_root=discovery.root,
                    resolved_by=reason,
                )
            if discovery.ambiguous:
                return ProjectResolution(
                    input=display_input,
                    project_root=resolved_candidate,
                    resolved_by=ResolutionReason.WORKING_DIR_REVERSE_LOOKUP_AMBIGUOUS,
                    candidates=discovery.candidates,
                )
        return ProjectResolution(
            input=display_input,
            project_root=resolved_candidate,
            resolved_by=ResolutionReason.EXISTING_PATH,
        )

    return ProjectResolution(
        input=display_input,
        project_root=candidate.resolve(),
        resolved_by=ResolutionReason.CHILD_PATH,
    )


def project_config_path(project_root: pathlib.Path) -> pathlib.Path:
    """Return the project-local Taurworks config path for a project root."""
    return project_root / ".taurworks" / "config.toml"


def read_project_config(project_root: pathlib.Path) -> dict[str, Any]:
    """Read project-local Taurworks config, returning an empty config if absent."""
    config_path = project_config_path(project_root)
    if not config_path.exists():
        return {}
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


def _toml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _toml_quote(value)
    raise ProjectConfigError(
        f"unsupported config value type for safe writer: {type(value).__name__}"
    )


def _validate_bare_toml_key(key: str) -> None:
    if not isinstance(key, str) or not BARE_TOML_KEY_PATTERN.fullmatch(key):
        raise ProjectConfigError(
            f"unsupported TOML key for safe writer: {key!r}; only bare keys are supported"
        )


def _partition_toml_items(
    table: dict[str, Any],
) -> tuple[list[tuple[str, Any]], list[tuple[str, dict[str, Any]]]]:
    scalar_items: list[tuple[str, Any]] = []
    table_items: list[tuple[str, dict[str, Any]]] = []
    for key, value in table.items():
        _validate_bare_toml_key(key)
        if isinstance(value, dict):
            table_items.append((key, value))
        else:
            scalar_items.append((key, value))
    return scalar_items, table_items


def _append_toml_table_lines(
    lines: list[str],
    table_path: tuple[str, ...],
    table: dict[str, Any],
) -> None:
    scalar_items, table_items = _partition_toml_items(table)
    if lines:
        lines.append("")
    lines.append(f"[{'.'.join(table_path)}]")
    for key, value in scalar_items:
        lines.append(f"{key} = {_toml_scalar(value)}")
    for key, nested_table in table_items:
        _append_toml_table_lines(lines, (*table_path, key), nested_table)


def _toml_lines(config: dict[str, Any]) -> list[str]:
    scalar_items, table_items = _partition_toml_items(config)

    lines: list[str] = []
    for key, value in scalar_items:
        lines.append(f"{key} = {_toml_scalar(value)}")

    for table_name, table in table_items:
        _append_toml_table_lines(lines, (table_name,), table)

    return lines


def write_project_config(project_root: pathlib.Path, config: dict[str, Any]) -> None:
    """Write project-local Taurworks config using the small supported TOML shape."""
    metadata_dir = project_root / ".taurworks"
    config_path = project_config_path(project_root)
    if metadata_dir.is_symlink():
        raise ProjectConfigError(
            f"metadata path is a symlink and is not modified for safety: {metadata_dir}"
        )
    if config_path.is_symlink():
        raise ProjectConfigError(
            f"config path is a symlink and is not modified for safety: {config_path}"
        )
    config_path.write_text("\n".join(_toml_lines(config)) + "\n", encoding="utf-8")


def ensure_minimal_project_config(
    project_root: pathlib.Path,
    config: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Ensure schema version and project name defaults are present in config."""
    updated_config = dict(
        config if config is not None else read_project_config(project_root)
    )
    changes: list[str] = []

    schema_version = updated_config.get("schema_version")
    if type(schema_version) is int and schema_version != PROJECT_SCHEMA_VERSION:
        raise ProjectConfigError(
            f"unsupported project config schema_version: {schema_version}; expected {PROJECT_SCHEMA_VERSION}"
        )
    if schema_version != PROJECT_SCHEMA_VERSION:
        updated_config["schema_version"] = PROJECT_SCHEMA_VERSION
        changes.append(f"schema_version set to {PROJECT_SCHEMA_VERSION}")

    project_table = updated_config.get("project")
    if not isinstance(project_table, dict):
        project_table = {}
        updated_config["project"] = project_table
        changes.append("project table created")

    project_name = project_table.get("name")
    if not isinstance(project_name, str) or not project_name.strip():
        project_table["name"] = project_name_from_path(project_root)
        changes.append(f"project.name set to {project_table['name']}")

    paths_table = updated_config.get("paths")
    if paths_table is not None and not isinstance(paths_table, dict):
        raise ProjectConfigError("config [paths] value is not a TOML table")

    return updated_config, changes


def activation_message_from_config(config: dict[str, Any]) -> str | None:
    """Return configured activation message when present."""
    activation_table = config.get("activation")
    if activation_table is None:
        return None
    if not isinstance(activation_table, dict):
        raise ProjectConfigError("config [activation] value is not a TOML table")

    message = activation_table.get("message")
    if message is None:
        return None
    if not isinstance(message, str):
        raise ProjectConfigError("config activation.message value must be a string")
    return message


def validate_activation_export_name(name: str) -> None:
    """Validate a conservative shell environment variable name."""
    if not ENVIRONMENT_VARIABLE_NAME_PATTERN.fullmatch(name):
        raise ProjectConfigError(
            f"invalid activation export name: {name!r}; expected [A-Za-z_][A-Za-z0-9_]*"
        )


def activation_exports_from_config(config: dict[str, Any]) -> dict[str, str]:
    """Return validated activation exports from config in deterministic order."""
    activation_table = config.get("activation")
    if activation_table is None:
        return {}
    if not isinstance(activation_table, dict):
        raise ProjectConfigError("config [activation] value is not a TOML table")

    exports_table = activation_table.get("exports")
    if exports_table is None:
        return {}
    if not isinstance(exports_table, dict):
        raise ProjectConfigError(
            "config [activation.exports] value is not a TOML table"
        )

    exports: dict[str, str] = {}
    for name in sorted(exports_table):
        validate_activation_export_name(name)
        value = exports_table[name]
        if not isinstance(value, str):
            raise ProjectConfigError(
                f"activation export {name!r} value must be a string"
            )
        exports[name] = value
    return exports


def validate_conda_environment_name(name: str) -> None:
    """Validate a conservative Conda environment name for shell activation."""
    if not CONDA_ENVIRONMENT_NAME_PATTERN.fullmatch(name):
        raise ProjectConfigError(
            f"invalid Conda activation environment name: {name!r}; "
            "expected [A-Za-z0-9][A-Za-z0-9_.-]*"
        )


def activation_environment_from_config(config: dict[str, Any]) -> dict[str, str] | None:
    """Return validated activation environment metadata when configured."""
    activation_table = config.get("activation")
    if activation_table is None:
        return None
    if not isinstance(activation_table, dict):
        raise ProjectConfigError("config [activation] value is not a TOML table")

    environment_table = activation_table.get("environment")
    if environment_table is None:
        return None
    if not isinstance(environment_table, dict):
        raise ProjectConfigError(
            "config [activation.environment] value is not a TOML table"
        )

    environment_type = environment_table.get("type")
    if not isinstance(environment_type, str) or not environment_type.strip():
        raise ProjectConfigError(
            "config activation.environment.type value must be the string 'conda'"
        )
    if environment_type not in SUPPORTED_ACTIVATION_ENVIRONMENT_TYPES:
        raise ProjectConfigError(
            "unsupported activation environment type: "
            f"{environment_type!r}; only 'conda' is supported"
        )

    name = environment_table.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ProjectConfigError(
            "config activation.environment.name value is required for Conda activation"
        )
    validate_conda_environment_name(name)
    return {"type": environment_type, "name": name}


def set_activation_environment(
    project_root: pathlib.Path,
    name: str,
) -> tuple[str | None, str, list[str]]:
    """Update project config with a validated Conda activation environment name.

    This is an explicit setter: a malformed existing `[activation.environment]`
    (invalid type, missing name, etc.) is overwritten rather than blocking the
    write, since the whole point of this command is to replace it.
    """
    validate_conda_environment_name(name)
    config = read_project_config(project_root)
    try:
        existing_environment = activation_environment_from_config(config)
    except ProjectConfigError:
        existing_environment = None
    previous_name = existing_environment["name"] if existing_environment else None
    config, repairs = ensure_minimal_project_config(project_root, config)

    activation_table = config.get("activation")
    if not isinstance(activation_table, dict):
        activation_table = {}
        config["activation"] = activation_table
    activation_table["environment"] = {"type": "conda", "name": name}

    write_project_config(project_root, config)
    return previous_name, name, repairs


def dev_command_from_config(config: dict[str, Any], name: str) -> str | None:
    """Return the configured Tier 1 `[dev.commands].<name>` string, if any."""
    dev_table = config.get("dev")
    if dev_table is None:
        return None
    if not isinstance(dev_table, dict):
        raise ProjectConfigError("config [dev] value is not a TOML table")

    commands_table = dev_table.get("commands")
    if commands_table is None:
        return None
    if not isinstance(commands_table, dict):
        raise ProjectConfigError("config [dev.commands] value is not a TOML table")

    command = commands_table.get(name)
    if command is None:
        return None
    if not isinstance(command, str) or not command.strip():
        raise ProjectConfigError(
            f"config dev.commands.{name} value must be a non-empty string"
        )
    return command


def working_dir_from_config(config: dict[str, Any]) -> str | None:
    """Return configured working_dir if present and valid enough to display."""
    paths_table = config.get("paths")
    if not isinstance(paths_table, dict):
        return None
    working_dir = paths_table.get("working_dir")
    if not isinstance(working_dir, str) or not working_dir:
        return None
    return working_dir


WORKING_DIR_ABSOLUTE_MESSAGE = "working_dir must be relative to the project root; absolute paths are not supported yet"
WORKING_DIR_ESCAPE_MESSAGE = (
    "working_dir must stay inside the project root and may not escape with '..'"
)
WORKING_DIR_DOTDOT_MESSAGE = (
    "working_dir may not escape the project root or contain '..' components; "
    "rewrite it as a plain relative path under the project root "
    "(for example `repo` instead of `repo/../repo`)"
)


def check_working_dir_symlinks(
    project_root: pathlib.Path,
    relative_path: pathlib.Path,
) -> None:
    """Reject a dangling or looping symlink along the lexical working_dir path.

    Walks `project_root` and then each prefix of `project_root / relative_path`
    without resolving it. A component that is a symlink must resolve to an
    existing target; a dangling or looping link raises `ProjectConfigError`
    instead of being reported as an ordinary missing directory. The walk stops
    at the first component that does not exist at all (an ordinary missing
    tail). This uses explicit `lstat`/`stat` calls rather than relying on
    `Path.is_dir()` or `Path.resolve()`, whose behavior for dangling and
    looping links differs across Python versions.
    """
    candidates = [project_root]
    for part in relative_path.parts:
        candidates.append(candidates[-1] / part)

    for candidate in candidates:
        try:
            link_status = os.lstat(candidate)
        except OSError:
            # Missing (or unreadable) component: an ordinary missing tail that
            # each caller's existing missing-directory policy handles.
            return
        if not stat.S_ISLNK(link_status.st_mode):
            continue
        try:
            os.stat(candidate)
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise ProjectConfigError(
                    f"working_dir path component is a symlink loop: {candidate}"
                ) from error
            if error.errno in (errno.ENOENT, errno.ENOTDIR):
                raise ProjectConfigError(
                    "working_dir path component is a dangling symlink: "
                    f"{candidate} -> {_readlink_for_display(candidate)}"
                ) from error
            raise ProjectConfigError(
                "working_dir path component is a symlink that cannot be followed: "
                f"{candidate} ({error.strerror})"
            ) from error


def _readlink_for_display(path: pathlib.Path) -> str:
    """Return a symlink's literal target for error messages, best effort."""
    try:
        return os.readlink(path)
    except OSError:
        return "(unreadable target)"


WORKING_DIR_LINK_BOUNDARY_MESSAGE = (
    "working_dir may not escape with '..' past the symlinked working_dir "
    "component; run `taurworks project working-dir set` from the project root "
    "to choose a directory outside the linked work tree"
)


def _map_cwd_through_working_dir(
    resolved_project_root: pathlib.Path,
    resolved_cwd: pathlib.Path,
    configured_working_dir: str | None,
) -> tuple[list[str], int] | None:
    """Map a cwd inside the resolved working_dir target back through the link.

    Returns `(parts, min_parts)`: the lexical, project-root-relative parts of
    the cwd (the configured working_dir value plus the cwd's path relative to
    its resolved target) and how many leading parts a `..` may never remove.
    The boundary is the last symlink component of the lexical path; every
    component after it is symlink-free, so a lexical step up there equals a
    physical one. Returns None when the cwd is not inside the target.
    """
    if not configured_working_dir:
        return None
    try:
        relative, target, _exists = resolve_configured_working_dir(
            resolved_project_root, configured_working_dir
        )
    except ProjectConfigError:
        return None
    try:
        tail = resolved_cwd.relative_to(target).parts
    except ValueError:
        return None

    configured_parts = list(relative.parts)
    boundary: int | None = None
    candidate = resolved_project_root
    for index, part in enumerate(configured_parts):
        candidate = candidate / part
        if candidate.is_symlink():
            boundary = index
    if boundary is None:
        return None
    return configured_parts + list(tail), boundary + 1


def relative_working_dir(
    project_root: pathlib.Path,
    cwd: pathlib.Path,
    user_path: str | None,
    configured_working_dir: str | None = None,
) -> pathlib.Path:
    """Validate and return a working directory path relative to project root.

    `user_path` is interpreted relative to `cwd`. The physical (resolved) `cwd`
    contains no symlinks, so its position under the resolved project root is
    a plain relative prefix. Leading `..` components of `user_path` step up
    within that prefix and may not climb above the project root; a `..` after
    any ordinary component is rejected, because it could follow a symlink. The
    resulting stored value is checked lexically, never by resolving it, so a
    component that is a symlink to a directory outside the project root is
    accepted.

    When the cwd is outside the resolved project root but inside the resolved
    target of the `configured_working_dir` symlink, it is mapped back through
    the link (see `_map_cwd_through_working_dir`); a leading `..` may then
    remove components only after the last symlink component.
    """
    resolved_project_root = project_root.resolve()
    resolved_cwd = cwd.resolve()
    min_parts = 0
    try:
        parts = list(resolved_cwd.relative_to(resolved_project_root).parts)
    except ValueError as error:
        mapped = _map_cwd_through_working_dir(
            resolved_project_root, resolved_cwd, configured_working_dir
        )
        if mapped is None:
            raise ProjectConfigError(WORKING_DIR_ESCAPE_MESSAGE) from error
        parts, min_parts = mapped

    if user_path is not None:
        raw_path = pathlib.Path(user_path).expanduser()
        if raw_path.is_absolute():
            raise ProjectConfigError(WORKING_DIR_ABSOLUTE_MESSAGE)
        seen_component = False
        for part in raw_path.parts:
            if part == "..":
                if seen_component:
                    raise ProjectConfigError(WORKING_DIR_DOTDOT_MESSAGE)
                if len(parts) <= min_parts:
                    raise ProjectConfigError(
                        WORKING_DIR_LINK_BOUNDARY_MESSAGE
                        if min_parts
                        else WORKING_DIR_ESCAPE_MESSAGE
                    )
                parts.pop()
            else:
                seen_component = True
                parts.append(part)

    relative_path = pathlib.Path(*parts) if parts else pathlib.Path(".")
    check_working_dir_symlinks(resolved_project_root, relative_path)

    target_path = resolved_project_root / relative_path
    if not target_path.is_dir():
        raise ProjectConfigError(
            f"working_dir target must be an existing directory: {target_path}"
        )
    return relative_path


def set_working_dir(
    project_root: pathlib.Path,
    cwd: pathlib.Path,
    user_path: str | None,
) -> tuple[str | None, str, list[str]]:
    """Update project config with a validated relative working directory."""
    config = read_project_config(project_root)
    previous_working_dir = working_dir_from_config(config)
    config, repairs = ensure_minimal_project_config(project_root, config)
    relative_path = relative_working_dir(
        project_root, cwd, user_path, configured_working_dir=previous_working_dir
    )
    relative_path_text = relative_path.as_posix()

    paths_table = config.get("paths")
    if not isinstance(paths_table, dict):
        paths_table = {}
        config["paths"] = paths_table
    paths_table["working_dir"] = relative_path_text

    write_project_config(project_root, config)
    return previous_working_dir, relative_path_text, repairs


def relative_working_dir_metadata(
    project_root: pathlib.Path,
    user_path: str,
) -> tuple[pathlib.Path, bool]:
    """Validate working-dir metadata lexically without requiring existence.

    The literal value must be relative and contain no `..` component. It is
    not resolved for the containment check, so a component that is a symlink
    to a directory outside the project root is accepted; a dangling or looping
    symlink component raises `ProjectConfigError`. Returns the normalized
    relative path and whether it currently names a directory (following
    symlinks).
    """
    if not user_path.strip():
        raise ProjectConfigError("working_dir must not be empty")

    raw_path = pathlib.Path(user_path).expanduser()
    if raw_path.is_absolute():
        raise ProjectConfigError(WORKING_DIR_ABSOLUTE_MESSAGE)
    if ".." in raw_path.parts:
        raise ProjectConfigError(WORKING_DIR_DOTDOT_MESSAGE)

    resolved_project_root = project_root.resolve()
    check_working_dir_symlinks(resolved_project_root, raw_path)
    relative_path = (
        pathlib.Path(*raw_path.parts) if raw_path.parts else pathlib.Path(".")
    )
    return relative_path, (resolved_project_root / relative_path).is_dir()


def resolve_configured_working_dir(
    project_root: pathlib.Path,
    working_dir: str,
) -> tuple[pathlib.Path, pathlib.Path, bool]:
    """Validate configured working-dir metadata and resolve it under project root."""
    relative_path, working_dir_exists = relative_working_dir_metadata(
        project_root, working_dir
    )
    resolved_working_dir = (project_root.resolve() / relative_path).resolve()
    return relative_path, resolved_working_dir, working_dir_exists


def create_working_dir_metadata_target(
    project_root: pathlib.Path,
    user_path: str,
) -> tuple[str, pathlib.Path, bool]:
    """Create a validated project-root-relative working directory when missing."""
    relative_path, working_dir_exists = relative_working_dir_metadata(
        project_root, user_path
    )
    resolved_working_dir = (project_root.resolve() / relative_path).resolve()
    if resolved_working_dir.exists() and not resolved_working_dir.is_dir():
        raise ProjectConfigError(
            "working_dir target exists but is not a directory: "
            f"{resolved_working_dir}"
        )
    if not working_dir_exists:
        resolved_working_dir.mkdir(parents=True, exist_ok=True)
    return relative_path.as_posix(), resolved_working_dir, not working_dir_exists


def set_working_dir_metadata(
    project_root: pathlib.Path,
    user_path: str,
) -> tuple[str | None, str, bool, bool, list[str]]:
    """Record working-dir metadata for create without creating that directory."""
    config = read_project_config(project_root)
    previous_working_dir = working_dir_from_config(config)
    config, repairs = ensure_minimal_project_config(project_root, config)
    relative_path, working_dir_exists = relative_working_dir_metadata(
        project_root, user_path
    )
    relative_path_text = relative_path.as_posix()

    config_changed = bool(repairs) or previous_working_dir != relative_path_text
    if not config_changed:
        return (
            previous_working_dir,
            relative_path_text,
            working_dir_exists,
            False,
            repairs,
        )

    paths_table = config.get("paths")
    if not isinstance(paths_table, dict):
        paths_table = {}
        config["paths"] = paths_table
    paths_table["working_dir"] = relative_path_text

    write_project_config(project_root, config)
    return (
        previous_working_dir,
        relative_path_text,
        working_dir_exists,
        True,
        repairs,
    )


def scaffold_project_metadata(
    target_dir: pathlib.Path,
) -> dict[str, str | bool | list[str]]:
    """Safely scaffold Taurworks metadata in `target_dir` without overwrite."""
    metadata_dir = target_dir / ".taurworks"
    config_path = metadata_dir / "config.toml"

    warnings: list[str] = []
    missing: list[str] = []
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    found: list[str] = []
    metadata_is_safe_directory = False

    if target_dir.exists() and not target_dir.is_dir():
        warnings.append(f"target path exists but is not a directory: {target_dir}")
        skipped.append(
            "refresh scaffolding skipped because target is not a directory: "
            f"{target_dir}"
        )
        return {
            "target_dir": str(target_dir),
            "changed": False,
            "found": found,
            "missing": missing,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "warnings": warnings,
        }

    if target_dir.exists():
        found.append(f"target directory exists: {target_dir}")
    else:
        missing.append(f"target directory missing: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
        created.append(f"directory: {target_dir}")

    if metadata_dir.exists():
        if metadata_dir.is_symlink():
            warnings.append(
                f"metadata path is a symlink and is not modified for safety: {metadata_dir}"
            )
            skipped.append(f"metadata directory creation skipped: {metadata_dir}")
        elif metadata_dir.is_dir():
            found.append(f"metadata directory exists: {metadata_dir}")
            metadata_is_safe_directory = True
        else:
            warnings.append(
                f"metadata path exists but is not a directory: {metadata_dir}"
            )
            skipped.append(f"metadata directory creation skipped: {metadata_dir}")
    else:
        missing.append(f"metadata directory missing: {metadata_dir}")
        metadata_dir.mkdir(parents=True, exist_ok=True)
        created.append(f"directory: {metadata_dir}")
        metadata_is_safe_directory = True

    if config_path.exists():
        if config_path.is_symlink():
            warnings.append(
                f"config path is a symlink and is not modified for safety: {config_path}"
            )
            skipped.append(f"config file update skipped: {config_path}")
        elif config_path.is_file():
            found.append(f"config exists: {config_path}")
            try:
                config = read_project_config(target_dir)
                updated_config, repairs = ensure_minimal_project_config(
                    target_dir, config
                )
                if repairs:
                    write_project_config(target_dir, updated_config)
                    updated.append(f"config repaired: {config_path}")
                    updated.extend(f"config repair: {repair}" for repair in repairs)
                else:
                    skipped.append(
                        f"config file retained without changes: {config_path}"
                    )
            except (ProjectConfigError, tomllib.TOMLDecodeError) as error:
                warnings.append(f"config file not updated: {error}")
                skipped.append(f"config file update skipped: {config_path}")
        else:
            warnings.append(
                f"config path exists but is not a regular file: {config_path}"
            )
            skipped.append(f"config file update skipped: {config_path}")
    elif metadata_is_safe_directory:
        missing.append(f"config missing: {config_path}")
        config, _ = ensure_minimal_project_config(target_dir, {})
        write_project_config(target_dir, config)
        created.append(f"file: {config_path}")
    else:
        skipped.append(f"config file update skipped: {config_path}")

    changed = bool(created or updated)

    return {
        "target_dir": str(target_dir),
        "changed": changed,
        "found": found,
        "missing": missing,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "warnings": warnings,
    }
