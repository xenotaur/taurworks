import dataclasses
import os
import pathlib
import re
import tomllib
from typing import Any

GLOBAL_CONFIG_SCHEMA_VERSION = 1
BARE_TOML_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


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
    with resolved_path.open("rb") as config_file:
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
    raise GlobalConfigError(
        f"unsupported config value type for safe writer: {type(value).__name__}"
    )


def _validate_bare_toml_key(key: str) -> None:
    if not isinstance(key, str) or not BARE_TOML_KEY_PATTERN.fullmatch(key):
        raise GlobalConfigError(
            f"unsupported TOML key for safe writer: {key!r}; only bare keys are supported"
        )


def _toml_lines(config: dict[str, Any]) -> list[str]:
    scalar_items: list[tuple[str, Any]] = []
    table_items: list[tuple[str, dict[str, Any]]] = []
    for key, value in config.items():
        _validate_bare_toml_key(key)
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
            _validate_bare_toml_key(key)
            if isinstance(value, dict):
                raise GlobalConfigError(
                    f"unsupported nested config table for safe writer: {table_name}.{key}"
                )
            lines.append(f"{key} = {_toml_scalar(value)}")

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


def normalize_workspace_root(path_text: str) -> pathlib.Path:
    """Expand and resolve a workspace root path for persistent config."""
    return pathlib.Path(path_text).expanduser().resolve()


def inferred_workspace_root() -> pathlib.Path | None:
    """Return the non-authoritative first-run workspace inference, if present."""
    candidate = pathlib.Path.home() / "Workspace"
    if candidate.is_dir():
        return candidate.resolve()
    return None


def gather_workspace_show_diagnostics() -> dict[str, Any]:
    """Gather read-only diagnostics for the configured or inferred workspace root."""
    resolved = config_path()
    config = read_config(resolved.path)
    configured_root = configured_workspace_root(config)
    inferred_root = None
    root_source = "unconfigured"
    workspace_root = None
    if configured_root is not None:
        workspace_root = str(normalize_workspace_root(configured_root))
        root_source = "configured"
    elif not resolved.path.exists():
        inferred_root_path = inferred_workspace_root()
        if inferred_root_path is not None:
            inferred_root = str(inferred_root_path)
            workspace_root = inferred_root
            root_source = "inferred"

    return {
        "config_path": str(resolved.path),
        "config_exists": resolved.path.is_file(),
        "xdg_source": resolved.source,
        "workspace_root": workspace_root or "none",
        "workspace_root_source": root_source,
        "configured_workspace_root": configured_root or "none",
        "inferred_workspace_root": inferred_root or "none",
        "read_only": True,
        "mutation_performed": False,
    }


def format_workspace_show_output(diagnostics: dict[str, Any]) -> str:
    """Format workspace root diagnostics."""
    return "\n".join(
        [
            "Taurworks workspace",
            f"- config_path: {diagnostics['config_path']}",
            f"- config_exists: {diagnostics['config_exists']}",
            f"- xdg_source: {diagnostics['xdg_source']}",
            f"- workspace_root: {diagnostics['workspace_root']}",
            f"- workspace_root_source: {diagnostics['workspace_root_source']}",
            f"- configured_workspace_root: {diagnostics['configured_workspace_root']}",
            f"- inferred_workspace_root: {diagnostics['inferred_workspace_root']}",
            f"- read_only: {diagnostics['read_only']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )


def gather_workspace_set_diagnostics(path_text: str) -> dict[str, Any]:
    """Set the configured workspace root in user-global Taurworks config."""
    workspace_root = normalize_workspace_root(path_text)
    if not workspace_root.is_dir():
        return {
            "ok": False,
            "error": f"workspace root must be an existing directory: {workspace_root}",
            "workspace_root": str(workspace_root),
            "mutation_performed": False,
        }

    resolved = config_path()
    config = read_config(resolved.path)
    updated_config = dict(config)
    workspace_table = updated_config.get("workspace")
    if workspace_table is None:
        workspace_table = {}
    if not isinstance(workspace_table, dict):
        return {
            "ok": False,
            "error": "global config [workspace] value is not a table",
            "workspace_root": str(workspace_root),
            "mutation_performed": False,
        }
    updated_workspace_table = dict(workspace_table)
    updated_workspace_table["root"] = str(workspace_root)
    updated_config["workspace"] = updated_workspace_table
    if "schema_version" not in updated_config:
        updated_config["schema_version"] = GLOBAL_CONFIG_SCHEMA_VERSION
    write_config(updated_config, resolved.path)
    return {
        "ok": True,
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "workspace_root": str(workspace_root),
        "created_config_parent": True,
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
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )
