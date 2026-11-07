---
execution_id: 2026_11_06_23_55_54_LAUGHING_NOETHER_SGYG23_REVIEW
prompt_id: PROMPT(AD_HOC:LAUGHING_NOETHER_SGYG23_REVIEW)[2026-11-06T23:54:19+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_06_23_47_02_LAUGHING_NOETHER_SGYG23_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/115
commit: 436489d11b8a06f969d1d6defdae552b1243a853
created_at: 2026-11-06T23:55:54+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/115
session_transcript: claude-app:886ad668-3050-4ae4-8925-4fa068b6791c
---

# Summary

Round 2 of review response on PR #115, within the same `/lrh-land` run.
An independent cold-context re-verification of round 1 classified Thread A
(`PRRT_kwDOBscEL86wLZif`, missing-directory policy) as Problematic
resolution and flagged stale call-site text; Threads B and C were
Clear-satisfied. The human explicitly amended the run's stop-work
condition to allow this round. Same-land-run continuation of the round-1
`_REVIEW` record (authored earlier in this session, `in_progress`).

# Result

- Thread A follow-up — round 1 listed `project working-dir show` as
  reporting `working_dir_exists: False`; confirmed false
  (`gather_project_working_dir_show_diagnostics`,
  `project_resolution.py:1078-1146`, echoes the raw config value and calls
  no validator). Removed from both `config_model.md` and the WI, and stated
  explicitly that the design leaves `show` unchanged.
- Call-site inventory — "all four current call sites" was wrong. Grepped
  every caller of `relative_working_dir`/`relative_working_dir_metadata`
  and replaced the list with a full inventory, adding `taurworks project
  working`/`taurworks working` (`project_resolution.py:1752`, fails on a
  missing path), `dev where`/`status` (`dev.py:42`), project
  classification (`manager.py:298`), and legacy migration
  (`legacy.py:408`), each with its existing missing-directory policy.
  Confirmed `tw activate` (`project activate --shell`) shares
  `gather_project_activate_print_diagnostics` with `--print`.
- Required Change 2 — corrected: `working-dir set` reaches only
  `set_working_dir` → `relative_working_dir`, not the metadata helper.
- `design.md:29` — reworded so lexical containment reads as designed, not
  yet implemented, matching `config_model.md`'s status line.

# Validation

- `scripts/format --check --diff`: 33 files unchanged, pass
- `scripts/lint`: all checks passed
- `scripts/test`: 350 tests, OK
- `lrh validate`: 3 errors, 10 warnings — unchanged pre-existing baseline
  (identical on `origin/master`; none in files this PR touches)

# Follow-up

- Re-run confirm-fixes against the new head for a fresh verdict.
