---
execution_id: 2026_11_14_04_10_34_TAURWORKS_DOCUMENTATION_303036_REVIEW
prompt_id: PROMPT(AD_HOC:TAURWORKS_DOCUMENTATION_303036_REVIEW)[2026-11-14T04:10:33+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_14_01_46_53_TAURWORKS_DOCUMENTATION_303036_REVIEW
pr: https://github.com/xenotaur/taurworks/pull/122
commit:
created_at: 2026-11-14T04:10:34+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/122
session_transcript: pending
---

# Summary

Review-response round 2 for PR #122, in the same `/lrh-land` run as round 1
(same-land-run continuation). Addresses the five non-thread findings from
the PR-mode self-review pass, after the user explicitly chose to fix them at
the stop-work halt.

# Result

All five fixed in `4b43629`:

- `docs/reference/cli.md`, `docs/reference/configuration.md`,
  `docs/how-to/troubleshooting.md`, `project/design/backlog.md`: `workspace
  show` reports `inferred` only when the global config file is absent.
- `docs/reference/configuration.md`: `schema_version` is enforced by
  commands that write the project config, not by readers.
- `docs/reference/configuration.md` "Hand-editing": rewrites drop comments;
  only string, integer, and boolean values can be rewritten; other types
  make the command fail and leave the file unchanged.
- `docs/reference/cli.md`: limits of top-level `taurworks activate`
  (workspace children only, no registry, exits 1 otherwise).
- `docs/reference/cli.md`, `docs/how-to/activate-projects.md`:
  `working-dir set` rejects absolute paths; `tw activate PATH` needs the
  project root itself.

Nothing skipped. These were non-thread findings, so there is no GitHub
thread to resolve.

# Validation

- `scripts/format --check --diff`, `scripts/lint`: pass.
- `scripts/test`: 404 tests OK.
- `lrh validate`: 0 errors, 0 warnings.
- Relative links and anchors: 0 broken.

# Follow-up

None.
