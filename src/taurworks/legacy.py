import pathlib
import re
import shlex
from typing import Any

from taurworks import project_internals

CONDA_ACTIVATE_PATTERN = re.compile(r"^conda\s+activate\s+(\S.*)$")
EXPORT_PATTERN = re.compile(r"^export\s+(\S+?)=(.*)$")
CD_PATTERN = re.compile(r"^cd\s+(\S.*)$")
MESSAGE_PATTERN = re.compile(r"^(?:echo|printf)\s+(\S.*)$")

_UNSAFE_VALUE_MARKERS = ("$", "`", "|", "&", ";", "<", ">", "*", "?", "(", ")")


def legacy_setup_path(project_root: pathlib.Path) -> pathlib.Path:
    """Return the conventional legacy setup script path for a project root."""
    return project_root / "Admin" / "project-setup.source"


def _split_literal_tokens(value: str) -> list[str] | None:
    """Return shell tokens for a literal (non-dynamic) value, or None if unsafe."""
    stripped = value.strip()
    if not stripped:
        return None
    if any(marker in stripped for marker in _UNSAFE_VALUE_MARKERS):
        return None
    try:
        tokens = shlex.split(stripped, posix=True)
    except ValueError:
        return None
    if not tokens:
        return None
    return tokens


def _unsupported(line_number: int, raw_line: str, reason: str) -> dict[str, Any]:
    return {
        "line": line_number,
        "raw": raw_line,
        "kind": "unsupported",
        "detected": {},
        "proposed_config": None,
        "note": reason,
    }


def _unsupported_export(line_number: int, key: str, reason: str) -> dict[str, Any]:
    return {
        "line": line_number,
        "raw": f"export {key}=<redacted>",
        "kind": "unsupported",
        "detected": {"name": key},
        "proposed_config": None,
        "note": reason,
    }


def _classify_line(line_number: int, raw_line: str, stripped: str) -> dict[str, Any]:
    conda_match = CONDA_ACTIVATE_PATTERN.match(stripped)
    if conda_match:
        tokens = _split_literal_tokens(conda_match.group(1))
        if tokens is not None and len(tokens) == 1:
            name = tokens[0]
            return {
                "line": line_number,
                "raw": raw_line,
                "kind": "conda_activate",
                "detected": {"name": name},
                "proposed_config": {
                    "activation": {"environment": {"type": "conda", "name": name}}
                },
                "note": f"Conda environment activation detected: {name}",
            }
        return _unsupported(
            line_number,
            raw_line,
            "conda activate target is not a simple literal name; requires manual review",
        )

    export_match = EXPORT_PATTERN.match(stripped)
    if export_match:
        key, raw_value = export_match.groups()
        tokens = _split_literal_tokens(raw_value)
        if tokens is not None and len(tokens) == 1:
            value = tokens[0]
            try:
                project_internals.validate_activation_export_name(key)
            except project_internals.ProjectConfigError:
                return _unsupported_export(
                    line_number,
                    key,
                    f"export name is not a valid shell environment variable name: {key!r}",
                )
            return {
                "line": line_number,
                "raw": raw_line,
                "kind": "export",
                "detected": {"name": key, "value_redacted": True},
                "proposed_config": {"activation": {"exports": {key: value}}},
                "note": f"Export detected: {key} (value redacted)",
            }
        return _unsupported_export(
            line_number,
            key,
            "export value is not a simple literal (contains shell expansion, "
            "substitution, or multiple tokens); requires manual review",
        )

    cd_match = CD_PATTERN.match(stripped)
    if cd_match:
        tokens = _split_literal_tokens(cd_match.group(1))
        if tokens is not None and len(tokens) == 1:
            path_text = tokens[0]
            return {
                "line": line_number,
                "raw": raw_line,
                "kind": "cd",
                "detected": {"path": path_text},
                "proposed_config": None,
                "note": f"Directory change detected: {path_text}",
            }
        return _unsupported(
            line_number,
            raw_line,
            "cd target is not a simple literal path; requires manual review",
        )

    message_match = MESSAGE_PATTERN.match(stripped)
    if message_match:
        tokens = _split_literal_tokens(message_match.group(1))
        if tokens is not None:
            message = " ".join(tokens)
            return {
                "line": line_number,
                "raw": raw_line,
                "kind": "message",
                "detected": {"message": message},
                "proposed_config": {"activation": {"message": message}},
                "note": "Readiness message detected",
            }
        return _unsupported(
            line_number,
            raw_line,
            "readiness message is not a simple literal; requires manual review",
        )

    return _unsupported(
        line_number,
        raw_line,
        "line does not match a supported pattern; requires manual review",
    )


def parse_legacy_setup_script(text: str) -> list[dict[str, Any]]:
    """Conservatively parse a legacy setup script into classified line matches."""
    matches: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        matches.append(_classify_line(line_number, raw_line, stripped))
    return matches


def gather_legacy_inspect_diagnostics(path_or_name: str | None) -> dict[str, Any]:
    """Collect conservative, read-only legacy setup script inspection data."""
    cwd = pathlib.Path.cwd().resolve()
    resolution = project_internals.resolve_project_target(
        path_or_name, cwd, prefer_project_root=True
    )
    project_root = resolution.project_root
    setup_path = legacy_setup_path(project_root)

    base: dict[str, Any] = {
        "ok": True,
        "cwd": str(cwd),
        "input": resolution.input,
        "project_root": str(project_root),
        "resolved_by": resolution.resolved_by.value,
        "legacy_setup_path": str(setup_path),
        "legacy_setup_exists": setup_path.is_file(),
        "matches": [],
        "supported_count": 0,
        "unsupported_count": 0,
        "message": "",
    }

    if not setup_path.is_file():
        base["ok"] = False
        base["message"] = f"No legacy setup script found at {setup_path}."
        return base

    try:
        text = setup_path.read_text(encoding="utf-8")
    except OSError as error:
        base["ok"] = False
        base["message"] = f"Could not read legacy setup script: {error}"
        return base

    matches = parse_legacy_setup_script(text)
    base["matches"] = matches
    base["supported_count"] = sum(
        1 for match in matches if match["kind"] != "unsupported"
    )
    base["unsupported_count"] = sum(
        1 for match in matches if match["kind"] == "unsupported"
    )
    base["message"] = (
        f"Detected {base['supported_count']} supported pattern(s) and "
        f"{base['unsupported_count']} unsupported line(s) requiring manual review."
    )
    return base


def format_legacy_inspect_output(diagnostics: dict[str, Any]) -> str:
    """Format `legacy inspect` output as stable, redaction-aware text."""
    lines = [
        "Taurworks legacy inspect (read-only)",
        f"- cwd: {diagnostics['cwd']}",
        f"- input: {diagnostics['input']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- resolved_by: {diagnostics['resolved_by']}",
        f"- legacy_setup_path: {diagnostics['legacy_setup_path']}",
        f"- legacy_setup_exists: {diagnostics['legacy_setup_exists']}",
    ]
    if not diagnostics["ok"]:
        lines.append(f"- message: {diagnostics['message']}")
        return "\n".join(lines)

    lines.append(f"- supported_count: {diagnostics['supported_count']}")
    lines.append(f"- unsupported_count: {diagnostics['unsupported_count']}")

    for match in diagnostics["matches"]:
        kind = match["kind"]
        if kind == "export":
            name = match["detected"]["name"]
            lines.append(
                f"- line {match['line']}: export {name}=<redacted> ({match['note']})"
            )
        elif kind == "conda_activate":
            lines.append(
                f"- line {match['line']}: conda activate "
                f"{match['detected']['name']} ({match['note']})"
            )
        elif kind == "cd":
            lines.append(
                f"- line {match['line']}: cd {match['detected']['path']} ({match['note']})"
            )
        elif kind == "message":
            lines.append(f"- line {match['line']}: readiness message ({match['note']})")
        else:
            lines.append(
                f"- line {match['line']}: unsupported — {match['note']}: {match['raw'].strip()}"
            )

    lines.append(f"- message: {diagnostics['message']}")
    return "\n".join(lines)


def _deep_merge_config(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _merge_legacy_matches_into_config(
    project_root: pathlib.Path,
    matches: list[dict[str, Any]],
    existing_config: dict[str, Any],
) -> dict[str, Any]:
    """Compute an unambiguous config patch plus per-field notes; writes nothing."""
    applied: list[str] = []
    skipped: list[str] = []
    manual_review: list[str] = []
    patch: dict[str, Any] = {}

    activation_table = existing_config.get("activation")
    existing_activation = activation_table if isinstance(activation_table, dict) else {}
    existing_environment = existing_activation.get("environment")
    existing_message = existing_activation.get("message")
    existing_exports_table = existing_activation.get("exports")
    existing_exports = (
        existing_exports_table if isinstance(existing_exports_table, dict) else {}
    )
    existing_working_dir = project_internals.working_dir_from_config(existing_config)

    conda_candidates = [m for m in matches if m["kind"] == "conda_activate"]
    if len(conda_candidates) > 1:
        manual_review.append(
            "multiple `conda activate` lines detected (lines "
            f"{[m['line'] for m in conda_candidates]}); ambiguous, not applied automatically"
        )
    elif conda_candidates:
        candidate = conda_candidates[0]
        if existing_environment:
            skipped.append(
                "activation.environment already configured; legacy conda activate "
                f"line left unapplied (line {candidate['line']})"
            )
        else:
            name = candidate["detected"]["name"]
            patch.setdefault("activation", {})["environment"] = {
                "type": "conda",
                "name": name,
            }
            applied.append(
                f"activation.environment.type=conda, name={name} (line {candidate['line']})"
            )

    message_candidates = [m for m in matches if m["kind"] == "message"]
    if len(message_candidates) > 1:
        manual_review.append(
            "multiple readiness message lines detected (lines "
            f"{[m['line'] for m in message_candidates]}); ambiguous, not applied automatically"
        )
    elif message_candidates:
        candidate = message_candidates[0]
        if existing_message:
            skipped.append(
                "activation.message already configured; legacy message left "
                f"unapplied (line {candidate['line']})"
            )
        else:
            message = candidate["detected"]["message"]
            patch.setdefault("activation", {})["message"] = message
            applied.append(f"activation.message set (line {candidate['line']})")

    export_candidates = [m for m in matches if m["kind"] == "export"]
    seen_keys: dict[str, int] = {}
    duplicate_keys: set[str] = set()
    for candidate in export_candidates:
        key = candidate["detected"]["name"]
        if key in seen_keys:
            duplicate_keys.add(key)
        else:
            seen_keys[key] = candidate["line"]

    exports_patch: dict[str, str] = {}
    for candidate in export_candidates:
        key = candidate["detected"]["name"]
        if key in duplicate_keys:
            manual_review.append(
                f"export {key} detected more than once; ambiguous, not applied automatically"
            )
            continue
        if key in existing_exports:
            skipped.append(
                f"activation.exports.{key} already configured; legacy export "
                f"left unapplied (line {candidate['line']})"
            )
            continue
        exports_patch[key] = candidate["proposed_config"]["activation"]["exports"][key]
        applied.append(f"activation.exports.{key} set (line {candidate['line']})")
    if exports_patch:
        patch.setdefault("activation", {})["exports"] = exports_patch

    cd_candidates = [m for m in matches if m["kind"] == "cd"]
    if len(cd_candidates) > 1:
        manual_review.append(
            "multiple `cd` lines detected (lines "
            f"{[m['line'] for m in cd_candidates]}); ambiguous, not applied automatically"
        )
    elif cd_candidates:
        candidate = cd_candidates[0]
        if existing_working_dir:
            skipped.append(
                "paths.working_dir already configured; legacy cd line left "
                f"unapplied (line {candidate['line']})"
            )
        else:
            raw_path = candidate["detected"]["path"]
            try:
                relative_path, exists = project_internals.relative_working_dir_metadata(
                    project_root, raw_path
                )
            except project_internals.ProjectConfigError as error:
                manual_review.append(
                    "legacy cd target could not be mapped to working_dir safely "
                    f"(line {candidate['line']}): {error}"
                )
            else:
                if not exists:
                    manual_review.append(
                        "legacy cd target does not exist under the project root "
                        f"(line {candidate['line']}): {raw_path}"
                    )
                else:
                    patch.setdefault("paths", {})[
                        "working_dir"
                    ] = relative_path.as_posix()
                    applied.append(
                        f"paths.working_dir set to {relative_path.as_posix()} "
                        f"(line {candidate['line']})"
                    )

    for match in matches:
        if match["kind"] == "unsupported":
            manual_review.append(
                f"line {match['line']} requires manual review: {match['note']}"
            )

    return {
        "patch": patch,
        "applied": applied,
        "skipped": skipped,
        "manual_review": manual_review,
    }


def gather_legacy_migrate_diagnostics(
    path_or_name: str | None, *, apply: bool
) -> dict[str, Any]:
    """Collect (and, when `apply` is set, write) an unambiguous legacy migration."""
    inspect_diagnostics = gather_legacy_inspect_diagnostics(path_or_name)
    base = dict(inspect_diagnostics)
    base["apply"] = apply
    base["config_written"] = False
    project_root = pathlib.Path(inspect_diagnostics["project_root"])
    base["config_path"] = str(project_internals.project_config_path(project_root))

    if not inspect_diagnostics["ok"]:
        return base

    try:
        existing_config = project_internals.read_project_config(project_root)
    except (project_internals.ProjectConfigError, OSError) as error:
        base["ok"] = False
        base["message"] = f"Could not read project config: {error}"
        return base

    merge_result = _merge_legacy_matches_into_config(
        project_root, inspect_diagnostics["matches"], existing_config
    )
    base["applied"] = merge_result["applied"]
    base["skipped"] = merge_result["skipped"]
    base["manual_review"] = merge_result["manual_review"]

    if not merge_result["patch"]:
        base["message"] = (
            "No unambiguous legacy patterns to migrate; nothing would change."
        )
        return base

    if not apply:
        base["message"] = (
            "Dry run: no changes written. Re-run with --apply to write the proposed config."
        )
        return base

    try:
        metadata_dir = project_root / ".taurworks"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        merged_config, repairs = project_internals.ensure_minimal_project_config(
            project_root, existing_config
        )
        merged_config = _deep_merge_config(merged_config, merge_result["patch"])
        project_internals.write_project_config(project_root, merged_config)
    except (project_internals.ProjectConfigError, OSError) as error:
        base["ok"] = False
        base["message"] = f"Failed to write project config: {error}"
        return base

    base["config_written"] = True
    base["repairs"] = repairs
    base["message"] = "Applied legacy migration to .taurworks/config.toml."
    return base


def format_legacy_migrate_output(diagnostics: dict[str, Any]) -> str:
    """Format `legacy migrate` output as stable text."""
    mode = "apply" if diagnostics.get("apply") else "dry run"
    lines = [
        f"Taurworks legacy migrate ({mode})",
        f"- cwd: {diagnostics['cwd']}",
        f"- input: {diagnostics['input']}",
        f"- project_root: {diagnostics['project_root']}",
        f"- resolved_by: {diagnostics['resolved_by']}",
        f"- legacy_setup_path: {diagnostics['legacy_setup_path']}",
        f"- legacy_setup_exists: {diagnostics['legacy_setup_exists']}",
        f"- config_path: {diagnostics['config_path']}",
    ]
    if not diagnostics["ok"]:
        lines.append(f"- message: {diagnostics['message']}")
        return "\n".join(lines)

    lines.append(f"- config_written: {diagnostics.get('config_written', False)}")
    applied = diagnostics.get("applied", [])
    skipped = diagnostics.get("skipped", [])
    manual_review = diagnostics.get("manual_review", [])
    lines.append(f"- applied_count: {len(applied)}")
    lines.append(f"- skipped_count: {len(skipped)}")
    lines.append(f"- manual_review_count: {len(manual_review)}")
    for item in applied:
        lines.append(f"- applied: {item}")
    for item in skipped:
        lines.append(f"- skipped: {item}")
    for item in manual_review:
        lines.append(f"- manual_review: {item}")
    lines.append(f"- message: {diagnostics['message']}")
    return "\n".join(lines)
