import os
import pathlib


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


def scaffold_project_metadata(
    target_dir: pathlib.Path,
) -> dict[str, str | bool | list[str]]:
    """Safely scaffold Taurworks metadata in `target_dir` without overwrite."""
    metadata_dir = target_dir / ".taurworks"
    config_path = metadata_dir / "config.toml"

    warnings: list[str] = []
    missing: list[str] = []
    created: list[str] = []
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
            skipped.append(f"config file retained without changes: {config_path}")
        else:
            warnings.append(
                f"config path exists but is not a regular file: {config_path}"
            )
            skipped.append(f"config file update skipped: {config_path}")
    elif metadata_is_safe_directory:
        missing.append(f"config missing: {config_path}")
        config_path.write_text(
            '# Taurworks project metadata\n[project]\nname = ""\n',
            encoding="utf-8",
        )
        created.append(f"file: {config_path}")
    else:
        skipped.append(f"config file update skipped: {config_path}")

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
