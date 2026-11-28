---
execution_id: 2026_11_25_17_20_38_WI_CONFIG_WRITER_NEWLINE_0001
prompt_id: PROMPT(AD_HOC:WI_CONFIG_WRITER_NEWLINE_0001)[2026-11-24T02:57:37+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/123
commit:
created_at: 2026-11-25T17:20:38+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CONFIG-WRITER-NEWLINE-0001.md
session_transcript: claude-app:f9407266-89e8-437f-8a64-a4a8cf46d0bf
---

# Summary

Filed work item `WI-CONFIG-WRITER-NEWLINE-0001` for the project-config
writer bug recorded in `project/design/backlog.md` ("Project-config writer
corrupts strings containing newlines"): `_toml_quote` in
`src/taurworks/project_internals.py` writes control characters back
unescaped, so a rewriting command can leave `.taurworks/config.toml`
unparseable while reporting success. This run created the planning
artifact only; it did not implement the fix.

# Result

- Created `project/work_items/proposed/WI-CONFIG-WRITER-NEWLINE-0001.md`
  (`type: deliverable`, `status: proposed`), via `/lrh-work-item`.
- The draft was shown in full and confirmed by the user before writing.
  Interview answers were inferred from the backlog entry and the code and
  confirmed at that gate, not asked individually.
- Chosen fix direction: escape control characters per the TOML spec rather
  than reject such strings.
- Research finding recorded in the item: `src/taurworks/global_config.py`
  already escapes via `json.dumps`, so the global config is out of scope.
- Opened https://github.com/xenotaur/taurworks/pull/123.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-CONFIG-WRITER-NEWLINE-0001`:
  `prompt_ready: yes`, no blocking items or warnings.
- No tests run: the change adds a planning document only.

# Follow-up

- Implement the work item (`/lrh-implement WI-CONFIG-WRITER-NEWLINE-0001`).
- The backlog entry stays `Deferred` until the implementation marks it
  resolved (Required Change 5 of the work item).
- No workstream exists in this project, so no workstream update was
  offered.
