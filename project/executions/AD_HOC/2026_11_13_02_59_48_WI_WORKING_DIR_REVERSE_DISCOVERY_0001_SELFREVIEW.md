---
execution_id: 2026_11_13_02_59_48_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW)[2026-11-13T02:59:48+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_11_03_45_54_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/119
commit: 9be45caa6efe6a5f8067a1550cb0036db6113bc3
created_at: 2026-11-13T02:59:48+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/119
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

PR-mode `/lrh-self-review` substitute pass on PR #119 at `a0a5127` (the
round-1 `_CONFIRM` head). It used a cold-context general-purpose subagent
and was report-only. This record was created at closeout, on `master`, rather than pushed to the PR, so the PR head wasn't moved (the PR #117/#118 precedent).

# Result

- Verdict: safe to merge, with non-blocking findings:
  1. **Worth fixing:** `dev test` from a `git worktree` inside the external
     target ran the main checkout's script, a regression vs master. The
     invoking session reproduced it.
  2. **Minor:** a non-UTF-8 global config crashed `dev where` outside any
     project.
  3. Undocumented: a `working_dir` linked to a broad directory such as
     `$HOME` claims every non-project directory under it.
  4. Wording aside in the "rerun" guidance.
- This tripped the stop-work condition. The user chose "Fix in PR": round 2
  (`fcca908`) fixed 1–2; 3–4 were deferred.

# Validation

The subagent ran 394 tests, lint, format and `lrh validate`, plus
temp-tree experiments covering ambiguity across 17 commands.

# Follow-up

- Fixed in round 2; 3–4 are follow-ups.
