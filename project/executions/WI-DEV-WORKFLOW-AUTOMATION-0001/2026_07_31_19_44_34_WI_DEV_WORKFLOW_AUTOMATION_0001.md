---
execution_id: 2026_07_31_19_44_34_WI_DEV_WORKFLOW_AUTOMATION_0001
prompt_id: PROMPT(WI-DEV-WORKFLOW-AUTOMATION-0001:WI_DEV_WORKFLOW_AUTOMATION_0001)[2026-07-31T19:44:34+00:00]
work_item: WI-DEV-WORKFLOW-AUTOMATION-0001
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/100
commit:
created_at: 2026-07-31T19:44:34+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-DEV-WORKFLOW-AUTOMATION-0001.md
session_transcript: claude-app:43689ae3-1b8e-45ff-b3b8-75e8997239fb
---

# Summary

Implemented `WI-DEV-WORKFLOW-AUTOMATION-0001`: `taurworks dev
clean/test/smoke/lint/format/build` as delegate-only v1 workflow
commands, resolving via Tier 1 (`[dev.commands]` config override, read
from `project_root`) then Tier 2 (project-local `scripts/<name>`,
resolved against `work_directory_guess`).

# Result

**`src/taurworks/project_internals.py`**: added
`dev_command_from_config(config, name)`, reading `.taurworks/config.toml`'s
`[dev.commands]` table, following the existing
`activation_message_from_config`/`activation_exports_from_config`
validation pattern (raises `ProjectConfigError` on malformed `[dev]`/
`[dev.commands]` tables or non-string command values).

**`src/taurworks/dev.py`**: added `DEV_V1_COMMANDS` tuple, a
`DevCommandResolution` frozen dataclass (mirroring `setup_command.py`'s
`ResolvedSetupPath` precedent: a `resolved` bool plus a `detail` field
that's the resolved source description on success or the failure message
on failure), `resolve_dev_command(name)`, and `execute_dev_command(resolution)`.
Resolution correctly splits Tier 1 and Tier 2 across two different base
directories per the WI's review-caught design fix: Tier 1 reads
`.taurworks/config.toml` from the detected `project_root`
(`project_internals.find_project_root_candidate`) regardless of any
configured `working_dir`; Tier 2's `scripts/<name>` and the execution
function's `subprocess.run(..., cwd=...)` both use
`gather_dev_where_diagnostics()`'s existing `work_directory_guess`, which
may legitimately differ from `project_root`. An unexecutable Tier 2
script fails clearly (distinct message) rather than silently falling
through to "not found."

**`src/taurworks/cli.py`**: added `clean`/`test`/`smoke`/`lint`/`format`/
`build` subparsers under `dev` (generated via a loop over
`(name, help_text)` pairs to avoid repetition), and dispatch in
`_handle_dev_command` that resolves, prints a clear stderr message and
exits 1 on failure, or executes and propagates the delegated exit code
via `raise SystemExit(...)` on success.

**Tests**: `tests/dev_test.py` (new, 20 tests) covers Tier 1 resolution,
Tier 2 resolution, Tier 1 precedence, the neither-resolves failure path,
the unexecutable-script failure path, exit-code passthrough, and the two
review-caught regressions specifically (Tier 1 config resolving from
`project_root` with a nested `working_dir` configured; the delegated
subprocess's `cwd` matching `work_directory_guess`), plus direct unit
coverage of `dev_command_from_config`. `tests/cli_test.py` adds
`DevWorkflowAutomationCliTest` (5 tests): end-to-end script delegation,
the clear-failure message, `shlex.split` config-command delegation, and
an end-to-end nested-`working_dir` case exercising both review-caught
regressions together via a real subprocess CLI invocation.

**Manual dogfood** (this repo's own root, since `working_dir = "."` here
so `project_root` and `work_directory_guess` coincide -- the nested-
`working_dir` divergence is covered by the dedicated tests above, not by
this repo's own dogfooding, exactly as the WI's Risk Notes anticipated):
ran all six `taurworks dev <name>` commands for real. `clean` removed
only regenerable `__pycache__`/`.ruff_cache` (verified via
`scripts/clean --dry-run` first); `format` reported 32 files already
unchanged; `lint` passed both `black --check` and `ruff`; `test` and
`smoke` ran the real suites (`OK`); `build` produced a real sdist/wheel,
cleaned up afterward via `dev clean`. Also directly verified the
neither-resolves failure path (`taurworks dev clean` from `/tmp`, outside
any project) prints a clear message naming both locations checked and
exits 1.

**README.md**: added a new "`taurworks dev` workflow automation (v1)"
subsection documenting the two-tier resolution order (including the
`project_root`/`work_directory_guess` split), the `[dev.commands]` config
table syntax, the cwd/exit-code/streaming behavior, and the
neither-resolves failure behavior; added the six new commands to the
"Implemented namespaced commands" list.

# Validation

- Tool versions (Taurworks conda env): Python 3.11.10, black 26.3.1, ruff 0.15.12
- `black --check --diff src tests`: 33 files unchanged, pass
- `ruff check src tests`: pass
- `python -m unittest discover -s tests -p "*_test.py"` (`PYTHONPATH=src:tests`):
  345 tests, OK (25 new: 20 in `dev_test.py`, 5 in `cli_test.py`)
- Manual dogfood: all six `taurworks dev <name>` commands run for real
  from this repo's own root, each delegating to the matching
  `./scripts/<name>`, plus the neither-resolves failure path verified
  directly outside any project.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Next: open PR, wait for reviewer comments, run
  `/lrh-review-response`/`/lrh-confirm-fixes`, then `/lrh-closeout` after
  merge.
