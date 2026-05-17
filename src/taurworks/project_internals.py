import dataclasses
import enum
import os
import pathlib
import re
import tomllib
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


@dataclasses.dataclass(frozen=True)
class ProjectResolution:
    """Inspectable result of resolving a project path or name."""

    input: str
    project_root: pathlib.Path
    resolved_by: ResolutionReason


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


def resolve_project_target(
    path_or_name: str | None,
    cwd: pathlib.Path,
    *,
    prefer_project_root: bool = False,
) -> ProjectResolution:
    """Resolve a project target with stable, inspectable precedence rules."""
    resolved_cwd = cwd.resolve()
    display_input = path_or_name or "(current working directory)"
    current_project_root = find_project_root_candidate(resolved_cwd)

    if path_or_name is None:
        if current_project_root is not None:
            return ProjectResolution(
                input=display_input,
                project_root=current_project_root,
                resolved_by=ResolutionReason.CURRENT_PROJECT,
            )
        return ProjectResolution(
            input=display_input,
            project_root=resolved_cwd,
            resolved_by=ResolutionReason.DEFAULT_CURRENT_DIRECTORY,
        )

    if current_project_root is not None:
        current_project_name = project_name_from_config(current_project_root)
        if path_or_name == current_project_name:
            return ProjectResolution(
                input=display_input,
                project_root=current_project_root,
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
            project_root = find_project_root_candidate(search_base)
            if project_root is not None:
                return ProjectResolution(
                    input=display_input,
                    project_root=project_root,
                    resolved_by=ResolutionReason.EXISTING_PATH_PROJECT_ROOT,
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


def working_dir_from_config(config: dict[str, Any]) -> str | None:
    """Return configured working_dir if present and valid enough to display."""
    paths_table = config.get("paths")
    if not isinstance(paths_table, dict):
        return None
    working_dir = paths_table.get("working_dir")
    if not isinstance(working_dir, str) or not working_dir:
        return None
    return working_dir


def relative_working_dir(
    project_root: pathlib.Path,
    cwd: pathlib.Path,
    user_path: str | None,
) -> pathlib.Path:
    """Validate and return a working directory path relative to project root."""
    resolved_project_root = project_root.resolve()
    if user_path is None:
        target_path = cwd.resolve()
    else:
        raw_path = pathlib.Path(user_path).expanduser()
        if raw_path.is_absolute():
            raise ProjectConfigError(
                "working_dir must be relative to the project root; absolute paths are not supported yet"
            )
        target_path = (cwd / raw_path).resolve()

    try:
        relative_path = target_path.relative_to(resolved_project_root)
    except ValueError as error:
        raise ProjectConfigError(
            "working_dir must stay inside the project root and may not escape with '..'"
        ) from error

    if not target_path.is_dir():
        raise ProjectConfigError(
            f"working_dir target must be an existing directory: {target_path}"
        )

    if str(relative_path) == ".":
        return pathlib.Path(".")
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
    relative_path = relative_working_dir(project_root, cwd, user_path)
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
    """Validate working-dir metadata for create without requiring existence."""
    if not user_path.strip():
        raise ProjectConfigError("working_dir must not be empty")

    raw_path = pathlib.Path(user_path).expanduser()
    if raw_path.is_absolute():
        raise ProjectConfigError(
            "working_dir must be relative to the project root; absolute paths are not supported yet"
        )

    resolved_project_root = project_root.resolve()
    target_path = (resolved_project_root / raw_path).resolve()

    try:
        relative_path = target_path.relative_to(resolved_project_root)
    except ValueError as error:
        raise ProjectConfigError(
            "working_dir must stay inside the project root and may not escape with '..'"
        ) from error

    if str(relative_path) == ".":
        return pathlib.Path("."), target_path.is_dir()
    return relative_path, target_path.is_dir()


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
