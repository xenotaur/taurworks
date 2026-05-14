---
prompt_id: "PROMPT(TAURWORKS_INIT_CREATE_RESOLUTION_DESIGN_ALIGNMENT)[DESIGN/2026-05-13]"
work_item: "AD_HOC"
slug: "taurworks-init-create-resolution-design-alignment"
status: "landed"
date: "2026-05-13"
---

# Summary
Aligned Taurworks design/control-plane documentation with the accepted dogfood-resolution design for `project init`, `project create`, shared target resolution, working-directory target handling, explicit working-directory creation, and nested same-name project prevention.

# Result
- Documented `project init [PATH] [--working-dir DIR] [--create-working-dir]` as safe, idempotent initialization of an existing/current project root that reuses refresh/config logic.
- Documented `project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` as new-root creation followed by init/refresh delegation, with `--nested` required for intentional nested same-name projects.
- Captured centralized target-resolution rules and diagnostic output including `input`, `project_root`, and `resolved_by`.
- Updated working-directory documentation so `show [PATH_OR_NAME]` is target-aware, `set DIR --project PATH_OR_NAME` is the preferred mutation shape, and missing work directories require explicit creation opt-in.
- Reaffirmed that `project activate --print` remains read-only and resolver-backed, and that `tw activate` / shell mutation remain future work after these dogfood findings are addressed.
- Updated the root README and related design, roadmap, focus, status, active work-item, and execution-record README control-plane artifacts.

# Validation
- Read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md` before editing.
- At the start of this prompt run, attempted to read `project/executions/README.md` before creating it in this change (failed: file was not present in this repository checkout yet).
- Checked prior executions for this exact prompt ID with `rg -n "TAURWORKS_INIT_CREATE_RESOLUTION_DESIGN_ALIGNMENT|init create|nested same-name|create-working-dir|shared target" project PROMPTS.md README.md` (no prior execution record for this exact prompt ID found).
- Ran `./scripts/test` (pass).
- Ran `./scripts/lint` (pass).
- Ran `./scripts/format --check --diff` (pass).
- Ran `git diff --check` (pass).
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(TAURWORKS_INIT_CREATE_RESOLUTION_DESIGN_ALIGNMENT)[DESIGN/2026-05-13]" --work-item AD_HOC --slug taurworks-init-create-resolution-design-alignment --status landed` (failed: script not present in repository); created this execution record manually following existing repository conventions.

# Follow-up
- Add or restore `scripts/prompts/record-execution` so prompt-workflow instructions match repository contents.

# Review follow-up
- Clarified README user-facing sections so planned resolver rules and planned flags such as `--create-working-dir`, `working-dir set --create`, target-aware `working-dir show [PATH_OR_NAME]`, and `working-dir set DIR --project PATH_OR_NAME` are explicitly labeled as not yet fully implemented.
- Clarified that the failed `project/executions/README.md` read happened at the start of the prompt run before this change added that file.
- Attempted review-protocol validation with `scripts/version tools` first (failed: `scripts/version` is not present in this repository checkout), so lint/format/test were not re-run for this review follow-up under the requested validation order.
- Ran `git diff --check` for the review follow-up (pass).
