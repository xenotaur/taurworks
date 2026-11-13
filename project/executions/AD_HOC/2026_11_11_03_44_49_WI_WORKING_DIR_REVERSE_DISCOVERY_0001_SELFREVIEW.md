---
execution_id: 2026_11_11_03_44_49_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_SELFREVIEW)[2026-11-11T03:44:49+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_11_11_03_45_54_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/119
commit: 9be45caa6efe6a5f8067a1550cb0036db6113bc3
created_at: 2026-11-11T03:44:49+00:00
agent: claude_app
instruction_source: "lrh-self-review diff-mode (lrh-implement Step 7.5) for project/work_items/proposed/WI-WORKING-DIR-REVERSE-DISCOVERY-0001.md"
session_transcript: claude-app:1b69806b-4260-4637-95d0-46434a8c5576
---

# Summary

Diff-mode `/lrh-self-review` pass (report-only, no `--apply`) on branch
`xenotaur/feat/wi-working-dir-reverse-discovery-0001-impl` at `f16b039`,
before the PR's first push. It reviewed `git diff origin/master` against
WI-WORKING-DIR-REVERSE-DISCOVERY-0001, using a cold-context general-purpose
subagent.

# Result

- Verdict: nothing blocking. The diff plausibly satisfies all 7 acceptance
  criteria.
- The subagent ran experiments covering the macOS `/var` vs `/private/var`
  aliasing, the `wd/sub` boundary, the ambiguous layout (`activate
  --shell`, `legacy inspect`/`migrate --apply`, `trust set`, `env set`,
  `project root .`, `dev test`), and the unchanged paths (`project init`,
  `project create`'s guard, `prefer_project_root=False`).
- Non-blocking findings:
  1. `project where` exited 0 on ambiguity, which contradicted the design's
     "every other affected command fails". The invoking session verified it
     (`cli.py` never raised).
  2. Stale "Today every cwd-based command..." prose in the implemented
     design section.
  3. Test gaps: (c) `set ../..` with `working_dir/sub`; (m) the
     `project create` guard; the `/var` alias case; (k) covering only
     `env show`.
  4. An unneeded reverse lookup for path-like activation targets.
  5. A design consequence: a `working_dir` linked to a broad directory
     such as `$HOME` claims every non-project directory under it.
- The main session applied verified fixes in commit `b0ab2cc`, outside this
  report-only pass:
  - `project where` exits 1 on ambiguity.
  - The design prose is corrected.
  - The cwd lookup is skipped for path-like activation targets.
  - Added the (c) `set ../..` and (m) create-guard tests.
- Left as-is: the `/var` alias test gap (verified manually by the
  subagent), (k) breadth (meets "one of"), and finding 5 (follows from the
  design).

# Validation

- The subagent ran `./scripts/test`, the targeted modules, format, lint
  and `lrh validate`, all passing.
- After the fixes: 393 tests OK; `lrh validate` 0 errors, 0 warnings.

# Follow-up

- Possibly document finding 5 (broad `working_dir` targets) in a later
  docs pass.
