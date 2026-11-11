---
execution_id: 2026_11_10_23_32_18_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW)[2026-11-10T23:30:44+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_10_16_21_41_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/118
commit: e5114117b0f4204a47e002f0d99a46dc3cabef08
created_at: 2026-11-10T23:32:18+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Review-response round for PR #118 (design + WI-WORKING-DIR-REVERSE-DISCOVERY-0001),
run inline from `/lrh-land`. It addressed three Copilot threads from the
review of `86efa4a`. Codex reported no findings on the first push. The user
approved the fixes at the confirm gate.

# Result

All three comments passed the presence, validity and feasibility checks and
were fixed in commit `90ea8e2`:

1. **`project working` can't reach the no-target branch.** PROJECT is
   required (`cli.py:614-618`), and `project working .` uses the
   explicit-path `prefer_project_root` branch. Fix:
   - The shared function now starts from a path (the cwd or an explicit
     existing-directory target), and the explicit-path branch gets the
     reverse lookup.
   - `project working` was removed from the no-target list.
   - Regression test (i) added.
2. **The ambiguity guidance offered "pass a target" to commands that take
   none** (`dev ...`, `working-dir set`). Fix: guidance is now
   command-specific in the WI and `config_model.md`. Commands that accept a
   target say to pass one; the others say to rerun from the chosen
   `project_root`, with a project-root-relative DIR for `set`. Test (j)
   added.
3. **The `working-dir set` boundary was inconsistent** (whole configured
   working_dir vs. symlink). Fix: the WI's acceptance criteria, Required
   Change 4 and `config_model.md` all now use one rule: the boundary is the
   last symlink component of the lexical path. Test (c) now covers
   configured `working_dir/sub`.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-WORKING-DIR-REVERSE-DISCOVERY-0001`:
  `prompt_ready: yes`.

# Follow-up

- `/lrh-confirm-fixes` to verify these against the new head and resolve the
  threads.
