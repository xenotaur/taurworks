import pathlib
import tomllib

from taurworks import project_internals


def _nearest_git_root(cwd: pathlib.Path) -> pathlib.Path | None:
    """Return nearest directory with Git metadata using read-only path checks."""
    for candidate in [cwd, *cwd.parents]:
        git_metadata = candidate / ".git"
        if git_metadata.is_dir() or git_metadata.is_file():
            return candidate
    return None


def _configured_working_dir(
    project_root: pathlib.Path | None,
) -> tuple[bool, str, str, bool, str]:
    """Resolve configured Taurworks working_dir metadata without mutating files."""
    if project_root is None:
        return False, "none", "none", False, "no Taurworks project root detected"

    config_path = project_internals.project_config_path(project_root)
    if not config_path.is_file():
        return False, "none", "none", False, "project config not found"

    try:
        config = project_internals.read_project_config(project_root)
        working_dir = project_internals.working_dir_from_config(config)
        if working_dir is None:
            return False, "none", "none", False, "paths.working_dir is not configured"
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
        return (
            False,
            "none",
            "none",
            False,
            f"working_dir could not be read safely: {error}",
        )

    return (
        True,
        relative_working_dir.as_posix(),
        str(resolved_working_dir),
        working_dir_exists,
        "configured working_dir resolved safely inside the project root",
    )


def _is_inside(cwd: pathlib.Path, candidate: str) -> bool:
    """Return whether cwd is inside candidate when candidate is a resolved path."""
    if candidate == "none":
        return False
    try:
        cwd.relative_to(pathlib.Path(candidate))
    except ValueError:
        return False
    return True


def gather_dev_where_diagnostics() -> dict[str, str | bool]:
    """Collect read-only diagnostics for `taurworks dev where`."""
    cwd = pathlib.Path.cwd().resolve()
    project_root = project_internals.find_project_root_candidate(cwd)
    git_root = _nearest_git_root(cwd)
    (
        working_dir_configured,
        working_dir,
        resolved_working_dir,
        working_dir_exists,
        working_dir_message,
    ) = _configured_working_dir(project_root)

    if resolved_working_dir != "none":
        work_directory_guess = resolved_working_dir
        guess_source = "configured Taurworks working_dir"
    elif git_root is not None:
        work_directory_guess = str(git_root)
        guess_source = "nearest .git metadata"
    elif project_root is not None:
        work_directory_guess = str(project_root)
        guess_source = "detected Taurworks project root"
    else:
        work_directory_guess = str(cwd)
        guess_source = "current working directory fallback"

    return {
        "cwd": str(cwd),
        "project_root": str(project_root) if project_root is not None else "unresolved",
        "project_metadata_found": project_root is not None,
        "working_dir_configured": working_dir_configured,
        "working_dir": working_dir,
        "resolved_working_dir": resolved_working_dir,
        "working_dir_exists": working_dir_exists,
        "inside_working_dir": _is_inside(cwd, resolved_working_dir),
        "work_directory_guess": work_directory_guess,
        "work_directory_guess_source": guess_source,
        "git_root_guess": str(git_root) if git_root is not None else "unresolved",
        "working_dir_message": working_dir_message,
        "read_only": True,
        "mutation_performed": False,
    }


def format_dev_where_output(diagnostics: dict[str, str | bool]) -> str:
    """Format `dev where` diagnostics as stable read-only text output."""
    lines = [
        "Taurworks dev workspace diagnostics (read-only)",
        f"- cwd: {diagnostics['cwd']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- project_metadata_found: {diagnostics['project_metadata_found']}",
        f"- working_dir_configured: {diagnostics['working_dir_configured']}",
        f"- working_dir: {diagnostics['working_dir']}",
        f"- resolved_working_dir: {diagnostics['resolved_working_dir']}",
        f"- working_dir_exists: {diagnostics['working_dir_exists']}",
        f"- inside_working_dir: {diagnostics['inside_working_dir']}",
        f"- work_directory_guess: {diagnostics['work_directory_guess']}",
        f"- work_directory_guess_source: {diagnostics['work_directory_guess_source']}",
        f"- git_root_guess: {diagnostics['git_root_guess']}",
        f"- working_dir_message: {diagnostics['working_dir_message']}",
        f"- read_only: {diagnostics['read_only']}",
        "- mutation_performed: False",
    ]
    return "\n".join(lines)


def gather_dev_status_diagnostics() -> dict[str, str | bool]:
    """Collect read-only summary diagnostics for `taurworks dev status`."""
    diagnostics = gather_dev_where_diagnostics()
    diagnostics["detailed_vcs_status"] = "not implemented"
    diagnostics["future_work"] = (
        "Detailed VCS and workflow automation is future work; no git commands were run."
    )
    return diagnostics


def format_dev_status_output(diagnostics: dict[str, str | bool]) -> str:
    """Format minimal `dev status` output without invoking workflow tools."""
    lines = [
        "Taurworks dev status (read-only)",
        f"- cwd: {diagnostics['cwd']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- working_dir: {diagnostics['working_dir']}",
        f"- resolved_working_dir: {diagnostics['resolved_working_dir']}",
        f"- inside_working_dir: {diagnostics['inside_working_dir']}",
        f"- work_directory_guess: {diagnostics['work_directory_guess']}",
        f"- git_root_guess: {diagnostics['git_root_guess']}",
        f"- detailed_vcs_status: {diagnostics['detailed_vcs_status']}",
        f"- read_only: {diagnostics['read_only']}",
        "- mutation_performed: False",
        f"- future_work: {diagnostics['future_work']}",
    ]
    return "\n".join(lines)
