import os
import pathlib


def _project_name_from_path(project_root: pathlib.Path) -> str:
    """Return a stable project display name from a project root path."""
    return project_root.name


def _find_project_root_candidate(cwd: pathlib.Path) -> pathlib.Path | None:
    """Find the nearest directory that contains `.taurworks`."""
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".taurworks").is_dir():
            return candidate
    return None


def _config_path_candidate() -> pathlib.Path:
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


def gather_project_where_diagnostics() -> dict[str, str | bool | None]:
    """Collect read-only diagnostics for `taurworks project where`."""
    cwd = pathlib.Path.cwd().resolve()
    project_root = _find_project_root_candidate(cwd)
    config_candidate = _config_path_candidate().resolve()

    metadata_found = project_root is not None

    if metadata_found:
        discovery_source = "filesystem metadata (.taurworks directory)"
        limitation = "No workspace registry resolution is implemented yet."
    else:
        discovery_source = "none"
        limitation = "No `.taurworks` metadata directory found from current directory to filesystem root."

    return {
        "cwd": str(cwd),
        "project_root_candidate": str(project_root) if project_root else "unresolved",
        "discovery_source": discovery_source,
        "config_path": str(config_candidate),
        "config_exists": config_candidate.exists(),
        "project_metadata_found": metadata_found,
        "limitations": limitation,
    }


def gather_project_list_diagnostics() -> dict[str, str | int | list[dict[str, str]]]:
    """Collect read-only diagnostics for `taurworks project list`."""
    cwd = pathlib.Path.cwd().resolve()
    project_root = _find_project_root_candidate(cwd)

    discovered_projects: list[pathlib.Path] = []
    discovery_source: str
    limitation: str

    if project_root is not None:
        discovery_source = "current context (.taurworks found in current/parent path)"
        limitation = "Global registry/workspace scanning is not implemented yet; reporting current context."
        discovered_projects.append(project_root)
    else:
        discovery_source = "cwd child-directory scan for .taurworks metadata"
        limitation = "Only current working directory and direct children are scanned in this stage."
        discovered_projects.extend(
            sorted(
                (
                    child
                    for child in cwd.iterdir()
                    if child.is_dir() and (child / ".taurworks").is_dir()
                ),
                key=lambda path: path.name,
            )
        )

    projects = [
        {"name": _project_name_from_path(project), "path": str(project)}
        for project in discovered_projects
    ]

    return {
        "cwd": str(cwd),
        "discovery_source": discovery_source,
        "project_count": len(projects),
        "projects": projects,
        "limitations": limitation,
    }


def format_project_where_output(diagnostics: dict[str, str | bool | None]) -> str:
    """Format `project where` diagnostics as stable text output."""
    lines = [
        "Taurworks project resolution diagnostics",
        f"- cwd: {diagnostics['cwd']}",
        f"- project_root_candidate: {diagnostics['project_root_candidate']}",
        f"- discovery_source: {diagnostics['discovery_source']}",
        f"- config_path_candidate: {diagnostics['config_path']}",
        f"- config_path_exists: {diagnostics['config_exists']}",
        f"- project_metadata_found: {diagnostics['project_metadata_found']}",
        f"- limitations: {diagnostics['limitations']}",
    ]
    return "\n".join(lines)


def format_project_list_output(
    diagnostics: dict[str, str | int | list[dict[str, str]]],
) -> str:
    """Format `project list` diagnostics as stable text output."""
    project_entries = diagnostics["projects"]

    lines = [
        "Taurworks project discovery listing",
        f"- cwd: {diagnostics['cwd']}",
        f"- discovery_source: {diagnostics['discovery_source']}",
        f"- project_count: {diagnostics['project_count']}",
    ]

    if project_entries:
        lines.append("- projects:")
        for project in project_entries:
            lines.append(f"  - {project['name']}: {project['path']}")
    else:
        lines.append("- projects: none")

    lines.append(f"- limitations: {diagnostics['limitations']}")
    return "\n".join(lines)


def resolve_project_refresh_target(path_or_name: str | None) -> pathlib.Path:
    """Resolve refresh target path using simple where-compatible rules."""
    if path_or_name is None:
        return pathlib.Path.cwd().resolve()

    candidate = pathlib.Path(path_or_name).expanduser()
    if candidate.exists():
        return candidate.resolve()

    return (pathlib.Path.cwd() / candidate).resolve()


def gather_project_create_diagnostics(
    path_or_name: str | None,
) -> dict[str, str | bool | list[str]]:
    """Collect safe create actions by delegating to refresh scaffolding logic."""
    diagnostics = gather_project_refresh_diagnostics(path_or_name)
    delegated_target = diagnostics["target_dir"]
    delegated_changed = diagnostics["changed"]

    diagnostics = dict(diagnostics)
    diagnostics["delegated_command"] = "project refresh"
    diagnostics["delegated_target_dir"] = delegated_target
    diagnostics["delegated_changed"] = delegated_changed
    return diagnostics


def format_project_create_output(
    diagnostics: dict[str, str | bool | list[str]],
) -> str:
    """Format create summary output for the refresh-backed lifecycle command."""
    lines = [
        "Taurworks project create summary",
        f"- target_dir: {diagnostics['target_dir']}",
        f"- delegated_command: {diagnostics['delegated_command']}",
        f"- delegated_target_dir: {diagnostics['delegated_target_dir']}",
    ]
    refresh_output = format_project_refresh_output(diagnostics)
    refresh_lines = refresh_output.splitlines()
    return "\n".join(lines + refresh_lines[2:])


def gather_project_refresh_diagnostics(
    path_or_name: str | None,
) -> dict[str, str | bool | list[str]]:
    """Collect safe refresh actions for Taurworks metadata scaffolding."""
    target_dir = resolve_project_refresh_target(path_or_name)
    metadata_dir = target_dir / ".taurworks"
    config_path = metadata_dir / "config.toml"

    warnings: list[str] = []
    missing: list[str] = []
    created: list[str] = []
    skipped: list[str] = []
    found: list[str] = []

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
        else:
            warnings.append(
                f"metadata path exists but is not a directory: {metadata_dir}"
            )
            skipped.append(f"metadata directory creation skipped: {metadata_dir}")
    else:
        missing.append(f"metadata directory missing: {metadata_dir}")
        metadata_dir.mkdir(parents=True, exist_ok=True)
        created.append(f"directory: {metadata_dir}")

    if config_path.exists():
        if config_path.is_symlink():
            warnings.append(
                f"config path is a symlink and is not modified for safety: {config_path}"
            )
            skipped.append(f"config file update skipped: {config_path}")
        elif config_path.is_file():
            found.append(f"config exists: {config_path}")
            skipped.append(f"config file retained without changes: {config_path}")
        else:
            warnings.append(
                f"config path exists but is not a regular file: {config_path}"
            )
            skipped.append(f"config file update skipped: {config_path}")
    elif metadata_dir.is_dir():
        missing.append(f"config missing: {config_path}")
        config_path.write_text(
            '# Taurworks project metadata\n[project]\nname = ""\n',
            encoding="utf-8",
        )
        created.append(f"file: {config_path}")

    changed = bool(created)

    return {
        "target_dir": str(target_dir),
        "changed": changed,
        "found": found,
        "missing": missing,
        "created": created,
        "skipped": skipped,
        "warnings": warnings,
    }


def format_project_refresh_output(
    diagnostics: dict[str, str | bool | list[str]],
) -> str:
    """Format refresh summary output with safety/idempotence signals."""
    lines = [
        "Taurworks project refresh summary",
        f"- target_dir: {diagnostics['target_dir']}",
        f"- changed: {diagnostics['changed']}",
    ]

    for key in ["found", "missing", "created", "skipped", "warnings"]:
        entries = diagnostics[key]
        if entries:
            lines.append(f"- {key}:")
            for entry in entries:
                lines.append(f"  - {entry}")
        else:
            lines.append(f"- {key}: none")

    if not diagnostics["changed"] and not diagnostics["warnings"]:
        lines.append("- result: no changes needed")
    elif diagnostics["warnings"]:
        lines.append("- result: warnings present; review skipped items")

    return "\n".join(lines)
