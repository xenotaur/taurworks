---
execution_id: 2026_08_16_12_35_00_STORAGE_MODEL_POST_RECOVERY_REVIEW
prompt_id: PROMPT(AD_HOC:STORAGE_MODEL_POST_RECOVERY_REVIEW)[2026-08-16T12:32:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/106
commit:
created_at: 2026-08-16T12:35:00-04:00
agent: chatgpt
instruction_source: post-recovery design discussion for PR #106
session_transcript: pending
---

# Summary

Refine the proposed Taurworks Workspace/Taurspace storage model using evidence
and design findings from the subsequent Google Drive recovery and migration
planning discussion, while keeping PR #106 documentation-only and preserving
canonical design documents until adoption.

# Result

- Clarified that Taurspace is a local mirror-designated filesystem namespace,
  not a Google Drive-owned location, and that external provider health is
  separate from Taurworks placement semantics.
- Preserved one default mirrored root as the initial implementation shape while
  preventing the JSON/data model from hard-coding exactly one mirror forever;
  future named roots remain evidence-driven and their TOML selection syntax is
  deferred.
- Strengthened Workspace as a stable logical execution namespace for humans,
  scripts, Git tooling, IDEs, and resumable agent sessions.
- Added non-normative active-project normalization and cold-project lazy
  parking/reactivation examples without introducing a new storage class.
- Added manual/provider-assisted migration as legitimate dogfood evidence and
  kept Taurworks mutation commands off the critical path for the initial
  Workspace/Taurspace migration.
- Added an anti-foreclosure design rule and targeted non-project applicability
  probes for Music/Pictures while keeping general filesystem storage management
  outside implementation scope.
- Added a final project-storage closeout stage requiring an explicit evidence,
  design, and cost-benefit `GO` / `NO-GO` / `DEFER` decision before any broader
  storage-management effort.
- Generalized storage-root overlap reasoning and updated the illustrative JSON
  contract to identify mirror roots without implying provider identity.

# Validation

- Re-read the current PR #106 proposal and diff before editing.
- Reviewed `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, and
  `project/executions/README.md` on the PR branch.
- Preserved the proposal-only scope: no canonical design documents or executable
  code were changed.
- The LRH CLI and local Taurworks validation scripts were not available in this
  remote GitHub-only session; this execution record was therefore authored
  manually as permitted by `project/executions/README.md`.
- GitHub CI should be rechecked on the updated PR head before merge/adoption.

# Follow-up

- Review the revised proposal as a whole.
- After any additional semantic review, run the repository's normal fresh-eyes
  review/confirmation workflow and confirm CI before adoption or merge.
