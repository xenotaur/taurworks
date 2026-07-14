---
execution_id: 2026_07_13_22_13_52_WI_LEGACY_BATCH_MIGRATION_0001
prompt_id: PROMPT(WI-LEGACY-BATCH-MIGRATION-0001:WI_LEGACY_BATCH_MIGRATION_0001)[2026-07-13T17:23:13-04:00]
work_item: WI-LEGACY-BATCH-MIGRATION-0001
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/68
commit: 53dcec8
created_at: 2026-07-13T22:13:52-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LEGACY-BATCH-MIGRATION-0001.md
session_transcript: claude-app:149f0939-369e-4d12-afa5-29a079bb476f
---

# Summary

One-time migration of the real legacy `Admin/project-setup.source` projects
to declarative `.taurworks/config.toml`. Added `bin/migrate_legacy_projects.py`
(a preprocessing pass over the existing taurworks parser/merge/writer),
dry-ran it against all discovered legacy projects, reviewed the diffs with the
owner, and applied to all of them.

# Result

Discovery found **11** legacy-admin projects (the WI estimated 12; the
`Imageworks (1)` duplicate the WI worried about no longer exists on disk, so
the wrong-path hazard did not materialize). All 11 were reviewed and applied
per owner decision (apply all 11; migrate Novarc credential as-is with a
follow-up note).

Per-project outcome (env / working_dir / message; all now `initialized`):

- CentaursGuide — CentaursGuide / . / message
- EmbodiedAI — EmbodiedAI / embodied-ai-workshop.github.io / export NODE_OPTIONS
- ImageWorks — ImageWorks / . / message
- LCATS — LCATS / LCATS / message
- LogicalRoboticsHarness — env **LRH** / logical_robotics_harness / message
- Narramorph — Narramorph / narramorph / message
- Novarc — NovarcSwrPilot / SwrPilot / export CREDENTIALS (see follow-up)
- ProsocialRobotics — ProsocialRobotics / . / message
- PythonGames — PygcurseGames / pygcurse/charspace / (no message)
- Taurcode — Taurcode / taurcode / message
- Taxman — Taxman / . / message

Safety verification:
- All 11 `Admin/project-setup.source` files are byte-identical before and
  after (md5 compared); scripts were never executed or modified.
- No existing config value was overwritten (none of the 11 had prior config;
  preservation is also covered by a unit test).
- Command substitution stayed manual-review: EmbodiedAI's
  `export CREDENTIALS=$(realpath ...)` was not migrated.

Acceptance (live, real shell): `tw activate LCATS`, `tw activate Narramorph`,
and `tw activate PythonGames` each switched `$CONDA_DEFAULT_ENV` to the
configured environment and `cd`'d to the configured working dir (nested
`pygcurse/charspace` for PythonGames), printing the readiness message where
configured.

# Validation

- Python 3.11, black 26.3.1, ruff 0.15.12 (matching constraints-dev.txt)
- New files black-clean and ruff-clean (bin script checked directly;
  `scripts/lint` covers `src tests`)
- `scripts/test` — 204 tests OK (193 prior + 11 new)
- `lrh validate` — no new errors (4 known pre-existing `contributors.md`)
- Pre-existing, out-of-scope: `scripts/format --check` flags
  `src/taurworks/manager.py`, identical on origin/master and untouched here.

# Follow-up

Sizing input for **WI-TRUSTED-LEGACY-SOURCING-0001**: all 11 scripts
`source ~/bin/utilities.source` (AWS-login helpers), which is not expressible
declaratively and remains manual-review in every project. So the trust-gated
sourcing item is relevant to the full set unless the owner judges specific
copies to be dead copypasta. Two per-project notes:

- **Novarc**: `CREDENTIALS` migrated as literal `~/Workspace/.../*.pem`.
  taurworks exports values without expanding `~`, whereas the original bash
  expanded it — so the activated value contains a literal `~`. Fix-up options:
  edit to an absolute path in `.taurworks/config.toml`, or move it to a future
  trusted hook. Left as-is per owner decision.
- **LogicalRoboticsHarness**: conda env is `LRH` (not the project name);
  confirm that environment exists before relying on activation.

Next plan step: WI-ACTIVATION-PRODUCERS-0001 (producer-side authoring so new
projects reach the same state via shipped commands).
