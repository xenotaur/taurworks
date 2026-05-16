import pathlib
import shlex
import tomllib

from taurworks import global_config
from taurworks import manager
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
    """Collect global workspace/registry diagnostics for `taurworks project list`."""
    cwd = pathlib.Path.cwd().resolve()
    discovered_projects = manager.gather_global_projects()

    projects = [
        {
            "name": str(project["name"]),
            "path": str(project["path"]),
            "status": str(project["status"]),
            "source": str(project["source"]),
            "registered": str(project["registered"]),
        }
        for project in discovered_projects
    ]

    return {
        "cwd": str(cwd),
        "discovery_source": "configured workspace direct children plus global project registry",
        "project_count": len(projects),
        "projects": projects,
        "limitations": "Workspace discovery scans only immediate children; recursive scans and script sourcing are not performed.",
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
            lines.append(
                f"  - {project['name']}: {project['path']} "
                f"[{project['status']}; {project['source']}]"
            )
    else:
        lines.append("- projects: none")

    lines.append(f"- limitations: {diagnostics['limitations']}")
    return "\n".join(lines)


def resolve_project_refresh_target(path_or_name: str | None) -> pathlib.Path:
    """Resolve refresh/create target path with path-only legacy semantics."""
    cwd = pathlib.Path.cwd()
    if path_or_name is None:
        return cwd.resolve()

    candidate = pathlib.Path(path_or_name).expanduser()
    if candidate.exists():
        return candidate.resolve()
    return (cwd / candidate).resolve()


def resolve_project_init_target(
    path_or_name: str | None,
) -> project_internals.ProjectResolution:
    """Resolve init targets while preserving no-argument current-dir init."""
    cwd = pathlib.Path.cwd().resolve()
    if path_or_name is None:
        return project_internals.ProjectResolution(
            input="(current working directory)",
            project_root=cwd,
            resolved_by=project_internals.ResolutionReason.DEFAULT_CURRENT_DIRECTORY,
        )
    return project_internals.resolve_project_target(path_or_name, cwd)


def _is_path_like_input(path_or_name: str) -> bool:
    """Return whether activation input is explicitly path-oriented."""
    candidate = pathlib.PurePath(path_or_name)
    return (
        candidate.is_absolute()
        or len(candidate.parts) != 1
        or path_or_name in {".", ".."}
        or path_or_name.startswith(("./", "../"))
    )


def _resolution_reason_for_project(
    project: dict[str, object],
) -> project_internals.ResolutionReason:
    source = str(project.get("source", ""))
    status = str(project["status"])
    if source == manager.PROJECT_SOURCE_REGISTERED:
        return project_internals.ResolutionReason.REGISTERED_PROJECT
    if source == manager.PROJECT_SOURCE_CURRENT:
        return project_internals.ResolutionReason.CURRENT_PROJECT
    if status == manager.PROJECT_STATUS_INITIALIZED:
        return project_internals.ResolutionReason.WORKSPACE_INITIALIZED_PROJECT
    if status == manager.PROJECT_STATUS_LEGACY_ADMIN:
        return project_internals.ResolutionReason.WORKSPACE_LEGACY_ADMIN_PROJECT
    return project_internals.ResolutionReason.WORKSPACE_ONLY_PROJECT


def resolve_global_activation_project(
    path_or_name: str | None,
    cwd: pathlib.Path,
) -> tuple[project_internals.ProjectResolution, dict[str, object]]:
    """Resolve activation using registry, workspace, then current project fallback."""
    display_input = path_or_name or "(current working directory)"

    if path_or_name is not None and not _is_path_like_input(path_or_name):
        registered_project = manager.find_registered_project(path_or_name)
        if registered_project is not None:
            return (
                project_internals.ProjectResolution(
                    input=display_input,
                    project_root=pathlib.Path(str(registered_project["path"])),
                    resolved_by=project_internals.ResolutionReason.REGISTERED_PROJECT,
                ),
                registered_project,
            )

        workspace_project = manager.find_workspace_project(path_or_name)
        if workspace_project is not None:
            return (
                project_internals.ProjectResolution(
                    input=display_input,
                    project_root=pathlib.Path(str(workspace_project["path"])),
                    resolved_by=_resolution_reason_for_project(workspace_project),
                ),
                workspace_project,
            )

    current_project = manager.find_current_project(cwd)
    if current_project is not None:
        current_root = pathlib.Path(str(current_project["path"]))
        current_config_name = project_internals.project_name_from_config(current_root)
        if path_or_name is None or path_or_name in {
            str(current_project["name"]),
            current_config_name,
            current_root.name,
        }:
            reason = project_internals.ResolutionReason.CURRENT_PROJECT
            if path_or_name is not None:
                reason = project_internals.ResolutionReason.CURRENT_PROJECT_NAME
            return (
                project_internals.ProjectResolution(
                    input=display_input,
                    project_root=current_root,
                    resolved_by=reason,
                ),
                current_project,
            )

    if path_or_name is not None and _is_path_like_input(path_or_name):
        resolution = project_internals.resolve_project_target(
            path_or_name,
            cwd,
            prefer_project_root=False,
        )
        project = manager.classify_project_entry(resolution.project_root)
        row = dict(project)
        row["source"] = "path"
        row["registered"] = False
        row["registered_name"] = "none"
        return resolution, row

    unresolved_root = (cwd / (path_or_name or ".")).resolve()
    project = manager.classify_project_entry(unresolved_root)
    row = dict(project)
    row["source"] = "unresolved"
    row["registered"] = False
    row["registered_name"] = "none"
    return (
        project_internals.ProjectResolution(
            input=display_input,
            project_root=unresolved_root,
            resolved_by=project_internals.ResolutionReason.CHILD_PATH,
        ),
        row,
    )


def _project_init_failure_diagnostics(
    resolution: project_internals.ProjectResolution,
    message: str,
    *,
    working_dir_requested: bool,
) -> dict[str, str | bool | list[str]]:
    """Build a stable non-mutating init failure diagnostic payload."""
    project_root = resolution.project_root
    return {
        "ok": False,
        "input": resolution.input,
        "resolved_by": resolution.resolved_by.value,
        "target_dir": str(project_root),
        "config_path": str(project_internals.project_config_path(project_root)),
        "root_exists": project_root.exists(),
        "root_created": False,
        "changed": False,
        "found": [],
        "missing": [],
        "created": [],
        "updated": [],
        "skipped": ["project init skipped because validation failed"],
        "warnings": [message],
        "delegated_command": "project refresh",
        "delegated_target_dir": str(project_root),
        "delegated_changed": False,
        "working_dir_requested": working_dir_requested,
        "previous_working_dir": "none",
        "working_dir": "none",
        "working_dir_exists": False,
        "working_dir_created": False,
        "working_dir_changed": False,
        "working_dir_message": message,
        "working_dir_repairs": [],
    }


def gather_project_init_diagnostics(
    path_or_name: str | None,
    working_dir: str | None = None,
    *,
    create_working_dir: bool = False,
) -> dict[str, str | bool | list[str]]:
    """Initialize existing/current project roots with safe metadata scaffolding."""
    resolution = resolve_project_init_target(path_or_name)
    project_root = resolution.project_root
    if not project_root.exists():
        return _project_init_failure_diagnostics(
            resolution,
            "project init target must be an existing directory; use `taurworks project create` to create a new project root",
            working_dir_requested=working_dir is not None,
        )
    if not project_root.is_dir():
        return _project_init_failure_diagnostics(
            resolution,
            f"project init target exists but is not a directory: {project_root}",
            working_dir_requested=working_dir is not None,
        )

    if working_dir is not None:
        try:
            (
                relative_working_dir,
                working_dir_exists,
            ) = project_internals.relative_working_dir_metadata(
                project_root, working_dir
            )
        except project_internals.ProjectConfigError as error:
            return _project_init_failure_diagnostics(
                resolution,
                str(error),
                working_dir_requested=True,
            )
        resolved_working_dir = (project_root.resolve() / relative_working_dir).resolve()
        if resolved_working_dir.exists() and not resolved_working_dir.is_dir():
            return _project_init_failure_diagnostics(
                resolution,
                "working_dir target exists but is not a directory: "
                f"{resolved_working_dir}",
                working_dir_requested=True,
            )
        if not working_dir_exists and not create_working_dir:
            return _project_init_failure_diagnostics(
                resolution,
                "working_dir target must be an existing directory unless --create-working-dir is supplied",
                working_dir_requested=True,
            )

    diagnostics = gather_project_refresh_diagnostics(str(project_root))
    delegated_target = diagnostics["target_dir"]
    delegated_changed = diagnostics["changed"]

    diagnostics = dict(diagnostics)
    diagnostics["ok"] = True
    diagnostics["input"] = resolution.input
    diagnostics["resolved_by"] = resolution.resolved_by.value
    diagnostics["config_path"] = str(
        project_internals.project_config_path(project_root)
    )
    diagnostics["root_exists"] = True
    diagnostics["root_created"] = False
    diagnostics["delegated_command"] = "project refresh"
    diagnostics["delegated_target_dir"] = delegated_target
    diagnostics["delegated_changed"] = delegated_changed
    diagnostics["working_dir_requested"] = working_dir is not None
    diagnostics["previous_working_dir"] = "none"
    diagnostics["working_dir"] = "none"
    diagnostics["working_dir_exists"] = False
    diagnostics["working_dir_created"] = False
    diagnostics["working_dir_changed"] = False
    diagnostics["working_dir_message"] = (
        "No working_dir requested; metadata left unchanged."
    )
    diagnostics["working_dir_repairs"] = []

    if working_dir is None:
        return diagnostics

    try:
        working_dir_created = False
        if create_working_dir:
            (
                _relative_working_dir,
                _resolved_working_dir,
                working_dir_created,
            ) = project_internals.create_working_dir_metadata_target(
                project_root, working_dir
            )
        (
            previous_working_dir,
            configured_working_dir,
            working_dir_exists,
            working_dir_changed,
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
        diagnostics["warnings"] = [*diagnostics["warnings"], str(error)]
        return diagnostics

    diagnostics["previous_working_dir"] = previous_working_dir or "none"
    diagnostics["working_dir"] = configured_working_dir
    diagnostics["working_dir_exists"] = working_dir_exists or working_dir_created
    diagnostics["working_dir_created"] = working_dir_created
    diagnostics["working_dir_changed"] = working_dir_changed
    if working_dir_changed or working_dir_created:
        diagnostics["changed"] = True
        updated = list(diagnostics["updated"])
        if working_dir_changed:
            updated.append(
                f"config updated: paths.working_dir set to {configured_working_dir}"
            )
            updated.extend(f"config repair: {repair}" for repair in repairs)
        if working_dir_created:
            created = list(diagnostics["created"])
            created.append(f"directory: {project_root / configured_working_dir}")
            diagnostics["created"] = created
        diagnostics["updated"] = updated
    diagnostics["working_dir_message"] = (
        "Working directory metadata recorded; missing directory was created."
        if working_dir_created
        else "Working directory metadata recorded; existing directory was not created."
    )
    diagnostics["working_dir_repairs"] = repairs
    return diagnostics


def format_project_init_output(
    diagnostics: dict[str, str | bool | list[str]],
) -> str:
    """Format init summary output for existing-root initialization."""
    lines = [
        "Taurworks project init summary",
        f"- ok: {diagnostics['ok']}",
        f"- input: {diagnostics['input']}",
        f"- project_root: {diagnostics['target_dir']}",
        f"- resolved_by: {diagnostics['resolved_by']}",
        f"- root_exists: {diagnostics['root_exists']}",
        f"- root_created: {diagnostics['root_created']}",
        f"- config_path: {diagnostics['config_path']}",
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
            f"- working_dir_changed: {diagnostics['working_dir_changed']}",
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


def _default_project_create_target_resolution() -> dict[str, str | bool]:
    """Return stable default create-target diagnostic fields."""
    return {
        "target_selection": "unresolved",
        "target_selection_message": "Project create target has not been resolved.",
        "workspace_root": "none",
        "workspace_root_source": "none",
        "path_argument": "none",
        "local_requested": False,
    }


def _configured_project_create_workspace() -> tuple[pathlib.Path | None, str | None]:
    """Return the configured workspace root or an explanatory error message."""
    try:
        config = global_config.read_config()
        global_config.validate_schema_version(config)
        configured_root = global_config.configured_workspace_root(config)
        if configured_root is None:
            return None, (
                "no configured workspace root; run `taurworks workspace set PATH` "
                "or use `taurworks project create NAME --local`"
            )
        workspace_root = global_config.configured_workspace_root_path(configured_root)
    except (global_config.GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return None, f"configured workspace root is not usable: {error}"

    if not workspace_root.is_dir():
        return None, (
            "configured workspace root is not an existing directory: "
            f"{workspace_root}; run `taurworks workspace set PATH`"
        )
    return workspace_root, None


def _project_create_target_resolution(
    target_selection: str,
    target_selection_message: str,
    *,
    workspace_root: pathlib.Path | None = None,
    workspace_root_source: str = "none",
    path_argument: str | None = None,
    local_requested: bool = False,
) -> dict[str, str | bool]:
    """Build stable create-target diagnostic fields."""
    return {
        "target_selection": target_selection,
        "target_selection_message": target_selection_message,
        "workspace_root": str(workspace_root) if workspace_root is not None else "none",
        "workspace_root_source": workspace_root_source,
        "path_argument": path_argument or "none",
        "local_requested": local_requested,
    }


def _is_within_directory(child: pathlib.Path, parent: pathlib.Path) -> bool:
    """Return whether child is equal to or inside parent after resolution."""
    resolved_child = child.resolve()
    resolved_parent = parent.resolve()
    return (
        resolved_child == resolved_parent or resolved_parent in resolved_child.parents
    )


def _resolve_explicit_project_create_path(path_text: str) -> pathlib.Path:
    """Resolve --path PATH from cwd unless PATH is already absolute."""
    candidate = pathlib.Path(path_text).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (pathlib.Path.cwd() / candidate).resolve()


def _resolve_project_create_target(
    path_or_name: str,
    *,
    explicit_path: str | None,
    local: bool,
) -> tuple[pathlib.Path, dict[str, str | bool], str | None]:
    """Resolve project create target under workspace, local cwd, or explicit path."""
    project_name = _simple_project_name(path_or_name)

    if explicit_path is not None:
        if not explicit_path.strip():
            return (
                pathlib.Path.cwd().resolve(),
                _project_create_target_resolution(
                    "explicit_path",
                    "--path was provided but empty.",
                    path_argument=explicit_path,
                    local_requested=local,
                ),
                "--path must not be empty",
            )
        if project_name is None:
            return (
                pathlib.Path.cwd().resolve(),
                _project_create_target_resolution(
                    "explicit_path",
                    "--path requires NAME to be a bare project name when NAME is supplied.",
                    path_argument=explicit_path,
                    local_requested=local,
                ),
                "--path requires NAME to be a bare project name; do not provide two paths",
            )
        project_root = _resolve_explicit_project_create_path(explicit_path)
        if project_name != project_root.name:
            return (
                project_root,
                _project_create_target_resolution(
                    "explicit_path",
                    "--path target basename must match NAME so NAME is not ignored.",
                    path_argument=explicit_path,
                    local_requested=local,
                ),
                f"--path target basename {project_root.name!r} does not match NAME {project_name!r}",
            )
        resolution = _project_create_target_resolution(
            "explicit_path",
            "Target resolved from explicit --path PATH.",
            path_argument=explicit_path,
            local_requested=local,
        )
        return project_root, resolution, None

    if local:
        if project_name is None:
            return (
                pathlib.Path.cwd().resolve(),
                _project_create_target_resolution(
                    "local",
                    "--local requires NAME to be a bare project name.",
                    local_requested=True,
                ),
                "--local requires a bare NAME and does not accept path-like targets",
            )
        project_root = (pathlib.Path.cwd() / project_name).resolve()
        resolution = _project_create_target_resolution(
            "local",
            "Target resolved from current working directory because --local was supplied.",
            local_requested=True,
        )
        return project_root, resolution, None

    if project_name is None:
        project_root = resolve_project_refresh_target(path_or_name)
        resolution = _project_create_target_resolution(
            "positional_path",
            "Target resolved from explicit path-like positional argument.",
            path_argument=path_or_name,
        )
        return project_root, resolution, None

    workspace_root, workspace_error = _configured_project_create_workspace()
    if workspace_root is None:
        resolution = _project_create_target_resolution(
            "configured_workspace",
            "Bare NAME creation requires a configured workspace root.",
        )
        return pathlib.Path.cwd().resolve() / project_name, resolution, workspace_error

    project_root = (workspace_root / project_name).resolve()
    resolution = _project_create_target_resolution(
        "configured_workspace",
        "Target resolved from configured workspace root plus NAME.",
        workspace_root=workspace_root,
        workspace_root_source="configured",
    )
    return project_root, resolution, None


def _project_create_failure_diagnostics(
    project_root: pathlib.Path,
    message: str,
    *,
    working_dir_requested: bool,
    target_resolution: dict[str, str | bool] | None = None,
) -> dict[str, str | bool | list[str]]:
    """Build a stable non-mutating create failure diagnostic payload."""
    diagnostics: dict[str, str | bool | list[str]] = {
        "ok": False,
        "target_dir": str(project_root),
        "root_created": False,
        "changed": False,
        "found": [],
        "missing": [],
        "created": [],
        "updated": [],
        "skipped": [message],
        "warnings": [message],
        "delegated_command": "project refresh",
        "delegated_target_dir": str(project_root),
        "delegated_changed": False,
        "working_dir_requested": working_dir_requested,
        "previous_working_dir": "none",
        "working_dir": "none",
        "working_dir_exists": False,
        "working_dir_created": False,
        "working_dir_changed": False,
        "working_dir_message": message,
        "working_dir_repairs": [],
    }
    diagnostics.update(_default_project_create_target_resolution())
    if target_resolution is not None:
        diagnostics.update(target_resolution)
    return diagnostics


def _simple_project_name(path_or_name: str) -> str | None:
    """Return a normalized bare project name, or None when input is a path."""
    candidate = pathlib.PurePath(path_or_name)
    if candidate.is_absolute() or len(candidate.parts) != 1:
        return None
    return candidate.name


def _current_project_name(cwd: pathlib.Path) -> str | None:
    """Return the configured current project name when readable."""
    project_root = project_internals.find_project_root_candidate(cwd)
    if project_root is None:
        return None
    try:
        config = project_internals.read_project_config(project_root)
    except (
        OSError,
        project_internals.ProjectConfigError,
        tomllib.TOMLDecodeError,
    ):
        return None
    project_table = config.get("project")
    if not isinstance(project_table, dict):
        return None
    project_name = project_table.get("name")
    if not isinstance(project_name, str) or not project_name.strip():
        return None
    return project_name


def _would_create_same_name_nested_project(
    path_or_name: str, cwd: pathlib.Path
) -> bool:
    """Return whether bare create NAME would create an accidental NAME/NAME root."""
    project_name = _simple_project_name(path_or_name)
    if project_name is None:
        return False
    if cwd.name == project_name:
        return True
    current_project_name = _current_project_name(cwd)
    return current_project_name == project_name


def gather_project_create_diagnostics(
    path_or_name: str | None,
    working_dir: str | None = None,
    *,
    create_working_dir: bool = False,
    nested: bool = False,
    local: bool = False,
    explicit_path: str | None = None,
) -> dict[str, str | bool | list[str]]:
    """Collect safe create actions by delegating to refresh scaffolding logic."""
    if path_or_name is None:
        if explicit_path is not None or local:
            message = "project create requires NAME when --local or --path is supplied"
            return _project_create_failure_diagnostics(
                pathlib.Path.cwd().resolve(),
                message,
                working_dir_requested=working_dir is not None,
                target_resolution=_project_create_target_resolution(
                    "unresolved",
                    message,
                    path_argument=explicit_path,
                    local_requested=local,
                ),
            )
        diagnostics = gather_project_init_diagnostics(
            None, working_dir, create_working_dir=create_working_dir
        )
        diagnostics = dict(diagnostics)
        diagnostics.update(_default_project_create_target_resolution())
        diagnostics["target_selection"] = "compatibility_current_directory"
        diagnostics["target_selection_message"] = (
            "No NAME was supplied; project create used the existing compatibility "
            "alias for current-directory initialization."
        )
        diagnostics["compatibility_alias"] = True
        diagnostics["compatibility_message"] = (
            "project create with no NAME is a compatibility alias; prefer "
            "`taurworks project init` for existing/current directory initialization."
        )
        return diagnostics

    cwd = pathlib.Path.cwd().resolve()
    project_root, target_resolution, target_error = _resolve_project_create_target(
        path_or_name, explicit_path=explicit_path, local=local
    )

    if target_error is not None:
        return _project_create_failure_diagnostics(
            project_root,
            target_error,
            working_dir_requested=working_dir is not None,
            target_resolution=target_resolution,
        )

    is_cwd_relative_same_name = project_root.parent == cwd
    if (
        not nested
        and is_cwd_relative_same_name
        and _would_create_same_name_nested_project(path_or_name, cwd)
    ):
        message = (
            "refusing to create a nested same-name project; use "
            "`taurworks project init` to initialize or repair the current project, "
            "or pass --nested to intentionally create a nested same-name project"
        )
        return _project_create_failure_diagnostics(
            project_root,
            message,
            working_dir_requested=working_dir is not None,
            target_resolution=target_resolution,
        )

    root_existed_before = project_root.exists()

    if working_dir is not None:
        try:
            relative_working_dir, _working_dir_exists = (
                project_internals.relative_working_dir_metadata(
                    project_root, working_dir
                )
            )
        except project_internals.ProjectConfigError as error:
            return _project_create_failure_diagnostics(
                project_root,
                str(error),
                working_dir_requested=True,
                target_resolution=target_resolution,
            )
        resolved_working_dir = (project_root.resolve() / relative_working_dir).resolve()
        if resolved_working_dir.exists() and not resolved_working_dir.is_dir():
            return _project_create_failure_diagnostics(
                project_root,
                "working_dir target exists but is not a directory: "
                f"{resolved_working_dir}",
                working_dir_requested=True,
                target_resolution=target_resolution,
            )
    diagnostics = gather_project_refresh_diagnostics(str(project_root))
    delegated_target = diagnostics["target_dir"]
    delegated_changed = diagnostics["changed"]
    root_created = (
        not root_existed_before and pathlib.Path(str(delegated_target)).is_dir()
    )

    diagnostics = dict(diagnostics)
    diagnostics.update(target_resolution)
    if diagnostics["target_selection"] in {"explicit_path", "positional_path"}:
        workspace_root, _workspace_error = _configured_project_create_workspace()
        if workspace_root is not None and not _is_within_directory(
            project_root, workspace_root
        ):
            diagnostics["warnings"] = [
                *diagnostics["warnings"],
                "created project is outside the configured workspace root; "
                "it will not appear in global project discovery unless registered",
            ]
            diagnostics["workspace_root"] = str(workspace_root)
            diagnostics["workspace_root_source"] = "configured"
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
    diagnostics["working_dir_changed"] = False
    diagnostics["working_dir_message"] = (
        "No working_dir requested; metadata left unchanged."
    )
    diagnostics["working_dir_repairs"] = []

    if working_dir is None:
        return diagnostics

    try:
        working_dir_created = False
        if create_working_dir:
            (
                _relative_working_dir,
                _resolved_working_dir,
                working_dir_created,
            ) = project_internals.create_working_dir_metadata_target(
                project_root, working_dir
            )
        (
            previous_working_dir,
            configured_working_dir,
            working_dir_exists,
            working_dir_changed,
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
        diagnostics["warnings"] = [*diagnostics["warnings"], str(error)]
        return diagnostics

    diagnostics["previous_working_dir"] = previous_working_dir or "none"
    diagnostics["working_dir"] = configured_working_dir
    diagnostics["working_dir_exists"] = working_dir_exists or working_dir_created
    diagnostics["working_dir_created"] = working_dir_created
    diagnostics["working_dir_changed"] = working_dir_changed
    if working_dir_changed or working_dir_created:
        diagnostics["changed"] = True
        updated = list(diagnostics["updated"])
        if working_dir_changed:
            updated.append(
                f"config updated: paths.working_dir set to {configured_working_dir}"
            )
            updated.extend(f"config repair: {repair}" for repair in repairs)
        if working_dir_created:
            created = list(diagnostics["created"])
            created.append(f"directory: {project_root / configured_working_dir}")
            diagnostics["created"] = created
        diagnostics["updated"] = updated
    diagnostics["working_dir_message"] = (
        "Working directory metadata recorded; missing directory was created."
        if working_dir_created
        else "Working directory metadata recorded; directory was not created."
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
        f"- target_selection: {diagnostics['target_selection']}",
        f"- target_selection_message: {diagnostics['target_selection_message']}",
        f"- workspace_root: {diagnostics['workspace_root']}",
        f"- workspace_root_source: {diagnostics['workspace_root_source']}",
        f"- path_argument: {diagnostics['path_argument']}",
        f"- local_requested: {diagnostics['local_requested']}",
        f"- root_created: {diagnostics['root_created']}",
        f"- delegated_command: {diagnostics['delegated_command']}",
        f"- delegated_target_dir: {diagnostics['delegated_target_dir']}",
    ]
    if diagnostics.get("compatibility_alias"):
        lines.append(f"- compatibility_alias: {diagnostics['compatibility_alias']}")
        lines.append(f"- compatibility_message: {diagnostics['compatibility_message']}")
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
            f"- working_dir_changed: {diagnostics['working_dir_changed']}",
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


def gather_project_working_dir_show_diagnostics(
    path_or_name: str | None = None,
) -> dict[str, str | bool]:
    """Collect working-directory metadata for a resolved project context."""
    cwd = pathlib.Path.cwd().resolve()
    resolution = project_internals.resolve_project_target(
        path_or_name,
        cwd,
        prefer_project_root=True,
    )
    project_root = resolution.project_root
    if not (project_root / ".taurworks").is_dir():
        return {
            "ok": False,
            "cwd": str(cwd),
            "input": resolution.input,
            "project_root": str(project_root),
            "resolved_by": resolution.resolved_by.value,
            "config_path": "unresolved",
            "working_dir_configured": False,
            "working_dir": "",
            "message": "No Taurworks project metadata found for the resolved target.",
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
            "input": resolution.input,
            "project_root": str(project_root),
            "resolved_by": resolution.resolved_by.value,
            "config_path": str(config_path),
            "working_dir_configured": False,
            "working_dir": "",
            "message": f"Could not read project config: {error}",
        }

    if working_dir is None:
        return {
            "ok": True,
            "cwd": str(cwd),
            "input": resolution.input,
            "project_root": str(project_root),
            "resolved_by": resolution.resolved_by.value,
            "config_path": str(config_path),
            "working_dir_configured": False,
            "working_dir": "",
            "message": "No working_dir is configured for this project.",
        }

    return {
        "ok": True,
        "cwd": str(cwd),
        "input": resolution.input,
        "project_root": str(project_root),
        "resolved_by": resolution.resolved_by.value,
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
        f"- input: {diagnostics['input']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- resolved_by: {diagnostics['resolved_by']}",
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


def _activation_target_diagnostics(
    base_diagnostics: dict[str, str | bool],
    target_dir: pathlib.Path,
    guidance: str,
    *,
    ok: bool = True,
) -> dict[str, str | bool]:
    base_diagnostics["ok"] = ok
    base_diagnostics["resolved_working_dir"] = str(target_dir)
    base_diagnostics["working_dir_exists"] = target_dir.is_dir()
    base_diagnostics["activation_command"] = f"cd {shlex.quote(str(target_dir))}"
    base_diagnostics["guidance"] = guidance
    return base_diagnostics


def gather_project_activate_print_diagnostics(
    path_or_name: str | None,
) -> dict[str, str | bool]:
    """Collect read-only activation-print diagnostics using global resolution."""
    cwd = pathlib.Path.cwd().resolve()
    resolution, project = resolve_global_activation_project(path_or_name, cwd)
    project_root = resolution.project_root

    config_path = project_internals.project_config_path(project_root)
    config_exists = config_path.is_file()
    project_status = str(project["status"])
    base_diagnostics: dict[str, str | bool] = {
        "ok": True,
        "cwd": str(cwd),
        "input": resolution.input,
        "project_root": str(project_root),
        "project_name": str(project["name"]),
        "resolved_by": resolution.resolved_by.value,
        "source": str(project.get("source", "unknown")),
        "registered": bool(project.get("registered", False)),
        "registered_name": str(project.get("registered_name", "none")),
        "project_status": project_status,
        "config_path": str(config_path),
        "project_metadata_found": (project_root / ".taurworks").is_dir(),
        "activation_config_exists": config_exists,
        "legacy_setup_exists": bool(project["legacy_setup_exists"]),
        "legacy_setup_path": str(project["legacy_setup_path"]),
        "working_dir_configured": False,
        "working_dir": "none",
        "resolved_working_dir": "none",
        "working_dir_exists": False,
        "activation_command": "none",
        "guidance": "",
        "read_only": True,
    }

    if base_diagnostics["source"] == "unresolved":
        base_diagnostics["ok"] = False
        base_diagnostics["guidance"] = (
            "Project name was not found in the global registry, configured workspace, "
            "or current project fallback; use an explicit path for local child directories."
        )
        return base_diagnostics

    if project_status == manager.PROJECT_STATUS_WORKSPACE_ONLY:
        return _activation_target_diagnostics(
            base_diagnostics,
            project_root,
            "Project is not initialized; activation only changes directory to the project root.",
            ok=project_root.is_dir(),
        )

    if project_status == manager.PROJECT_STATUS_LEGACY_ADMIN:
        return _activation_target_diagnostics(
            base_diagnostics,
            project_root,
            "Legacy Admin/project-setup.source exists but was not sourced; activation only changes directory to the project root.",
            ok=project_root.is_dir(),
        )

    if not config_exists:
        base_diagnostics["ok"] = False
        base_diagnostics["guidance"] = (
            "No project config was found. Register an existing root, initialize a "
            "workspace child, or use an explicit path for local path-oriented commands."
        )
        return base_diagnostics

    try:
        config = project_internals.read_project_config(project_root)
        working_dir = project_internals.working_dir_from_config(config)
        if working_dir is None:
            return _activation_target_diagnostics(
                base_diagnostics,
                project_root,
                "No working_dir is configured for this initialized project; activation changes directory to the project root.",
                ok=project_root.is_dir(),
            )

        (
            relative_working_dir,
            resolved_working_dir,
            working_dir_exists,
        ) = project_internals.resolve_configured_working_dir(project_root, working_dir)
    except (
        project_internals.ProjectConfigError,
        OSError,
        tomllib.TOMLDecodeError,
    ) as error:
        base_diagnostics["ok"] = False
        base_diagnostics["guidance"] = (
            "Configured working_dir is invalid or could not be read safely: "
            f"{error}. Run `taurworks project working-dir set [DIR]` "
            "from inside the project to replace it."
        )
        return base_diagnostics

    base_diagnostics["working_dir_configured"] = True
    base_diagnostics["working_dir"] = relative_working_dir.as_posix()
    base_diagnostics["resolved_working_dir"] = str(resolved_working_dir)
    base_diagnostics["working_dir_exists"] = working_dir_exists
    base_diagnostics["activation_command"] = (
        f"cd {shlex.quote(str(resolved_working_dir))}"
    )
    if working_dir_exists:
        base_diagnostics["guidance"] = (
            "Activation guidance is ready. Inspect the command below and run it "
            "manually if you want to change your shell directory."
        )
    else:
        base_diagnostics["guidance"] = (
            "Configured working_dir resolves safely inside the project, but the "
            "directory does not exist. Create it before treating activation as complete."
        )
    return base_diagnostics


def format_project_activate_print_output(
    diagnostics: dict[str, str | bool],
) -> str:
    """Format read-only `project activate --print` diagnostics as stable text."""
    lines = [
        "Taurworks project activation guidance (read-only)",
        f"- cwd: {diagnostics['cwd']}",
        f"- input: {diagnostics['input']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- project_name: {diagnostics['project_name']}",
        f"- resolved_by: {diagnostics['resolved_by']}",
        f"- source: {diagnostics['source']}",
        f"- registered: {diagnostics['registered']}",
        f"- registered_name: {diagnostics['registered_name']}",
        f"- project_status: {diagnostics['project_status']}",
        f"- config_path: {diagnostics['config_path']}",
        f"- project_metadata_found: {diagnostics['project_metadata_found']}",
        f"- activation_config_exists: {diagnostics['activation_config_exists']}",
        f"- legacy_setup_exists: {diagnostics['legacy_setup_exists']}",
        f"- legacy_setup_path: {diagnostics['legacy_setup_path']}",
        f"- working_dir_configured: {diagnostics['working_dir_configured']}",
        f"- working_dir: {diagnostics['working_dir']}",
        f"- resolved_working_dir: {diagnostics['resolved_working_dir']}",
        f"- working_dir_exists: {diagnostics['working_dir_exists']}",
        f"- activation_command: {diagnostics['activation_command']}",
        "- shell_mutation: not performed",
        f"- guidance: {diagnostics['guidance']}",
        "- note: activation_command is printed for inspection only and was not executed",
        "- note: real shell mutation is limited to an explicitly sourced shell wrapper/function such as tw activate",
    ]
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
