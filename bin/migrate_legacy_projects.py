#!/usr/bin/env python3
"""One-time migration of legacy Admin/project-setup.source projects.

WI-LEGACY-BATCH-MIGRATION-0001. This is a bespoke, run-once tool, not a
general matcher upgrade: it exists to move a known, finite set of personal
legacy projects onto declarative ``.taurworks/config.toml`` activation data.

The shipped ``taurworks legacy migrate`` matcher rejects the variable
indirection these scripts use (``ENVIRONMENT=X; conda activate $ENVIRONMENT;
cd $WORKSPACE``). This script adds a conservative *preprocessing* pass that
resolves script-local ``NAME=value`` assignments and expands a leading ``~``
or ``$HOME``, then hands the normalized lines to the existing, reviewed
Taurworks parser, merge, and safe-writer code. It never executes a legacy
script, never modifies one, and never overwrites an existing config value.

Usage::

    # Dry run (default): print a proposed-config diff for every legacy project.
    PYTHONPATH=src python bin/migrate_legacy_projects.py

    # Apply to all discovered legacy projects.
    PYTHONPATH=src python bin/migrate_legacy_projects.py --apply

    # Apply to only the reviewed/approved subset.
    PYTHONPATH=src python bin/migrate_legacy_projects.py --apply \
        --project LCATS --project Taxman
"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys
import tempfile

from taurworks import legacy
from taurworks import manager
from taurworks import project_internals

# A value we are willing to resolve contains only literal text, a leading
# ``~``, and ``$VAR`` / ``${VAR}`` references. Anything else (command
# substitution, pipes, globs, redirection) means "not a simple literal" and
# the assignment is left unresolved so downstream classification treats the
# dependent line as manual review.
_UNSAFE_MARKERS = ("`", "|", "&", ";", "<", ">", "*", "?", "(", ")")
_ASSIGNMENT_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_REFERENCE_PATTERN = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)"
)
# Lines whose arguments we rewrite with resolved values before handing them
# to the Taurworks parser. Export values are intentionally passed through
# untouched so their handling stays identical to the shipped migrate tool.
_REWRITABLE_PATTERN = re.compile(r"^(conda\s+activate|cd|echo|printf)\s")


def _strip_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "\"'":
        return stripped[1:-1]
    return stripped


def _expand_references(text: str, symbols: dict[str, str]) -> str | None:
    """Substitute known ``$VAR``/``${VAR}`` references; None if any is unknown."""
    unresolved = False

    def replace(match: re.Match[str]) -> str:
        nonlocal unresolved
        name = match.group(1) or match.group(2)
        if name in symbols:
            return symbols[name]
        unresolved = True
        return match.group(0)

    result = _REFERENCE_PATTERN.sub(replace, text)
    if unresolved:
        return None
    return result


def _expand_leading_tilde(text: str, home: pathlib.Path) -> str:
    if text == "~":
        return str(home)
    if text.startswith("~/"):
        return str(home) + text[1:]
    return text


def _resolve_value(raw: str, symbols: dict[str, str], home: pathlib.Path) -> str | None:
    """Resolve an assignment RHS to a literal, or None if not safely literal."""
    value = _strip_quotes(raw)
    if not value or "$(" in value or any(marker in value for marker in _UNSAFE_MARKERS):
        return None
    expanded = _expand_references(value, symbols)
    if expanded is None:
        return None
    expanded = _expand_leading_tilde(expanded, home)
    # A surviving ``$`` means an expansion we do not model; refuse it.
    if "$" in expanded:
        return None
    return expanded


def build_symbol_table(text: str, home: pathlib.Path) -> dict[str, str]:
    """Collect resolvable ``NAME=value`` assignments in source order.

    ``$HOME`` is seeded so references to it resolve. Assignments whose value
    is not a simple literal are skipped, which leaves any dependent line to be
    classified as manual review rather than guessed at.
    """
    symbols: dict[str, str] = {"HOME": str(home)}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("export ", "local ", "declare ", "readonly ")):
            continue
        match = _ASSIGNMENT_PATTERN.match(stripped)
        if not match:
            continue
        name, raw_value = match.groups()
        resolved = _resolve_value(raw_value, symbols, home)
        if resolved is not None:
            symbols[name] = resolved
    return symbols


def preprocess_script(text: str, home: pathlib.Path) -> str:
    """Normalize a legacy script for the Taurworks parser.

    Consumed ``NAME=value`` assignment lines are dropped (the parser ignores
    them anyway). ``conda activate`` / ``cd`` / ``echo`` / ``printf`` lines
    have their known references and a leading ``~`` resolved. Every other line
    (``export``, ``source``, unknown constructs) passes through verbatim so it
    is classified exactly as the shipped tool would classify it.
    """
    symbols = build_symbol_table(text, home)
    out_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped and not stripped.startswith("#"):
            assignment = _ASSIGNMENT_PATTERN.match(stripped)
            is_bare_assignment = assignment is not None and not stripped.startswith(
                ("export ", "local ", "declare ", "readonly ")
            )
            if is_bare_assignment:
                continue
            if _REWRITABLE_PATTERN.match(stripped):
                expanded = _expand_references(stripped, symbols)
                if expanded is not None:
                    if expanded.split(" ", 1)[0] == "cd":
                        _, _, argument = expanded.partition(" ")
                        expanded = f"cd {_expand_leading_tilde(argument.strip(), home)}"
                    out_lines.append(expanded)
                    continue
        out_lines.append(raw_line)
    return "\n".join(out_lines) + "\n"


def _render_config_text(
    project_root: pathlib.Path,
    existing_config: dict[str, object],
    patch: dict[str, object],
) -> str:
    """Render the config that apply would write, using the real safe writer."""
    proposed, _ = project_internals.ensure_minimal_project_config(
        project_root, existing_config
    )
    proposed = legacy._deep_merge_config(proposed, patch)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = pathlib.Path(tmp_dir)
        (tmp_root / ".taurworks").mkdir(parents=True, exist_ok=True)
        project_internals.write_project_config(tmp_root, proposed)
        return project_internals.project_config_path(tmp_root).read_text(
            encoding="utf-8"
        )


def plan_project(project_root: pathlib.Path, home: pathlib.Path) -> dict[str, object]:
    """Compute the proposed migration for one legacy project without writing."""
    admin_script = project_root / "Admin" / "project-setup.source"
    text = admin_script.read_text(encoding="utf-8")
    normalized = preprocess_script(text, home)
    matches = legacy.parse_legacy_setup_script(normalized)
    existing_config = project_internals.read_project_config(project_root)
    merge = legacy._merge_legacy_matches_into_config(
        project_root, matches, existing_config
    )
    config_path = project_internals.project_config_path(project_root)
    existing_text = (
        config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    )
    proposed_text = (
        _render_config_text(project_root, existing_config, merge["patch"])
        if merge["patch"]
        else existing_text
    )
    diff = "".join(
        difflib.unified_diff(
            existing_text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile=f"{config_path} (before)",
            tofile=f"{config_path} (after)",
        )
    )
    return {
        "project_root": project_root,
        "config_path": config_path,
        "patch": merge["patch"],
        "applied": merge["applied"],
        "skipped": merge["skipped"],
        "manual_review": merge["manual_review"],
        "existing_text": existing_text,
        "proposed_text": proposed_text,
        "diff": diff,
    }


def apply_plan(plan: dict[str, object]) -> None:
    """Write the planned config using the real safe writer; never overwrites."""
    project_root = plan["project_root"]
    existing_config = project_internals.read_project_config(project_root)
    metadata_dir = project_root / ".taurworks"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    merged, _ = project_internals.ensure_minimal_project_config(
        project_root, existing_config
    )
    merged = legacy._deep_merge_config(merged, plan["patch"])
    project_internals.write_project_config(project_root, merged)


def discover_legacy_projects(workspace: pathlib.Path) -> list[dict[str, object]]:
    return sorted(
        (
            entry
            for entry in manager.discover_workspace_projects(workspace)
            if entry["status"] == manager.PROJECT_STATUS_LEGACY_ADMIN
        ),
        key=lambda entry: str(entry["name"]),
    )


def _print_plan(plan: dict[str, object], name: str) -> None:
    print(f"\n===== {name} =====")
    print(f"project_root: {plan['project_root']}")
    if not plan["patch"]:
        print("proposed: nothing to migrate (no unambiguous patterns detected)")
    else:
        print("applied:")
        for item in plan["applied"]:
            print(f"  + {item}")
    if plan["skipped"]:
        print("skipped (existing values preserved):")
        for item in plan["skipped"]:
            print(f"  = {item}")
    if plan["manual_review"]:
        print("manual review:")
        for item in plan["manual_review"]:
            print(f"  ? {item}")
    if plan["diff"]:
        print("diff:")
        print(plan["diff"], end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write proposed config (default is a dry run that only prints diffs).",
    )
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        metavar="NAME",
        help="Limit to the named project(s); repeatable. Default is all legacy projects.",
    )
    parser.add_argument(
        "--workspace",
        type=pathlib.Path,
        default=None,
        help="Workspace root to scan (default: the configured Taurworks workspace).",
    )
    args = parser.parse_args(argv)

    workspace = (
        args.workspace if args.workspace is not None else manager.workspace_path()
    )
    workspace = pathlib.Path(workspace).expanduser()
    home = pathlib.Path.home()

    if not workspace.is_dir():
        print(f"error: workspace does not exist: {workspace}", file=sys.stderr)
        return 2

    projects = discover_legacy_projects(workspace)
    if args.projects:
        wanted = set(args.projects)
        projects = [p for p in projects if str(p["name"]) in wanted]
        missing = wanted - {str(p["name"]) for p in projects}
        for name in sorted(missing):
            print(f"warning: no legacy-admin project named {name!r}", file=sys.stderr)

    mode = "apply" if args.apply else "dry run"
    print(f"Taurworks legacy batch migration ({mode})")
    print(f"workspace: {workspace}")
    print(f"legacy projects: {len(projects)}")

    would_write = 0
    written = 0
    for entry in projects:
        name = str(entry["name"])
        project_root = pathlib.Path(str(entry["path"]))
        plan = plan_project(project_root, home)
        _print_plan(plan, name)
        if not plan["patch"]:
            continue
        would_write += 1
        if args.apply:
            apply_plan(plan)
            written += 1
            print(f"written: {plan['config_path']}")

    print("\n===== summary =====")
    if args.apply:
        print(f"config files written: {written}")
    else:
        print(f"projects with a proposed config: {would_write}")
        print(
            "re-run with --apply (optionally --project NAME) to write approved configs"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
