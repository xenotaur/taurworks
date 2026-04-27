import os
import pathlib


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
        base_dir = pathlib.Path(xdg_config_home).expanduser()
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
        limitation = (
            "No `.taurworks` metadata directory found from current directory to filesystem root."
        )

    return {
        "cwd": str(cwd),
        "project_root_candidate": str(project_root) if project_root else "unresolved",
        "discovery_source": discovery_source,
        "config_path": str(config_candidate),
        "config_exists": config_candidate.exists(),
        "project_metadata_found": metadata_found,
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
