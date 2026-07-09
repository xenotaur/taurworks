---
execution_id: 2026_07_08_13_37_09_WI_LEGACY_CONDA_GATING
prompt_id: PROMPT(WI-LEGACY-CONDA-GATING-0001:WI_LEGACY_CONDA_GATING)[2026-07-08T13:17:50-04:00]
work_item: WI-LEGACY-CONDA-GATING-0001
status: landed
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/63
commit: e9c9bf6dc43af620813662fc10fb3fe896e41a37
created_at: 2026-07-08T13:37:09-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LEGACY-CONDA-GATING-0001.md
session_transcript: claude-app:8d50d14e-57c6-4894-b351-2d95ae102df3
---

# Summary

Gate legacy top-level `taurworks refresh`/`taurworks create` (and `tw
refresh`/`tw create`) from creating a Conda environment by default, and work
through the low-risk remaining follow-ups from the 2026-05-17 side-effect
audit (`project/audits/side_effects.md`).

# Result

- `src/taurworks/manager.py`: added a `create_env: bool = False` parameter to
  `refresh_project` and `create_project`. `create_conda_environment` (and the
  inline Conda-create block in `create_project`) is now only invoked when
  `create_env=True`; the default path prints a skip message and leaves
  repository-directory creation and the `.taurworks/project-setup.source`
  write unchanged.
- `src/taurworks/cli.py`: added a `--create-env` flag to the legacy `create`
  and `refresh` subparsers, threaded through to `manager.create_project` /
  `manager.refresh_project`, and updated both subcommands' `description` text
  to document the new opt-in default.
- `tests/manager_test.py`: added four tests covering the default (no Conda
  subprocess call, skip message printed, metadata still created) and the
  explicit `create_env=True` opt-in path (Conda create command invoked with
  expected args) for both `refresh_project` and `create_project`.
- `project/audits/side_effects.md`: annotated each "Follow-up recommendations"
  item with status — #2 (Conda gating) marked resolved; #1 (metadata-only
  refresh) marked partially addressed (Conda-only; directory/setup-script
  writes deliberately unchanged, see Non-Goals/Open Questions in the work
  item); #3, #4, #5 marked already satisfied by current behavior; #6 (`eval`
  surface in `tw activate`) marked reviewed with a decision to keep it as-is,
  since both `eval` calls operate only on Taurworks-generated,
  validated/quoted data and a safer replacement is a larger, compatibility-
  sensitive change (per this item's Risk Notes); #7 marked partially
  satisfied by the existing `scripts/audit-side-effects` helper.
- Reviewed `src/taurworks/resources/shell/taurworks-shell.sh` per required
  change #4; no code change made (see rationale above and in the audit doc).

# Validation

- `scripts/format --check --diff` — clean (24 files unchanged after one
  reformat applied during development)
- `scripts/lint` — Black + Ruff, all checks passed
- `scripts/test` — 170 tests, OK
- `lrh validate` — 4 errors / 1 warning, all pre-existing on `master`
  (`contributors/contributors.md` missing required fields; orphaned active
  work item warning for `WI-ACTIVATION-CONFIG-0001`) and confirmed identical
  before this branch's changes via `git stash`; no new errors introduced by
  this work item (see `project_lrh_cli_path.md` / contributors.md gap noted
  in prior session memory — pre-existing, needs real data not fabrication,
  out of scope here)
- Manual smoke test: `taurworks create SmokeTest` with an isolated
  `TAURWORKS_WORKSPACE` skipped Conda creation by default while still
  creating the project/repo directories and `.taurworks/project-setup.source`
  script; `taurworks create --help` / `taurworks refresh --help` show the new
  `--create-env` flag

# Follow-up

- Open Question from the work item: whether a follow-up item should pursue
  full metadata-only `refresh`/`create` (audit recommendation #1 in full),
  removing/gating repository-directory creation and the
  `.taurworks/project-setup.source` write too. Deliberately deferred.
- Wiring `scripts/audit-side-effects` into CI as an enforced gate (audit
  follow-up #7) remains open.
- `session_transcript` is `pending`; update to `claude-app:<session-id>` once
  the session ID is known.
