import pathlib
import tomllib
from typing import Any

from taurworks import global_config

PROJECT_CONFIG_RELATIVE_PATH = pathlib.Path(".taurworks") / "config.toml"


def normalize_project_root(path_text: str) -> pathlib.Path:
    """Expand and resolve a project registry root path."""
    return pathlib.Path(path_text).expanduser().resolve()


def project_config_exists(project_root: pathlib.Path) -> bool:
    """Return whether a project root contains Taurworks project-local config."""
    return (project_root / PROJECT_CONFIG_RELATIVE_PATH).is_file()


def _failure_diagnostics(
    action: str,
    error: str,
    *,
    name: str | None = None,
    project_root: pathlib.Path | str | None = None,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "ok": False,
        "action": action,
        "error": error,
        "config_path": str(global_config.config_path().path),
        "name": name or "none",
        "project_root": str(project_root) if project_root is not None else "none",
        "mutation_performed": False,
    }
    return diagnostics


def _read_valid_config() -> tuple[global_config.GlobalConfigPath, dict[str, Any]]:
    resolved = global_config.config_path()
    config = global_config.read_config(resolved.path)
    global_config.validate_schema_version(config)
    projects_table = config.get("projects")
    if projects_table is not None and not isinstance(projects_table, dict):
        raise global_config.GlobalConfigError(
            "global config [projects] value is not a table"
        )
    return resolved, config


def _registry_table(config: dict[str, Any]) -> dict[str, Any]:
    projects_table = config.get("projects")
    if projects_table is None:
        projects_table = {}
        config["projects"] = projects_table
    if not isinstance(projects_table, dict):
        raise global_config.GlobalConfigError(
            "global config [projects] value is not a table"
        )
    return projects_table


def _project_entry_root(entry: Any, name: str) -> str:
    if not isinstance(entry, dict):
        raise global_config.GlobalConfigError(
            f"global config [projects.{name}] value is not a table"
        )
    root = entry.get("root")
    if not isinstance(root, str) or not root.strip():
        raise global_config.GlobalConfigError(
            f"global config [projects.{name}].root must be a non-empty string"
        )
    return root


def _configured_workspace_root_from_config(
    config: dict[str, Any],
) -> pathlib.Path | None:
    configured_root = global_config.configured_workspace_root(config)
    if configured_root is None:
        return None
    try:
        return global_config.configured_workspace_root_path(configured_root)
    except global_config.GlobalConfigError:
        return None


def _workspace_collision(
    name: str,
    project_root: pathlib.Path,
    workspace_root: pathlib.Path | None,
) -> dict[str, Any]:
    collision: dict[str, Any] = {
        "collision_with_workspace_child": False,
        "workspace_child_root": "none",
    }
    if workspace_root is None:
        return collision

    workspace_child = workspace_root / name
    if workspace_child.exists():
        resolved_child = workspace_child.resolve()
        if resolved_child != project_root:
            collision["collision_with_workspace_child"] = True
            collision["workspace_child_root"] = str(resolved_child)
    return collision


def gather_project_register_diagnostics(
    name: str,
    path_text: str,
    *,
    force: bool = False,
    allow_missing: bool = False,
) -> dict[str, Any]:
    """Register a global project root by name."""
    project_root = normalize_project_root(path_text)
    if not project_root.exists() and not allow_missing:
        return _failure_diagnostics(
            "register",
            f"project root must be an existing directory unless --allow-missing is supplied: {project_root}",
            name=name,
            project_root=project_root,
        )
    if project_root.exists() and not project_root.is_dir():
        return _failure_diagnostics(
            "register",
            f"project root exists but is not a directory: {project_root}",
            name=name,
            project_root=project_root,
        )

    try:
        global_config.validate_bare_toml_key(name)
        resolved, config = _read_valid_config()
        projects_table = _registry_table(config)
        existing_entry = projects_table.get(name)
        existing_root = None
        if existing_entry is not None:
            existing_root = _project_entry_root(existing_entry, name)
            if not force:
                return _failure_diagnostics(
                    "register",
                    "project is already registered; use --force to overwrite",
                    name=name,
                    project_root=project_root,
                ) | {"existing_root": existing_root}
        global_config.write_project_root_preserving_config(
            resolved.path,
            config,
            name,
            project_root,
        )
        workspace_root = _configured_workspace_root_from_config(config)
    except (global_config.GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return _failure_diagnostics(
            "register", str(error), name=name, project_root=project_root
        )

    warnings = []
    if project_root.exists() and not project_config_exists(project_root):
        warnings.append(
            f"project-local config not found: {project_root / PROJECT_CONFIG_RELATIVE_PATH}"
        )
    if allow_missing and not project_root.exists():
        warnings.append("registered path does not currently exist")

    diagnostics: dict[str, Any] = {
        "ok": True,
        "action": "register",
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "name": name,
        "project_root": str(project_root),
        "path_exists": project_root.exists(),
        "project_config_exists": project_config_exists(project_root),
        "overwrote_existing": existing_root is not None,
        "existing_root": existing_root or "none",
        "warnings": warnings,
        "mutation_performed": True,
    }
    diagnostics.update(_workspace_collision(name, project_root, workspace_root))
    return diagnostics


def gather_project_unregister_diagnostics(name: str) -> dict[str, Any]:
    """Remove a global project registry entry without touching project files."""
    try:
        global_config.validate_bare_toml_key(name)
        resolved, config = _read_valid_config()
        projects_table = _registry_table(config)
        existing_entry = projects_table.get(name)
        if existing_entry is None:
            return _failure_diagnostics(
                "unregister",
                f"project is not registered: {name}",
                name=name,
            )
        removed_root = _project_entry_root(existing_entry, name)
        global_config.remove_project_preserving_config(
            resolved.path,
            config,
            name,
        )
    except (global_config.GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return _failure_diagnostics("unregister", str(error), name=name)

    return {
        "ok": True,
        "action": "unregister",
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "name": name,
        "removed_root": removed_root,
        "project_files_deleted": False,
        "mutation_performed": True,
    }


def gather_project_registry_list_diagnostics() -> dict[str, Any]:
    """List global project registry entries without mutating config or projects."""
    try:
        resolved, config = _read_valid_config()
        projects_table = config.get("projects") or {}
        if not isinstance(projects_table, dict):
            raise global_config.GlobalConfigError(
                "global config [projects] value is not a table"
            )
        workspace_root = _configured_workspace_root_from_config(config)
        projects = []
        for name in sorted(projects_table):
            global_config.validate_bare_toml_key(name)
            root_text = _project_entry_root(projects_table[name], name)
            project_root = pathlib.Path(root_text).expanduser()
            if project_root.is_absolute():
                normalized_root = project_root.resolve()
            else:
                raise global_config.GlobalConfigError(
                    f"global config [projects.{name}].root must be absolute"
                )
            entry: dict[str, Any] = {
                "name": name,
                "root": str(normalized_root),
                "path_exists": normalized_root.exists(),
                "project_config_exists": project_config_exists(normalized_root),
            }
            entry.update(_workspace_collision(name, normalized_root, workspace_root))
            projects.append(entry)
    except (global_config.GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return _failure_diagnostics("registry list", str(error))

    return {
        "ok": True,
        "action": "registry list",
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "project_count": len(projects),
        "projects": projects,
        "read_only": True,
        "mutation_performed": False,
    }


def _format_warnings(warnings: list[str]) -> list[str]:
    if not warnings:
        return ["- warnings: none"]
    lines = ["- warnings:"]
    for warning in warnings:
        lines.append(f"  - {warning}")
    return lines


def format_project_register_output(diagnostics: dict[str, Any]) -> str:
    """Format global project registration diagnostics."""
    if not diagnostics["ok"]:
        lines = [
            "Taurworks project register failed",
            f"- error: {diagnostics['error']}",
            f"- name: {diagnostics['name']}",
            f"- config_path: {diagnostics['config_path']}",
            f"- project_root: {diagnostics['project_root']}",
        ]
        if "existing_root" in diagnostics:
            lines.append(f"- existing_root: {diagnostics['existing_root']}")
        lines.append(f"- mutation_performed: {diagnostics['mutation_performed']}")
        return "\n".join(lines)

    lines = [
        "Taurworks project register",
        f"- config_path: {diagnostics['config_path']}",
        f"- xdg_source: {diagnostics['xdg_source']}",
        f"- name: {diagnostics['name']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- path_exists: {diagnostics['path_exists']}",
        f"- project_config_exists: {diagnostics['project_config_exists']}",
        f"- overwrote_existing: {diagnostics['overwrote_existing']}",
        f"- existing_root: {diagnostics['existing_root']}",
        f"- collision_with_workspace_child: {diagnostics['collision_with_workspace_child']}",
        f"- workspace_child_root: {diagnostics['workspace_child_root']}",
    ]
    lines.extend(_format_warnings(diagnostics["warnings"]))
    lines.append(f"- mutation_performed: {diagnostics['mutation_performed']}")
    return "\n".join(lines)


def format_project_unregister_output(diagnostics: dict[str, Any]) -> str:
    """Format global project unregistration diagnostics."""
    if not diagnostics["ok"]:
        return "\n".join(
            [
                "Taurworks project unregister failed",
                f"- error: {diagnostics['error']}",
                f"- name: {diagnostics['name']}",
                f"- config_path: {diagnostics['config_path']}",
                f"- mutation_performed: {diagnostics['mutation_performed']}",
            ]
        )

    return "\n".join(
        [
            "Taurworks project unregister",
            f"- config_path: {diagnostics['config_path']}",
            f"- xdg_source: {diagnostics['xdg_source']}",
            f"- name: {diagnostics['name']}",
            f"- removed_root: {diagnostics['removed_root']}",
            f"- project_files_deleted: {diagnostics['project_files_deleted']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )


def format_project_registry_list_output(diagnostics: dict[str, Any]) -> str:
    """Format global project registry list diagnostics."""
    if not diagnostics["ok"]:
        return "\n".join(
            [
                "Taurworks project registry list failed",
                f"- error: {diagnostics['error']}",
                f"- config_path: {diagnostics['config_path']}",
                f"- mutation_performed: {diagnostics['mutation_performed']}",
            ]
        )

    lines = [
        "Taurworks project registry",
        f"- config_path: {diagnostics['config_path']}",
        f"- xdg_source: {diagnostics['xdg_source']}",
        f"- project_count: {diagnostics['project_count']}",
    ]
    if diagnostics["projects"]:
        lines.append("- projects:")
        for project in diagnostics["projects"]:
            lines.extend(
                [
                    f"  - name: {project['name']}",
                    f"    root: {project['root']}",
                    f"    path_exists: {project['path_exists']}",
                    f"    project_config_exists: {project['project_config_exists']}",
                    f"    collision_with_workspace_child: {project['collision_with_workspace_child']}",
                    f"    workspace_child_root: {project['workspace_child_root']}",
                ]
            )
    else:
        lines.append("- projects: none")
    lines.extend(
        [
            f"- read_only: {diagnostics['read_only']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )
    return "\n".join(lines)
