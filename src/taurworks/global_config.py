import dataclasses
import json
import os
import pathlib
import re
import tomllib
from typing import Any

GLOBAL_CONFIG_SCHEMA_VERSION = 1
BARE_TOML_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
TOML_TABLE_HEADER_PATTERN = re.compile(r"^\s*\[+\s*([^\[\]]+?)\s*\]+\s*(?:#.*)?$")
TOML_ROOT_KEY_PATTERN = re.compile(r"^(?P<indent>\s*)root\s*=.*$")


class GlobalConfigError(ValueError):
    """Raised when Taurworks global config cannot be safely read or updated."""


@dataclasses.dataclass(frozen=True)
class GlobalConfigPath:
    """Resolved user-global Taurworks config path and its source."""

    path: pathlib.Path
    source: str


def config_path() -> GlobalConfigPath:
    """Return the XDG-style Taurworks global config path."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        candidate_base_dir = pathlib.Path(xdg_config_home).expanduser()
        if candidate_base_dir.is_absolute():
            return GlobalConfigPath(
                candidate_base_dir / "taurworks" / "config.toml",
                "XDG_CONFIG_HOME",
            )
    return GlobalConfigPath(
        pathlib.Path.home() / ".config" / "taurworks" / "config.toml",
        "default fallback",
    )


def read_config(path: pathlib.Path | None = None) -> dict[str, Any]:
    """Read user-global Taurworks config, returning an empty config if absent."""
    resolved_path = path if path is not None else config_path().path
    if not resolved_path.exists():
        return {}
    if not resolved_path.is_file():
        raise GlobalConfigError(
            f"config path exists but is not a file: {resolved_path}"
        )
    with resolved_path.open("rb") as config_file:
        return tomllib.load(config_file)


def _toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _toml_quote(value)
    raise GlobalConfigError(
        f"unsupported config value type for safe writer: {type(value).__name__}"
    )


def validate_bare_toml_key(key: str) -> None:
    if not isinstance(key, str) or not BARE_TOML_KEY_PATTERN.fullmatch(key):
        raise GlobalConfigError(
            f"unsupported TOML key for safe writer: {key!r}; only bare keys are supported"
        )


def _split_table_items(
    table: dict[str, Any],
) -> tuple[list[tuple[str, Any]], list[tuple[str, dict[str, Any]]]]:
    scalar_items: list[tuple[str, Any]] = []
    nested_table_items: list[tuple[str, dict[str, Any]]] = []
    for key, value in table.items():
        validate_bare_toml_key(key)
        if isinstance(value, dict):
            nested_table_items.append((key, value))
        else:
            scalar_items.append((key, value))
    return scalar_items, nested_table_items


def _append_table_lines(
    lines: list[str],
    table_path: list[str],
    table: dict[str, Any],
) -> None:
    scalar_items, nested_table_items = _split_table_items(table)
    if lines:
        lines.append("")
    lines.append(f"[{'.'.join(table_path)}]")
    for key, value in scalar_items:
        lines.append(f"{key} = {_toml_scalar(value)}")
    for nested_name, nested_table in nested_table_items:
        _append_table_lines(lines, [*table_path, nested_name], nested_table)


def _toml_lines(config: dict[str, Any]) -> list[str]:
    scalar_items, table_items = _split_table_items(config)

    lines: list[str] = []
    for key, value in scalar_items:
        lines.append(f"{key} = {_toml_scalar(value)}")

    for table_name, table in table_items:
        _append_table_lines(lines, [table_name], table)

    return lines


def write_config(config: dict[str, Any], path: pathlib.Path | None = None) -> None:
    """Write user-global Taurworks config using the supported TOML shape."""
    resolved_path = path if path is not None else config_path().path
    if resolved_path.is_symlink():
        raise GlobalConfigError(
            f"config path is a symlink and is not modified for safety: {resolved_path}"
        )
    if resolved_path.parent.is_symlink():
        raise GlobalConfigError(
            f"config directory is a symlink and is not modified for safety: {resolved_path.parent}"
        )
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text("\n".join(_toml_lines(config)) + "\n", encoding="utf-8")


def gather_config_where_diagnostics() -> dict[str, Any]:
    """Gather read-only diagnostics for the global config path."""
    resolved = config_path()
    return {
        "config_path": str(resolved.path),
        "exists": resolved.path.is_file(),
        "xdg_source": resolved.source,
        "read_only": True,
        "mutation_performed": False,
    }


def format_config_where_output(diagnostics: dict[str, Any]) -> str:
    """Format global config path diagnostics."""
    return "\n".join(
        [
            "Taurworks global config",
            f"- config_path: {diagnostics['config_path']}",
            f"- exists: {diagnostics['exists']}",
            f"- xdg_source: {diagnostics['xdg_source']}",
            f"- read_only: {diagnostics['read_only']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )


def configured_workspace_root(config: dict[str, Any]) -> str | None:
    """Return the configured workspace root from global config, if present."""
    workspace_table = config.get("workspace")
    if not isinstance(workspace_table, dict):
        return None
    root = workspace_table.get("root")
    if not isinstance(root, str) or not root.strip():
        return None
    return root


def validate_schema_version(config: dict[str, Any]) -> None:
    schema_version = config.get("schema_version")
    if schema_version is None:
        return
    if schema_version != GLOBAL_CONFIG_SCHEMA_VERSION:
        raise GlobalConfigError(
            "unsupported global config schema_version: "
            f"{schema_version!r}; expected {GLOBAL_CONFIG_SCHEMA_VERSION}"
        )


def normalize_workspace_root(path_text: str) -> pathlib.Path:
    """Expand and resolve a workspace root path for persistent config."""
    return pathlib.Path(path_text).expanduser().resolve()


def configured_workspace_root_path(path_text: str) -> pathlib.Path:
    """Return an absolute configured workspace root path or fail safely."""
    candidate = pathlib.Path(path_text).expanduser()
    if not candidate.is_absolute():
        raise GlobalConfigError(
            "configured workspace root must be absolute; run `taurworks workspace set PATH`"
        )
    return candidate.resolve()


def inferred_workspace_root() -> pathlib.Path | None:
    """Return the non-authoritative first-run workspace inference, if present."""
    candidate = pathlib.Path.home() / "Workspace"
    if candidate.is_dir():
        return candidate.resolve()
    return None


def _config_error_diagnostics(
    resolved: GlobalConfigPath,
    error: Exception,
    *,
    config_exists: bool,
) -> dict[str, Any]:
    return {
        "ok": False,
        "config_path": str(resolved.path),
        "config_exists": config_exists,
        "xdg_source": resolved.source,
        "workspace_root": "none",
        "workspace_root_source": "invalid_config",
        "configured_workspace_root": "none",
        "inferred_workspace_root": "none",
        "error": str(error),
        "read_only": True,
        "mutation_performed": False,
    }


def gather_workspace_show_diagnostics() -> dict[str, Any]:
    """Gather read-only diagnostics for the configured or inferred workspace root."""
    resolved = config_path()
    try:
        config = read_config(resolved.path)
        validate_schema_version(config)
        configured_root = configured_workspace_root(config)
        inferred_root = None
        root_source = "unconfigured"
        workspace_root = None
        if configured_root is not None:
            workspace_root = str(configured_workspace_root_path(configured_root))
            root_source = "configured"
        elif not resolved.path.exists():
            inferred_root_path = inferred_workspace_root()
            if inferred_root_path is not None:
                inferred_root = str(inferred_root_path)
                workspace_root = inferred_root
                root_source = "inferred"
    except (GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return _config_error_diagnostics(
            resolved,
            error,
            config_exists=resolved.path.exists(),
        )

    return {
        "ok": True,
        "config_path": str(resolved.path),
        "config_exists": resolved.path.is_file(),
        "xdg_source": resolved.source,
        "workspace_root": workspace_root or "none",
        "workspace_root_source": root_source,
        "configured_workspace_root": configured_root or "none",
        "inferred_workspace_root": inferred_root or "none",
        "error": "none",
        "read_only": True,
        "mutation_performed": False,
    }


def format_workspace_show_output(diagnostics: dict[str, Any]) -> str:
    """Format workspace root diagnostics."""
    lines = [
        "Taurworks workspace",
        f"- config_path: {diagnostics['config_path']}",
        f"- config_exists: {diagnostics['config_exists']}",
        f"- xdg_source: {diagnostics['xdg_source']}",
        f"- workspace_root: {diagnostics['workspace_root']}",
        f"- workspace_root_source: {diagnostics['workspace_root_source']}",
        f"- configured_workspace_root: {diagnostics['configured_workspace_root']}",
        f"- inferred_workspace_root: {diagnostics['inferred_workspace_root']}",
    ]
    if diagnostics["error"] != "none":
        lines.append(f"- error: {diagnostics['error']}")
    lines.extend(
        [
            f"- read_only: {diagnostics['read_only']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )
    return "\n".join(lines)


def _toml_table_name(line: str) -> str | None:
    match = TOML_TABLE_HEADER_PATTERN.match(line)
    if match is None:
        return None
    return match.group(1).strip()


def _ensure_schema_version_text(config_text: str) -> str:
    if not config_text.strip():
        return f"schema_version = {GLOBAL_CONFIG_SCHEMA_VERSION}\n"
    return f"schema_version = {GLOBAL_CONFIG_SCHEMA_VERSION}\n" + config_text


def _set_workspace_root_in_toml(config_text: str, workspace_root: pathlib.Path) -> str:
    root_line = f"root = {_toml_quote(str(workspace_root))}"
    lines = config_text.splitlines()
    workspace_start = None
    workspace_end = len(lines)
    for index, line in enumerate(lines):
        table_name = _toml_table_name(line)
        if table_name == "workspace":
            workspace_start = index
            continue
        if workspace_start is not None and table_name is not None:
            workspace_end = index
            break

    if workspace_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["[workspace]", root_line])
        return "\n".join(lines) + "\n"

    for index in range(workspace_start + 1, workspace_end):
        match = TOML_ROOT_KEY_PATTERN.match(lines[index])
        if match is not None:
            lines[index] = f"{match.group('indent')}{root_line}"
            return "\n".join(lines) + "\n"

    lines.insert(workspace_end, root_line)
    return "\n".join(lines) + "\n"


def _write_workspace_root_preserving_config(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    workspace_root: pathlib.Path,
) -> bool:
    parent_existed = config_path_to_write.parent.exists()
    if config_path_to_write.is_symlink():
        raise GlobalConfigError(
            f"config path is a symlink and is not modified for safety: {config_path_to_write}"
        )
    if config_path_to_write.parent.is_symlink():
        raise GlobalConfigError(
            "config directory is a symlink and is not modified for safety: "
            f"{config_path_to_write.parent}"
        )

    if config_path_to_write.exists():
        config_text = config_path_to_write.read_text(encoding="utf-8")
    else:
        config_text = ""
    if "schema_version" not in config:
        config_text = _ensure_schema_version_text(config_text)
    updated_text = _set_workspace_root_in_toml(config_text, workspace_root)
    tomllib.loads(updated_text)
    config_path_to_write.parent.mkdir(parents=True, exist_ok=True)
    config_path_to_write.write_text(updated_text, encoding="utf-8")
    return not parent_existed


def _workspace_set_failure(
    error: str,
    workspace_root: pathlib.Path | str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "workspace_root": str(workspace_root),
        "created_config_parent": False,
        "mutation_performed": False,
    }


def gather_workspace_set_diagnostics(path_text: str) -> dict[str, Any]:
    """Set the configured workspace root in user-global Taurworks config."""
    workspace_root = normalize_workspace_root(path_text)
    if not workspace_root.is_dir():
        return _workspace_set_failure(
            f"workspace root must be an existing directory: {workspace_root}",
            workspace_root,
        )

    resolved = config_path()
    try:
        config = read_config(resolved.path)
        validate_schema_version(config)
        workspace_table = config.get("workspace")
        if workspace_table is not None and not isinstance(workspace_table, dict):
            return _workspace_set_failure(
                "global config [workspace] value is not a table",
                workspace_root,
            )
        created_config_parent = _write_workspace_root_preserving_config(
            resolved.path,
            config,
            workspace_root,
        )
    except (GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return _workspace_set_failure(str(error), workspace_root)

    return {
        "ok": True,
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "workspace_root": str(workspace_root),
        "created_config_parent": created_config_parent,
        "mutation_performed": True,
    }


def format_workspace_set_output(diagnostics: dict[str, Any]) -> str:
    """Format workspace set diagnostics."""
    if not diagnostics["ok"]:
        return "\n".join(
            [
                "Taurworks workspace set failed",
                f"- error: {diagnostics['error']}",
                f"- workspace_root: {diagnostics['workspace_root']}",
                f"- mutation_performed: {diagnostics['mutation_performed']}",
            ]
        )
    return "\n".join(
        [
            "Taurworks workspace set",
            f"- config_path: {diagnostics['config_path']}",
            f"- xdg_source: {diagnostics['xdg_source']}",
            f"- workspace_root: {diagnostics['workspace_root']}",
            f"- created_config_parent: {diagnostics['created_config_parent']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )
