---
execution_id: 2026_11_10_16_21_41_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001)[2026-11-10T06:45:29+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/118
commit: e5114117b0f4204a47e002f0d99a46dc3cabef08
created_at: 2026-11-10T16:21:41+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-WORKING-DIR-REVERSE-DISCOVERY-0001.md
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Created `WI-WORKING-DIR-REVERSE-DISCOVERY-0001` and its design section,
following a `/lrh-design` pass on the PR #117 follow-up. The problem:
cwd-based project discovery fails from inside a symlinked `working_dir`
target. PR: https://github.com/xenotaur/taurworks/pull/118

# Result

- Wrote `project/work_items/proposed/WI-WORKING-DIR-REVERSE-DISCOVERY-0001.md`
  (`deliverable`; depends on the resolved
  `WI-WORKING-DIR-SYMLINK-ESCAPE-0001`).
- Added a `project/design/config_model.md` section, "Discovery from inside a
  symlinked work tree", with status "not yet implemented". The PR #117
  "run it from project_root instead" note now points to it.
- The user chose these in the `/lrh-design` round:
  - Strategy: working_dir reverse lookup only. The physical walk stays
    first; a logical `$PWD` walk is deferred.
  - Include the `working-dir set` mapping through the link in the same WI.
  - Deliverable for this session: the design + WI PR, landed.
    Implementation comes later.
- The user confirmed the drafted WI and design section before they were
  written.
- Fields I inferred, not taken from user answers: `related_focus`,
  `related_roadmap`, the empty `related_workstreams` (this repo has no
  workstreams), `depends_on`, `forbidden_actions`, `artifacts_expected`,
  and the test list.
- Prior-art check: no duplicate found. The only demand is the PR #117
  follow-up notes.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-WORKING-DIR-REVERSE-DISCOVERY-0001`:
  `prompt_ready: yes`, no blocking items or warnings.

# Follow-up

- Implement via `/lrh-execute WI-WORKING-DIR-REVERSE-DISCOVERY-0001`.
- No workstream to update.
