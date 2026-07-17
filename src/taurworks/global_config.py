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
ACTIVATION_LEGACY_SOURCING_KEY_PATTERN = re.compile(
    r"^(?P<indent>\s*)legacy_sourcing\s*=.*$"
)
TRUST_PATH_KEY_PATTERN = re.compile(r"^(?P<indent>\s*)path\s*=.*$")
TRUST_DIGEST_KEY_PATTERN = re.compile(r"^(?P<indent>\s*)digest\s*=.*$")
TRUST_DIGEST_VALUE_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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
    if scalar_items:
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


def _ensure_global_config_write_is_safe(config_path_to_write: pathlib.Path) -> None:
    if config_path_to_write.is_symlink():
        raise GlobalConfigError(
            f"config path is a symlink and is not modified for safety: {config_path_to_write}"
        )
    if config_path_to_write.parent.is_symlink():
        raise GlobalConfigError(
            "config directory is a symlink and is not modified for safety: "
            f"{config_path_to_write.parent}"
        )


def _read_config_text_for_preserving_write(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    *,
    ensure_schema_version: bool,
) -> str:
    if config_path_to_write.exists():
        config_text = config_path_to_write.read_text(encoding="utf-8")
    else:
        config_text = ""
    if ensure_schema_version and "schema_version" not in config:
        config_text = _ensure_schema_version_text(config_text)
    return config_text


def _project_table_name(project_name: str) -> str:
    validate_bare_toml_key(project_name)
    return f"projects.{project_name}"


def _table_is_child_of(table_name: str, parent_table_name: str) -> bool:
    return table_name.startswith(f"{parent_table_name}.")


def _set_project_root_in_toml(
    config_text: str,
    project_name: str,
    project_root: pathlib.Path,
) -> str:
    target_table = _project_table_name(project_name)
    root_line = f"root = {_toml_quote(str(project_root))}"
    lines = config_text.splitlines()
    project_start = None
    project_end = len(lines)
    for index, line in enumerate(lines):
        table_name = _toml_table_name(line)
        if table_name == target_table:
            project_start = index
            continue
        if project_start is not None and table_name is not None:
            project_end = index
            break

    if project_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"[{target_table}]", root_line])
        return "\n".join(lines) + "\n"

    for index in range(project_start + 1, project_end):
        match = TOML_ROOT_KEY_PATTERN.match(lines[index])
        if match is not None:
            lines[index] = f"{match.group('indent')}{root_line}"
            return "\n".join(lines) + "\n"

    lines.insert(project_end, root_line)
    return "\n".join(lines) + "\n"


def _remove_project_table_from_toml(config_text: str, project_name: str) -> str:
    target_table = _project_table_name(project_name)
    lines = config_text.splitlines()
    kept_lines: list[str] = []
    skipping = False
    for line in lines:
        table_name = _toml_table_name(line)
        if table_name is not None:
            skipping = table_name == target_table or _table_is_child_of(
                table_name, target_table
            )
        if not skipping:
            kept_lines.append(line)
    return "\n".join(kept_lines).rstrip() + "\n"


def write_project_root_preserving_config(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    project_name: str,
    project_root: pathlib.Path,
) -> bool:
    """Set a global project registry root while preserving unrelated TOML text."""
    parent_existed = config_path_to_write.parent.exists()
    _ensure_global_config_write_is_safe(config_path_to_write)
    config_text = _read_config_text_for_preserving_write(
        config_path_to_write,
        config,
        ensure_schema_version=True,
    )
    updated_text = _set_project_root_in_toml(config_text, project_name, project_root)
    tomllib.loads(updated_text)
    config_path_to_write.parent.mkdir(parents=True, exist_ok=True)
    config_path_to_write.write_text(updated_text, encoding="utf-8")
    return not parent_existed


def remove_project_preserving_config(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    project_name: str,
) -> None:
    """Remove a global project registry table while preserving unrelated TOML text."""
    _ensure_global_config_write_is_safe(config_path_to_write)
    config_text = _read_config_text_for_preserving_write(
        config_path_to_write,
        config,
        ensure_schema_version=False,
    )
    updated_text = _remove_project_table_from_toml(config_text, project_name)
    tomllib.loads(updated_text)
    config_path_to_write.parent.mkdir(parents=True, exist_ok=True)
    config_path_to_write.write_text(updated_text, encoding="utf-8")


def _write_workspace_root_preserving_config(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    workspace_root: pathlib.Path,
) -> bool:
    parent_existed = config_path_to_write.parent.exists()
    _ensure_global_config_write_is_safe(config_path_to_write)
    config_text = _read_config_text_for_preserving_write(
        config_path_to_write,
        config,
        ensure_schema_version=True,
    )
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


# --- Tier 1: global legacy-sourcing enable switch --------------------------
#
# Off by default. While off, `tw activate` never sources a legacy setup
# script and never prompts, regardless of any per-project trust record.


def configured_legacy_sourcing_enabled(config: dict[str, Any]) -> bool:
    """Return the Tier 1 legacy-sourcing switch; defaults to disabled."""
    activation_table = config.get("activation")
    if not isinstance(activation_table, dict):
        return False
    return activation_table.get("legacy_sourcing") is True


def _set_activation_legacy_sourcing_in_toml(config_text: str, enabled: bool) -> str:
    value_line = f"legacy_sourcing = {'true' if enabled else 'false'}"
    lines = config_text.splitlines()
    table_start = None
    table_end = len(lines)
    for index, line in enumerate(lines):
        table_name = _toml_table_name(line)
        if table_name == "activation":
            table_start = index
            continue
        if table_start is not None and table_name is not None:
            table_end = index
            break

    if table_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["[activation]", value_line])
        return "\n".join(lines) + "\n"

    for index in range(table_start + 1, table_end):
        match = ACTIVATION_LEGACY_SOURCING_KEY_PATTERN.match(lines[index])
        if match is not None:
            lines[index] = f"{match.group('indent')}{value_line}"
            return "\n".join(lines) + "\n"

    lines.insert(table_end, value_line)
    return "\n".join(lines) + "\n"


def gather_config_legacy_sourcing_show_diagnostics() -> dict[str, Any]:
    """Gather read-only diagnostics for the Tier 1 legacy-sourcing switch."""
    resolved = config_path()
    try:
        config = read_config(resolved.path)
        validate_schema_version(config)
        enabled = configured_legacy_sourcing_enabled(config)
    except (GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return {
            "ok": False,
            "config_path": str(resolved.path),
            "xdg_source": resolved.source,
            "legacy_sourcing_enabled": False,
            "error": str(error),
            "read_only": True,
            "mutation_performed": False,
        }
    return {
        "ok": True,
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "legacy_sourcing_enabled": enabled,
        "error": "none",
        "read_only": True,
        "mutation_performed": False,
    }


def format_config_legacy_sourcing_show_output(diagnostics: dict[str, Any]) -> str:
    """Format Tier 1 legacy-sourcing switch diagnostics."""
    lines = [
        "Taurworks legacy-sourcing switch",
        f"- config_path: {diagnostics['config_path']}",
        f"- legacy_sourcing_enabled: {diagnostics['legacy_sourcing_enabled']}",
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


def gather_config_legacy_sourcing_set_diagnostics(enabled: bool) -> dict[str, Any]:
    """Set the Tier 1 legacy-sourcing switch in user-global Taurworks config."""
    resolved = config_path()
    try:
        config = read_config(resolved.path)
        validate_schema_version(config)
        activation_table = config.get("activation")
        if activation_table is not None and not isinstance(activation_table, dict):
            raise GlobalConfigError("global config [activation] value is not a table")
        _ensure_global_config_write_is_safe(resolved.path)
        config_text = _read_config_text_for_preserving_write(
            resolved.path, config, ensure_schema_version=True
        )
        updated_text = _set_activation_legacy_sourcing_in_toml(config_text, enabled)
        tomllib.loads(updated_text)
        resolved.path.parent.mkdir(parents=True, exist_ok=True)
        resolved.path.write_text(updated_text, encoding="utf-8")
    except (GlobalConfigError, OSError, tomllib.TOMLDecodeError) as error:
        return {
            "ok": False,
            "config_path": str(resolved.path),
            "legacy_sourcing_enabled": enabled,
            "error": str(error),
            "mutation_performed": False,
        }
    return {
        "ok": True,
        "config_path": str(resolved.path),
        "xdg_source": resolved.source,
        "legacy_sourcing_enabled": enabled,
        "error": "none",
        "mutation_performed": True,
    }


def format_config_legacy_sourcing_set_output(diagnostics: dict[str, Any]) -> str:
    """Format Tier 1 legacy-sourcing switch mutation diagnostics."""
    if not diagnostics["ok"]:
        return "\n".join(
            [
                "Taurworks legacy-sourcing switch update failed",
                f"- error: {diagnostics['error']}",
                f"- config_path: {diagnostics['config_path']}",
                f"- mutation_performed: {diagnostics['mutation_performed']}",
            ]
        )
    return "\n".join(
        [
            "Taurworks legacy-sourcing switch update",
            f"- config_path: {diagnostics['config_path']}",
            f"- xdg_source: {diagnostics['xdg_source']}",
            f"- legacy_sourcing_enabled: {diagnostics['legacy_sourcing_enabled']}",
            f"- mutation_performed: {diagnostics['mutation_performed']}",
        ]
    )


# --- Tier 2: per-project trust records --------------------------------------
#
# Stored in a dedicated [trust.NAME] table, never under [projects.NAME]: the
# registry requires every [projects.NAME] entry to have a non-empty `root`
# and iterates all such entries (see project_registry._project_entry_root),
# so a trust-only entry there would break existing registry handling. Trust
# records are written only by explicit `taurworks project trust ...`
# commands, never automatically and never from inside a project directory,
# so arriving project content can never grant itself trust.


def _trust_table_name(project_name: str) -> str:
    validate_bare_toml_key(project_name)
    return f"trust.{project_name}"


def trust_record_from_config(
    config: dict[str, Any], project_name: str
) -> dict[str, str] | None:
    """Return the validated {'path', 'digest'} trust record, or None if absent."""
    trust_table = config.get("trust")
    if trust_table is None:
        return None
    if not isinstance(trust_table, dict):
        raise GlobalConfigError("global config [trust] value is not a table")
    entry = trust_table.get(project_name)
    if entry is None:
        return None
    if not isinstance(entry, dict):
        raise GlobalConfigError(
            f"global config [trust.{project_name}] value is not a table"
        )
    path = entry.get("path")
    digest = entry.get("digest")
    if not isinstance(path, str) or not path.strip():
        raise GlobalConfigError(
            f"global config [trust.{project_name}].path must be a non-empty string"
        )
    if not isinstance(digest, str) or not TRUST_DIGEST_VALUE_PATTERN.fullmatch(digest):
        raise GlobalConfigError(
            f"global config [trust.{project_name}].digest must be a "
            "64-character lowercase hex sha256 digest"
        )
    return {"path": path, "digest": digest}


def _set_trust_record_in_toml(
    config_text: str,
    project_name: str,
    script_path: pathlib.Path,
    digest: str,
) -> str:
    target_table = _trust_table_name(project_name)
    path_line = f"path = {_toml_quote(str(script_path))}"
    digest_line = f"digest = {_toml_quote(digest)}"
    lines = config_text.splitlines()
    table_start = None
    table_end = len(lines)
    for index, line in enumerate(lines):
        table_name = _toml_table_name(line)
        if table_name == target_table:
            table_start = index
            continue
        if table_start is not None and table_name is not None:
            table_end = index
            break

    if table_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"[{target_table}]", path_line, digest_line])
        return "\n".join(lines) + "\n"

    path_set = False
    digest_set = False
    for index in range(table_start + 1, table_end):
        path_match = TRUST_PATH_KEY_PATTERN.match(lines[index])
        if path_match is not None:
            lines[index] = f"{path_match.group('indent')}{path_line}"
            path_set = True
            continue
        digest_match = TRUST_DIGEST_KEY_PATTERN.match(lines[index])
        if digest_match is not None:
            lines[index] = f"{digest_match.group('indent')}{digest_line}"
            digest_set = True

    insertions = []
    if not path_set:
        insertions.append(path_line)
    if not digest_set:
        insertions.append(digest_line)
    if insertions:
        lines[table_end:table_end] = insertions
    return "\n".join(lines) + "\n"


def _remove_trust_table_from_toml(config_text: str, project_name: str) -> str:
    target_table = _trust_table_name(project_name)
    lines = config_text.splitlines()
    kept_lines: list[str] = []
    skipping = False
    for line in lines:
        table_name = _toml_table_name(line)
        if table_name is not None:
            skipping = table_name == target_table or _table_is_child_of(
                table_name, target_table
            )
        if not skipping:
            kept_lines.append(line)
    return "\n".join(kept_lines).rstrip() + "\n"


def write_trust_record_preserving_config(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    project_name: str,
    script_path: pathlib.Path,
    digest: str,
) -> None:
    """Set a project's trust record (script path + sha256 digest)."""
    _ensure_global_config_write_is_safe(config_path_to_write)
    config_text = _read_config_text_for_preserving_write(
        config_path_to_write, config, ensure_schema_version=True
    )
    updated_text = _set_trust_record_in_toml(
        config_text, project_name, script_path, digest
    )
    tomllib.loads(updated_text)
    config_path_to_write.parent.mkdir(parents=True, exist_ok=True)
    config_path_to_write.write_text(updated_text, encoding="utf-8")


def remove_trust_record_preserving_config(
    config_path_to_write: pathlib.Path,
    config: dict[str, Any],
    project_name: str,
) -> None:
    """Remove a project's trust record."""
    _ensure_global_config_write_is_safe(config_path_to_write)
    config_text = _read_config_text_for_preserving_write(
        config_path_to_write, config, ensure_schema_version=False
    )
    updated_text = _remove_trust_table_from_toml(config_text, project_name)
    tomllib.loads(updated_text)
    config_path_to_write.parent.mkdir(parents=True, exist_ok=True)
    config_path_to_write.write_text(updated_text, encoding="utf-8")
