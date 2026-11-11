---
execution_id: 2026_11_11_03_45_54_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
prompt_id: PROMPT(WI-WORKING-DIR-REVERSE-DISCOVERY-0001:WI_WORKING_DIR_REVERSE_DISCOVERY_0001)[2026-11-11T01:57:48+00:00]
work_item: WI-WORKING-DIR-REVERSE-DISCOVERY-0001
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/119
commit:
created_at: 2026-11-11T03:45:54+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-WORKING-DIR-REVERSE-DISCOVERY-0001.md
session_transcript: pending
---

# Summary

Implemented `WI-WORKING-DIR-REVERSE-DISCOVERY-0001` via `/lrh-execute`. Cwd-
and path-based project discovery now falls back to a working_dir reverse
lookup when the physical walk finds no `.taurworks/`. That lets commands
run from inside a symlinked external working_dir target (for example after
`tw activate`) find their project. PR:
https://github.com/xenotaur/taurworks/pull/119

# Result

- **`manager.find_project_root_for_path`:** physical walk first, then the
  reverse lookup over `gather_global_projects()`. Deepest match wins; a tie
  is ambiguous, carrying its candidates; invalid working_dirs are skipped.
- **`project_internals`:**
  - New `PathDiscovery` and `DiscoverySource` types, plus the
    `ambiguous_discovery_message` guidance helper.
  - `ProjectResolution.candidates` and two new reasons
    (`working_dir_reverse_lookup`, `working_dir_reverse_lookup_ambiguous`).
  - A `discover` hook on `resolve_project_target` for the no-target case,
    the name check and `prefer_project_root` path targets.
  - The `working-dir set` mapping through the link, with the
    last-symlink-component boundary.
- **Callers routed through the shared function:**
  - `dev where`/`status`/workflow commands (`dev.py`)
  - `project where`, `working-dir show`/`set` and the path emitters
    (`project_resolution.py`)
  - `resolve_global_activation_project`, via `find_current_project`'s new
    `(row, discovery)` return
  - env and trust ambiguity checks (`project_resolution.py`) and
    `legacy inspect` (`legacy.py`)
- **Exit codes:** `dev where`/`status` and `project where` exit 1 on
  ambiguity (`cli.py`). The user approved adding `cli.py` when the plan
  diverged.
- **Implementer notes from PR #118, all handled:**
  - `dev` ambiguity: no guess, exit 1, no script fallback.
  - An ambiguous cwd falls through for explicit targets.
  - The ambiguous `project_root` placeholder is documented on
    `ProjectResolution`.
  - `legacy migrate` and `activate --shell` are covered through the shared
    paths.
  - Wording fixes, including `project where`'s limitation text.
- **Unchanged:** `project init`, `project create`'s nested-name guard, the
  `prefer_project_root=False` branch, `tw activate`'s `cd`, and the shell
  helper.
- `config_model.md` status flipped to implemented; README updated.

# Validation

- `scripts/version tools`: Python 3.11.8, black 26.3.1, ruff 0.15.12
- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 393 tests OK
- `lrh validate`: 0 errors, 0 warnings
- Manual dogfood (WI Validation section), with a Workspace project whose
  `working_dir` is a symlink into Tempspace:
  - `tw activate` followed by `taurworks dev where` reported
    `resolved_by: working_dir_reverse_lookup` with the Workspace project
    root.
  - `project where`, `project activate --print`, `project working .` and
    `project root .` from `<target>/sub` all resolved the project.
  - `working-dir set` stored `working_dir/sub`, then `set ..` stored
    `working_dir`, and `set ..` from the target was rejected with the
    link-boundary message.
- Pre-push `/lrh-self-review` diff-mode found nothing blocking. Its
  verified findings were fixed in `b0ab2cc`.

# Follow-up

- Optional docs note: a `working_dir` linked to a broad directory (such as
  `$HOME`) claims every non-project directory under it.
- `project/focus/current_focus.md` and `project/roadmap/roadmap.md` could
  be refreshed after closeout.
