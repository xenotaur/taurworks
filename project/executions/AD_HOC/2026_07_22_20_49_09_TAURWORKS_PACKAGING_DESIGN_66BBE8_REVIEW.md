---
execution_id: 2026_07_22_20_49_09_TAURWORKS_PACKAGING_DESIGN_66BBE8_REVIEW
prompt_id: PROMPT(AD_HOC:TAURWORKS_PACKAGING_DESIGN_66BBE8_REVIEW)[2026-07-22T20:10:49-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/77
commit: b6687a31d66aec3ec92b9fed06460c85af9f0f8b
created_at: 2026-07-22T20:49:09-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/77
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Addressed 8 open review comments on PR #77 (`project/design/packaging_and_install.md`),
the public-release packaging/install design doc. All comments were doc-accuracy
issues raised against a design note, not code defects; no source changes were
required.

# Result

All 8 comments passed presence/validity/feasibility triage and were fixed:

- copilot: softened the "all confirmed by reading the current repo" framing
  in the Purpose section — the `~/bin/tl.source` live-setup detail is from
  the user's own description of their setup, not evidenced in version-controlled
  state.
- copilot: corrected `bin/`'s file count from "30 files" to the actual 27
  non-hidden entries.
- copilot: reworded the `scripts/install` references from present tense
  ("becomes"/"is kept") to future/proposed tense, since the script does not
  exist yet.
- copilot: clarified that `sourceme/`'s packaging into `setup.py`'s
  `package_data` (which currently only lists `resources/shell/taurworks-shell.sh`)
  is implementation work this design assumes but does not yet specify.
- copilot: corrected the `TAURWORKS_SHELL_HELPER_PATH` description — it is an
  existing env-var-only precedent, not an existing "CLI-flag-plus-env-var
  pattern"; the new `--debug`/`TAURWORKS_DEBUG` pairing is a new pattern.
- codex (P2): exempted `bin/migrate_legacy_projects.py` from the blanket
  "bin/ is unrelated" claim — it imports `taurworks.legacy`/`manager`/
  `project_internals` and is imported by `tests/migrate_legacy_projects_test.py`
  by file path; it must stay under the `taurworks` boundary rather than
  moving to `taurscripts` or being deleted with the rest of `bin/`.
- codex (P2): specified that `scripts/install`'s proposed shim should use a
  non-editable `pipx install . --force`, reserving `--editable` for the
  existing dev-install path (`./scripts/develop`).
- codex (P2): expanded the PATH-loss diagnostic design to cover internal
  `command taurworks ...` calls made from within `tw activate` after
  `conda activate` runs (e.g. `legacy inspect`, `project trust set`), not
  only the initial entry-point delegation check.

# Validation

Design-doc-only change (markdown), no source touched. Ran canonical validation
per repository convention anyway:

- `git rev-parse HEAD` (pre-push): `c851a1eb461d2792d414c01715ff26dc7a5b2c8c`
- `./scripts/version tools` (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `./scripts/format --check --diff`: 28 files unchanged, pass
- `./scripts/lint`: black + ruff, pass
- `./scripts/test`: 288 tests, OK
- `lrh validate`: 4 pre-existing errors, all `contributors/contributors.md`
  (known gap, unrelated to this change — see `project_contributors_md_gap`
  memory)

# Follow-up

- `session_transcript: pending` should be updated to `claude-app:<session-id>`
  after this session ends.
- Recommend `/lrh-confirm-fixes` before merge to verify fixes against the
  current diff and resolve the review threads.
- The design doc's own open questions (tl-source install location, exact
  `bin/` destination for the non-`migrate_legacy_projects.py` files, and
  `--debug` line-by-line classification) remain deferred to the implementing
  work item(s), unchanged by this review-response pass.
