---
execution_id: 2026_11_11_00_17_31_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW)[2026-11-11T00:17:22+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_11_00_10_23_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/118
commit: e5114117b0f4204a47e002f0d99a46dc3cabef08
created_at: 2026-11-11T00:17:31+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/118
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Round 3 of review-response for PR #118, run inline from `/lrh-land`. It
addresses the fresh substitute PR-mode review on `561e970`, whose findings
tripped the stop-work condition again. The user chose "Fix in PR (round 3)"
over merging with closeout notes. Fixes are in commit `6b7e35f`.

# Result

1. **Medium: no ambiguity carrier on the `resolve_project_target` path.**
   I verified it: `ProjectResolution` (`project_internals.py:36-43`) has
   only `input`, `project_root` and `resolved_by`.
   - RC1 now adds a `candidates` field (empty by default) and an ambiguous
     `ResolutionReason`.
   - RC2 says an ambiguous lookup never falls back to `EXISTING_PATH` or
     `DEFAULT_CURRENT_DIRECTORY`, and that callers fail, with the path
     emitters printing nothing to stdout.
   - AC3/AC4 updated; test (l) added.
2. **Low-medium: wrong guidance for `working-dir show`.** Its bare names
   resolve relative to the cwd. RC3's guidance is now split into three
   groups:
   - registry-name commands: pass the name or path;
   - `working-dir show`: pass the path to `project_root`;
   - commands with no target (`dev ...`, `project where`,
     `working-dir set`): rerun from `project_root`.

   `config_model.md` matches.
3. **Low: inventory gaps.**
   - `project root` and top-level `taurworks working`/`root` share the
     path-emitter branch (`cli.py:109-114`, `cli.py:1207-1210`). They are
     added to AC2, RC2 and test (i).
   - `:775` (`_current_project_name`, `project create`'s nested-name guard)
     is now listed as not affected; it stays physical-walk only.
   - The current-project name check (`:134`, `:149-156`) is in the
     inventory, and the RC2 hook feeds it so `working-dir show NAME` works.
     Test (m) added.
   - `project where` added to the guidance groups and test (j).
4. **Low: the `:127` wording** now says these callers never pass `None`,
   and that `init` can pass a bare name.
- PR body updated to list tests (a) through (m).

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-WORKING-DIR-REVERSE-DISCOVERY-0001`:
  `prompt_ready: yes`.

# Follow-up

- Confirm-fixes round 3 on the new head, with a fresh substitute review
  (these were non-thread findings).
