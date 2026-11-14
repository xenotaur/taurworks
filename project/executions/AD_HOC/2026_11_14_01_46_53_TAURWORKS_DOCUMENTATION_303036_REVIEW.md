---
execution_id: 2026_11_14_01_46_53_TAURWORKS_DOCUMENTATION_303036_REVIEW
prompt_id: PROMPT(AD_HOC:TAURWORKS_DOCUMENTATION_303036_REVIEW)[2026-11-14T01:39:54+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/122
commit:
created_at: 2026-11-14T01:46:53+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/122
session_transcript: pending
---

# Summary

Review-response round 1 for PR #122 (end-user documentation), run inline
from `/lrh-land`. Seven open threads (one Codex, six Copilot; two were the
same finding), all verified valid against the source before fixing.

No `rerun_of`: the PR's primary record
(`2026_11_14_00_14_13_DOC_WORK_END_USER_DOCS`) uses a different slug from
this branch-derived one, so the slug-based lookup finds no primary.

# Result

All seven fixed:

- README quick start: added `mkdir -p ~/Workspace` before `workspace set`
  (Codex and Copilot, same finding).
- `docs/explanation/concepts.md`, `docs/how-to/use-tl-fallback.md`: legacy
  sourcing consent is one-time (`--legacy` / "source once") or persistent
  trust, not trust only.
- `docs/how-to/activate-projects.md`: a missing `working_dir` only changes
  the directory target; Conda, exports, and message still apply.
- `docs/how-to/migrate-legacy-projects.md`: verify with
  `tw activate NAME --no-legacy`; retire-script `mv` now uses
  project-root-qualified paths.
- `docs/how-to/manage-projects.md`, `docs/reference/cli.md`:
  `projects --details` checks for a Conda environment named after the
  project (not the configured one) and walks the tree to count files.

Nothing skipped.

# Validation

- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`:
  pass.
- `scripts/test`: 404 tests OK.
- `lrh validate`: 0 errors, 0 warnings.
- Relative links and anchors in `README.md` and `docs/**/*.md`: 0 broken.

# Follow-up

- `projects --details` reporting `missing` for a project whose configured
  Conda environment has a different name is a behavior quirk, documented
  as-is here; a candidate backlog item.
