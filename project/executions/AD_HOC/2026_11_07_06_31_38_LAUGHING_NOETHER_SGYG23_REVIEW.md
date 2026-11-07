---
execution_id: 2026_11_07_06_31_38_LAUGHING_NOETHER_SGYG23_REVIEW
prompt_id: PROMPT(AD_HOC:LAUGHING_NOETHER_SGYG23_REVIEW)[2026-11-07T06:30:19+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_07_00_01_06_LAUGHING_NOETHER_SGYG23_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/115
commit: 8a1f90e200d8aa58b4e30933fdd6c2766f22c768
created_at: 2026-11-07T06:31:38+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/115
session_transcript: claude-app:886ad668-3050-4ae4-8925-4fa068b6791c
---

# Summary

Round 4 of review response on PR #115, within the same `/lrh-land` run.
A fresh cold-context re-verification of round 3 kept Thread A
(`PRRT_kwDOBscEL86wLZif`) at Problematic resolution: the docs promised a
hard error for an invalid symlink at every validating command, but `dev
where`/`status` (`dev.py:37-50`) catch `ProjectConfigError` and fall back.
Threads B and C stayed Clear-satisfied. The human explicitly approved a
helper-level rewrite. Same-land-run continuation of the round-3 `_REVIEW`
record (authored earlier in this session, `in_progress`).

# Result

- Thread A — the invalid-symlink rule is now stated at the helper level in
  `config_model.md` and the WI (acceptance, Scope, Required Change 6 test
  (d), prose criteria): both helpers raise the same `ProjectConfigError`
  they raise for an escaping value, and each caller keeps its existing
  handling unchanged. Per-caller invalid-symlink outcomes are no longer
  enumerated. Test (d) is now helper-level plus one end-to-end check
  (`project activate --print`).
- Nit — Scope inventory and acceptance now say `tw activate` fails at the
  shell layer (`taurworks-shell.sh:334-337`) for a missing working dir,
  rather than grouping it with `activate --print`'s successful report.
- Nit — legacy migration's absolute-`cd` normalization
  (`legacy._normalize_cd_target`) is documented as unchanged; only relative
  legacy targets get the lexical rule.
- Nit — `current_focus.md` Active direction 2 now includes the
  dangling/looping-symlink check.
- Post-verification nits (same round, committed with this record update):
  a fresh cold verifier rated all three threads Clear-satisfied and flagged
  that `tw activate` runs `activate --shell` (not `--print`; same
  diagnostics function) and that roadmap.md's "Phase 2A above" should read
  "below". Both wordings corrected in `config_model.md`, the WI, and
  `roadmap.md`.

# Validation

- `scripts/format --check --diff`: 33 files unchanged, pass
- `scripts/lint`: all checks passed
- `scripts/test`: 350 tests, OK
- `lrh validate`: 3 errors, 10 warnings — unchanged pre-existing baseline
  (identical on `origin/master`; none in files this PR touches)

# Follow-up

- Re-run confirm-fixes against the new head for a fresh verdict.
