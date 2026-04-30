import pathlib

from taurworks import project_internals


def gather_project_where_diagnostics() -> dict[str, str | bool | None]:
    """Collect read-only diagnostics for `taurworks project where`."""
    cwd = pathlib.Path.cwd().resolve()
    project_root = project_internals.find_project_root_candidate(cwd)
    config_candidate = project_internals.config_path_candidate().resolve()

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
    discovered_projects, discovery_source, limitation = (
        project_internals.discover_projects_from_context(cwd)
    )

    projects = [
        {
            "name": project_internals.project_name_from_path(project),
            "path": str(project),
        }
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
    return project_internals.resolve_project_target(path_or_name, pathlib.Path.cwd())


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
    return project_internals.scaffold_project_metadata(target_dir)


def gather_project_activate_print_diagnostics(
    path_or_name: str | None,
) -> dict[str, str | bool]:
    """Collect read-only activation-print diagnostics for a resolved project."""
    cwd = pathlib.Path.cwd().resolve()
    target = project_internals.resolve_project_target(path_or_name, cwd)
    project_root = project_internals.find_project_root_candidate(target)
    resolved_project = project_root if project_root is not None else target
    config_path = resolved_project / ".taurworks" / "config.toml"
    config_exists = config_path.is_file()

    if config_exists:
        activation_command = (
            f'cd "{resolved_project}"'
            "  # then run your environment activation command manually"
        )
        guidance = (
            "Activation hint: project metadata exists. Taurworks only prints guidance "
            "in this slice and does not activate shells automatically."
        )
    else:
        activation_command = ""
        guidance = "No activation target is currently configured for this project."

    return {
        "cwd": str(cwd),
        "input": path_or_name or "(current working directory)",
        "resolved_project": str(resolved_project),
        "project_metadata_found": project_root is not None,
        "activation_config_exists": config_exists,
        "activation_command": activation_command,
        "guidance": guidance,
        "read_only": True,
    }


def format_project_activate_print_output(
    diagnostics: dict[str, str | bool],
) -> str:
    """Format read-only `project activate --print` diagnostics as stable text."""
    lines = [
        "Taurworks project activation guidance (read-only)",
        f"- cwd: {diagnostics['cwd']}",
        f"- input: {diagnostics['input']}",
        f"- resolved_project: {diagnostics['resolved_project']}",
        f"- project_metadata_found: {diagnostics['project_metadata_found']}",
        f"- activation_config_exists: {diagnostics['activation_config_exists']}",
        f"- guidance: {diagnostics['guidance']}",
    ]
    if diagnostics["activation_command"]:
        lines.append(f"- activation_command: {diagnostics['activation_command']}")
    else:
        lines.append("- activation_command: none")

    lines.append("- shell_mutation: not performed")
    lines.append(
        "- note: real shell mutation will require an explicit shell wrapper/function in a later slice"
    )
    return "\n".join(lines)


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
