import dataclasses
import os
import pathlib

from taurworks import shell_resources

TL_SOURCE_FILENAME = "tl.source"


@dataclasses.dataclass(frozen=True)
class ResolvedSetupPath:
    """A resolved setup target path and which precedence tier produced it."""

    path: pathlib.Path
    source: str


def resolve_shell_helper_path() -> ResolvedSetupPath:
    """Resolve the shell-helper target path.

    Precedence matches `tw shell refresh`'s own resolution (kept in sync in
    `_tw_shell_refresh`, `src/taurworks/resources/shell/taurworks-shell.sh`):
    `TAURWORKS_SHELL_HELPER_PATH` (any value) takes precedence, then a valid
    absolute `XDG_CONFIG_HOME`, then the `~/.config` fallback.
    """
    override = os.environ.get("TAURWORKS_SHELL_HELPER_PATH")
    if override:
        return ResolvedSetupPath(
            pathlib.Path(override).expanduser(), "TAURWORKS_SHELL_HELPER_PATH"
        )

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        candidate_base_dir = pathlib.Path(xdg_config_home).expanduser()
        if candidate_base_dir.is_absolute():
            return ResolvedSetupPath(
                candidate_base_dir / "taurworks" / "taurworks-shell.sh",
                "XDG_CONFIG_HOME",
            )

    return ResolvedSetupPath(
        pathlib.Path.home() / ".config" / "taurworks" / "taurworks-shell.sh",
        "default fallback",
    )


def resolve_tl_source_path(shell_helper_path: pathlib.Path) -> pathlib.Path:
    """Resolve the `tl` source file's target path.

    `tl`'s packaged source file lives alongside the shell helper, in the
    same config directory, so it shares the shell helper's resolved
    location rather than needing its own override variable.
    """
    return shell_helper_path.parent / TL_SOURCE_FILENAME


def _write_if_changed(path: pathlib.Path, content: str) -> str:
    """Write `content` to `path` only if missing or different.

    Returns one of "created", "updated", or "unchanged".
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") == content:
            return "unchanged"
        path.write_text(content, encoding="utf-8")
        return "updated"
    path.write_text(content, encoding="utf-8")
    return "created"


def gather_setup_diagnostics() -> dict:
    """Perform (idempotent) `taurworks setup` and collect a truth-first summary."""
    shell_helper_resolved = resolve_shell_helper_path()
    tl_source_path = resolve_tl_source_path(shell_helper_resolved.path)

    shell_helper_status = _write_if_changed(
        shell_helper_resolved.path, shell_resources.read_shell_helper_text()
    )
    tl_source_status = _write_if_changed(
        tl_source_path, shell_resources.read_tl_source_text()
    )

    created = []
    updated = []
    unchanged = []
    status_buckets = {"created": created, "updated": updated, "unchanged": unchanged}
    for label, path, status in (
        ("shell helper", shell_helper_resolved.path, shell_helper_status),
        ("tl source", tl_source_path, tl_source_status),
    ):
        status_buckets[status].append(f"{label}: {path}")

    return {
        "shell_helper_path": str(shell_helper_resolved.path),
        "shell_helper_path_source": shell_helper_resolved.source,
        "tl_source_path": str(tl_source_path),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "warnings": [],
        "changed": bool(created or updated),
        "source_lines": [
            f"source {shell_helper_resolved.path}",
            f"source {tl_source_path}",
        ],
    }


def format_setup_output(diagnostics: dict) -> str:
    """Format `taurworks setup`'s truth-first summary output."""
    lines = [
        "Taurworks setup summary",
        f"- shell_helper_path: {diagnostics['shell_helper_path']} (via {diagnostics['shell_helper_path_source']})",
        f"- tl_source_path: {diagnostics['tl_source_path']}",
        f"- changed: {diagnostics['changed']}",
    ]

    for key in ["created", "updated", "unchanged", "warnings"]:
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

    lines.append("")
    lines.append(
        "Add these lines to your shell startup file (e.g. ~/.bashrc) to enable tw and tl:"
    )
    lines.append("")
    lines.extend(diagnostics["source_lines"])

    return "\n".join(lines)
