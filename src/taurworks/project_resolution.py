import pathlib
import tomllib

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
    working_dir: str | None = None,
) -> dict[str, str | bool | list[str]]:
    """Collect safe create actions by delegating to refresh scaffolding logic."""
    if working_dir is not None:
        preflight_target = resolve_project_refresh_target(path_or_name)
        try:
            project_internals.relative_working_dir_metadata(
                preflight_target, working_dir
            )
        except project_internals.ProjectConfigError as error:
            return {
                "ok": False,
                "target_dir": str(preflight_target),
                "root_created": False,
                "changed": False,
                "found": [],
                "missing": [],
                "created": [],
                "updated": [],
                "skipped": [
                    "project refresh skipped because working_dir validation failed"
                ],
                "warnings": [str(error)],
                "delegated_command": "project refresh",
                "delegated_target_dir": str(preflight_target),
                "delegated_changed": False,
                "working_dir_requested": True,
                "previous_working_dir": "none",
                "working_dir": "none",
                "working_dir_exists": False,
                "working_dir_created": False,
                "working_dir_message": str(error),
                "working_dir_repairs": [],
            }

    diagnostics = gather_project_refresh_diagnostics(path_or_name)
    delegated_target = diagnostics["target_dir"]
    delegated_changed = diagnostics["changed"]
    project_root = pathlib.Path(str(delegated_target))
    root_created = f"directory: {project_root}" in diagnostics["created"]

    diagnostics = dict(diagnostics)
    diagnostics["ok"] = True
    diagnostics["root_created"] = root_created
    diagnostics["delegated_command"] = "project refresh"
    diagnostics["delegated_target_dir"] = delegated_target
    diagnostics["delegated_changed"] = delegated_changed
    diagnostics["working_dir_requested"] = working_dir is not None
    diagnostics["previous_working_dir"] = "none"
    diagnostics["working_dir"] = "none"
    diagnostics["working_dir_exists"] = False
    diagnostics["working_dir_created"] = False
    diagnostics["working_dir_message"] = (
        "No working_dir requested; metadata left unchanged."
    )
    diagnostics["working_dir_repairs"] = []

    if working_dir is None:
        return diagnostics

    try:
        (
            previous_working_dir,
            configured_working_dir,
            working_dir_exists,
            repairs,
        ) = project_internals.set_working_dir_metadata(project_root, working_dir)
    except (
        project_internals.ProjectConfigError,
        OSError,
        tomllib.TOMLDecodeError,
    ) as error:
        diagnostics["ok"] = False
        diagnostics["working_dir"] = "none"
        diagnostics["working_dir_message"] = str(error)
        return diagnostics

    diagnostics["previous_working_dir"] = previous_working_dir or "none"
    diagnostics["working_dir"] = configured_working_dir
    diagnostics["working_dir_exists"] = working_dir_exists
    diagnostics["working_dir_message"] = (
        "Working directory metadata recorded; directory was not created."
    )
    diagnostics["working_dir_repairs"] = repairs
    return diagnostics


def format_project_create_output(
    diagnostics: dict[str, str | bool | list[str]],
) -> str:
    """Format create summary output for the refresh-backed lifecycle command."""
    lines = [
        "Taurworks project create summary",
        f"- ok: {diagnostics['ok']}",
        f"- project_root: {diagnostics['target_dir']}",
        f"- root_created: {diagnostics['root_created']}",
        f"- delegated_command: {diagnostics['delegated_command']}",
        f"- delegated_target_dir: {diagnostics['delegated_target_dir']}",
    ]
    refresh_output = format_project_refresh_output(diagnostics)
    refresh_lines = refresh_output.splitlines()
    lines.extend(refresh_lines[2:])
    lines.extend(
        [
            f"- working_dir_requested: {diagnostics['working_dir_requested']}",
            f"- previous_working_dir: {diagnostics['previous_working_dir']}",
            f"- working_dir: {diagnostics['working_dir']}",
            f"- working_dir_exists: {diagnostics['working_dir_exists']}",
            f"- working_dir_created: {diagnostics['working_dir_created']}",
        ]
    )
    working_dir_repairs = diagnostics["working_dir_repairs"]
    if working_dir_repairs:
        lines.append("- working_dir_repairs:")
        for repair in working_dir_repairs:
            lines.append(f"  - {repair}")
    else:
        lines.append("- working_dir_repairs: none")
    lines.append(f"- working_dir_message: {diagnostics['working_dir_message']}")
    return "\n".join(lines)


def gather_project_refresh_diagnostics(
    path_or_name: str | None,
) -> dict[str, str | bool | list[str]]:
    """Collect safe refresh actions for Taurworks metadata scaffolding."""
    target_dir = resolve_project_refresh_target(path_or_name)
    return project_internals.scaffold_project_metadata(target_dir)


def gather_project_working_dir_show_diagnostics() -> dict[str, str | bool]:
    """Collect working-directory metadata for the current project context."""
    cwd = pathlib.Path.cwd().resolve()
    project_root = project_internals.find_project_root_candidate(cwd)
    if project_root is None:
        return {
            "ok": False,
            "cwd": str(cwd),
            "project_root": "unresolved",
            "config_path": "unresolved",
            "working_dir_configured": False,
            "working_dir": "",
            "message": "No Taurworks project root found from current directory to filesystem root.",
        }

    config_path = project_internals.project_config_path(project_root)
    try:
        config = project_internals.read_project_config(project_root)
        working_dir = project_internals.working_dir_from_config(config)
    except (
        project_internals.ProjectConfigError,
        OSError,
        tomllib.TOMLDecodeError,
    ) as error:
        return {
            "ok": False,
            "cwd": str(cwd),
            "project_root": str(project_root),
            "config_path": str(config_path),
            "working_dir_configured": False,
            "working_dir": "",
            "message": f"Could not read project config: {error}",
        }

    if working_dir is None:
        return {
            "ok": True,
            "cwd": str(cwd),
            "project_root": str(project_root),
            "config_path": str(config_path),
            "working_dir_configured": False,
            "working_dir": "",
            "message": "No working_dir is configured for this project.",
        }

    return {
        "ok": True,
        "cwd": str(cwd),
        "project_root": str(project_root),
        "config_path": str(config_path),
        "working_dir_configured": True,
        "working_dir": working_dir,
        "message": "Configured working_dir found.",
    }


def format_project_working_dir_show_output(diagnostics: dict[str, str | bool]) -> str:
    """Format `project working-dir show` output as stable text."""
    lines = [
        "Taurworks project working directory",
        f"- cwd: {diagnostics['cwd']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- config_path: {diagnostics['config_path']}",
        f"- working_dir_configured: {diagnostics['working_dir_configured']}",
    ]
    if diagnostics["working_dir_configured"]:
        lines.append(f"- working_dir: {diagnostics['working_dir']}")
    else:
        lines.append("- working_dir: none")
    lines.append(f"- message: {diagnostics['message']}")
    return "\n".join(lines)


def gather_project_working_dir_set_diagnostics(
    user_path: str | None,
) -> dict[str, str | bool | list[str]]:
    """Set working-directory metadata for the current project context."""
    cwd = pathlib.Path.cwd().resolve()
    project_root = project_internals.find_project_root_candidate(cwd)
    if project_root is None:
        return {
            "ok": False,
            "cwd": str(cwd),
            "project_root": "unresolved",
            "config_path": "unresolved",
            "input": user_path or "(current working directory)",
            "previous_working_dir": "",
            "working_dir": "",
            "repairs": [],
            "message": "No Taurworks project root found from current directory to filesystem root.",
        }

    config_path = project_internals.project_config_path(project_root)
    try:
        previous_working_dir, working_dir, repairs = project_internals.set_working_dir(
            project_root, cwd, user_path
        )
    except (
        project_internals.ProjectConfigError,
        OSError,
        tomllib.TOMLDecodeError,
    ) as error:
        return {
            "ok": False,
            "cwd": str(cwd),
            "project_root": str(project_root),
            "config_path": str(config_path),
            "input": user_path or "(current working directory)",
            "previous_working_dir": "",
            "working_dir": "",
            "repairs": [],
            "message": str(error),
        }

    return {
        "ok": True,
        "cwd": str(cwd),
        "project_root": str(project_root),
        "config_path": str(config_path),
        "input": user_path or "(current working directory)",
        "previous_working_dir": previous_working_dir or "none",
        "working_dir": working_dir,
        "repairs": repairs,
        "message": "Working directory metadata updated.",
    }


def format_project_working_dir_set_output(
    diagnostics: dict[str, str | bool | list[str]],
) -> str:
    """Format `project working-dir set` output as stable text."""
    lines = [
        "Taurworks project working directory update",
        f"- cwd: {diagnostics['cwd']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- config_path: {diagnostics['config_path']}",
        f"- input: {diagnostics['input']}",
        f"- previous_working_dir: {diagnostics['previous_working_dir']}",
    ]
    if diagnostics["working_dir"]:
        lines.append(f"- working_dir: {diagnostics['working_dir']}")
    else:
        lines.append("- working_dir: none")

    repairs = diagnostics["repairs"]
    if repairs:
        lines.append("- repairs:")
        for repair in repairs:
            lines.append(f"  - {repair}")
    else:
        lines.append("- repairs: none")

    lines.append(f"- ok: {diagnostics['ok']}")
    lines.append(f"- message: {diagnostics['message']}")
    return "\n".join(lines)


def gather_project_activate_print_diagnostics(
    path_or_name: str | None,
) -> dict[str, str | bool]:
    """Collect read-only activation-print diagnostics for a resolved project."""
    cwd = pathlib.Path.cwd().resolve()
    target = project_internals.resolve_project_target(path_or_name, cwd)
    resolved_project = target
    project_root = None
    if path_or_name is None:
        project_root = project_internals.find_project_root_candidate(target)
        if project_root is not None:
            resolved_project = project_root

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

    for key in ["found", "missing", "created", "updated", "skipped", "warnings"]:
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
