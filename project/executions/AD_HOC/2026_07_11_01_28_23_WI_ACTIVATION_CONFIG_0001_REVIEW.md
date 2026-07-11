---
execution_id: 2026_07_11_01_28_23_WI_ACTIVATION_CONFIG_0001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_ACTIVATION_CONFIG_0001_REVIEW)[2026-07-10T02:27:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_09_22_12_46_WI_ACTIVATION_CONFIG_0001
pr: https://github.com/xenotaur/taurworks/pull/65
commit: 
created_at: 2026-07-11T01:28:23-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/65
session_transcript: pending
---

# Summary

Address 8 open review comments (6 distinct issues) on PR #65 (`taurworks
legacy inspect`/`migrate`, `WI-ACTIVATION-CONFIG-0001` slices 4-5) via
`lrh request review_response`.

# Result

**Issue 1 — invalid conda env names not validated (codex + copilot,
duplicate)**

`conda activate` detections were marked supported without checking
`project_internals.validate_conda_environment_name`, so a target like
`/opt/conda/envs/foo` would be written to `activation.environment.name` and
only fail later when the project was activated.

Presence: confirmed. Validity: confirmed — real bug. Feasibility: trivial.
Fixed by validating the name in `_classify_line` before returning a
`conda_activate` match; invalid names now fall through to `unsupported`.

**Issue 2 — absolute `cd` targets always rejected (codex)**

`manager.refresh_project`/`create_project` generate legacy scripts with
`cd "{repo_dir}"` using an *absolute* path, but
`relative_working_dir_metadata` only accepts relative paths and always
raised, so `legacy migrate` sent the most common legacy format to manual
review instead of applying it.

Presence: confirmed. Validity: confirmed — the exact format this repo's own
legacy-script generator produces was mishandled. Feasibility: fixable
without loosening safety. Fixed by adding `_normalize_cd_target`, which
converts an absolute path to project-root-relative when it resolves inside
the project root (and leaves it for manual review, unchanged, when it
resolves outside).

**Issue 3 — project resolution doesn't check the registry/workspace
(codex)**

`legacy inspect`/`migrate` only did current/path-style resolution via
`project_internals.resolve_project_target`, unlike `project activate`/`root`,
so a registered or workspace project name resolved incorrectly from outside
the project directory.

Presence: confirmed. Validity: confirmed. Feasibility: trivial — an
existing resolver already does the right thing. Fixed by switching to
`project_resolution.resolve_global_activation_project`, reusing its
`legacy_setup_path`/`legacy_setup_exists` fields (already computed by
`manager.classify_project_entry`) instead of recomputing them.

**Issue 4 — malformed config.toml crashes instead of failing gracefully
(codex)**

`tomllib.TOMLDecodeError` wasn't in the caught exception tuple around
`read_project_config` in `gather_legacy_migrate_diagnostics`, so a broken
partial config produced a traceback instead of the stable `ok: false`
diagnostics used everywhere else.

Presence: confirmed. Validity: confirmed. Feasibility: trivial. Fixed by
adding `tomllib.TOMLDecodeError` to the except clause.

**Issue 5 — two tests assert after `TemporaryDirectory` exits (copilot, 2
comments)**

`test_inspect_never_writes_or_executes` and `test_dry_run_writes_nothing`
had their filesystem-existence assertions outside the `with
tempfile.TemporaryDirectory()` block, so the checks ran against an
already-deleted directory and were vacuously true regardless of actual
behavior — the exact mistake caught in the prior review round on
`WI-LEGACY-CONDA-GATING-0001`.

Presence: confirmed. Validity: confirmed. Feasibility: trivial. Fixed by
moving the assertions inside the `with` block in both tests.

**Issue 6 — unsupported lines print raw, potentially secret-bearing text
(copilot)**

`legacy inspect` echoed the full raw text of any unsupported line (e.g. a
`curl -H "Authorization: Bearer abc123"` line), even though export values
were already redacted — a real gap in the "never leak secrets" intent.

Presence: confirmed. Validity: confirmed. Feasibility: trivial. Fixed by
dropping the raw line from `format_legacy_inspect_output`'s unsupported-line
branch; only the line number and note are printed now. The internal match
dict still retains `raw` for potential future tooling, but it is never
surfaced in CLI output.

No comments were skipped.

Added 5 new tests covering: invalid conda name rejection, absolute `cd`
target inside/outside the project root, malformed-TOML graceful failure,
and workspace-name resolution from outside the project directory (via
`TAURWORKS_WORKSPACE`/isolated `HOME`/`XDG_CONFIG_HOME`, `os.chdir` with
try/finally, matching the pattern already used in
`project_resolution_test.py`).

# Validation

- `git rev-parse HEAD` / `git status --short` captured before validation
- Local environment note: `scripts/version tools` is not present in this
  repo. Initial `python -m black --version` showed 25.11.0 (drifted from
  the CI-pinned `constraints-dev.txt` value of `black==26.3.1`), which
  produced an unrelated-looking reformat diff against `src/taurworks/manager.py`
  (a file untouched by this PR). Reinstalled `black==26.3.1` to match CI's
  pin before proceeding; confirmed clean afterward. This was a local
  tooling drift, not a code regression — `manager.py` was not modified.
- `scripts/format --check --diff` — 26 files unchanged (under black 26.3.1)
- `scripts/lint` — Black + Ruff, all checks passed
- `scripts/test` — 193 tests, OK
- `lrh validate` — 4 errors / 1 warning, identical to the pre-existing
  `contributors.md`/orphaned-work-item baseline; no new errors
- Manual smoke test: `taurworks legacy inspect` on a project with an
  invalid conda target and an absolute `cd` path correctly flagged the
  conda line as unsupported (with reason, no raw-line leak for the other
  unsupported line) and detected the absolute `cd` target; `taurworks
  legacy migrate --apply` correctly wrote `paths.working_dir` from the
  absolute `cd` target and left the invalid conda line as manual review

# Follow-up

- `session_transcript` is `pending`; update to `claude-app:<session-id>`
  once the session ID is known.
- Local anaconda environment's `black` was reinstalled to `26.3.1` during
  this session to match the CI pin; worth a persistent memory note so
  future sessions don't lose time re-diagnosing the same drift.
