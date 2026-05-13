---
prompt_id: "PROMPT(TAURWORKS_PROJECT_WORKING_DIR_DESIGN_ALIGNMENT)[DESIGN/2026-05-12]"
work_item: "AD_HOC"
slug: "taurworks-project-working-dir-design-alignment"
status: "landed"
date: "2026-05-13"
---

# Summary
Aligned Taurworks design/control-plane documentation around the next working-directory metadata slice.

# Result
- Documented `project_root` as the directory containing `.taurworks/` and `working_dir` as the default code/work directory stored relative to that root.
- Added the minimal planned `.taurworks/config.toml` schema with `schema_version`, `[project].name`, and `[paths].working_dir`.
- Reflected the implementation sequence: `project working-dir show/set`, then `project create --working-dir`, then `project activate --print` using configured `working_dir`.
- Clarified that full `taurworks dev ...`, automatic shell mutation, and multi-repo project management remain out of scope for the next phase.
- Updated the root README and related design, roadmap, focus, status, and work-item control-plane artifacts.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- Attempted to read `project/executions/README.md` (failed: file is not present in this repository checkout).
- Checked prior executions for this exact prompt ID with `rg -n "TAURWORKS_PROJECT_WORKING_DIR_DESIGN_ALIGNMENT|DESIGN/2026-05-12" project/executions project` (none found).
- Ran `scripts/test` (pass).
- Ran `scripts/lint` (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_PROJECT_WORKING_DIR_DESIGN_ALIGNMENT)[DESIGN/2026-05-12]" --work-item AD_HOC --slug taurworks-project-working-dir-design-alignment --status landed` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Add or restore `scripts/prompts/record-execution` and `project/executions/README.md` so prompt-workflow instructions match repository contents.

# Review follow-up
- Reconciled README implementation status language so implemented project commands and planned working-directory metadata commands are not conflated.
- Spelled out full `taurworks project ...` command names in current-status language to avoid confusion with top-level compatibility commands.
- Added the shipped `taurworks project where` diagnostic command to planned/target project namespace lists.
- Attempted `scripts/version tools` before lint/format/test per review protocol guidance (failed: `scripts/version` is not present in this repository checkout), so formatter/linter/test validation was not re-run for this review-only documentation cleanup.
