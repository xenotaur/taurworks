import os
import pathlib
import tomllib
from typing import Any

PROJECT_SCHEMA_VERSION = 1


class ProjectConfigError(ValueError):
    """Raised when Taurworks project config cannot be safely updated."""


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


def resolve_project_target(path_or_name: str | None, cwd: pathlib.Path) -> pathlib.Path:
    """Resolve refresh/create target path using where-compatible rules."""
    if path_or_name is None:
        return cwd.resolve()

    candidate = pathlib.Path(path_or_name).expanduser()
    if candidate.exists():
        return candidate.resolve()

    return (cwd / candidate).resolve()


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


def _toml_lines(config: dict[str, Any]) -> list[str]:
    scalar_items: list[tuple[str, Any]] = []
    table_items: list[tuple[str, dict[str, Any]]] = []
    for key, value in config.items():
        if isinstance(value, dict):
            table_items.append((key, value))
        else:
            scalar_items.append((key, value))

    lines: list[str] = []
    for key, value in scalar_items:
        lines.append(f"{key} = {_toml_scalar(value)}")

    for table_name, table in table_items:
        if lines:
            lines.append("")
        lines.append(f"[{table_name}]")
        for key, value in table.items():
            if isinstance(value, dict):
                raise ProjectConfigError(
                    f"unsupported nested config table for safe writer: {table_name}.{key}"
                )
            lines.append(f"{key} = {_toml_scalar(value)}")

    return lines


def write_project_config(project_root: pathlib.Path, config: dict[str, Any]) -> None:
    """Write project-local Taurworks config using the small supported TOML shape."""
    config_path = project_config_path(project_root)
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

    if updated_config.get("schema_version") != PROJECT_SCHEMA_VERSION:
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
