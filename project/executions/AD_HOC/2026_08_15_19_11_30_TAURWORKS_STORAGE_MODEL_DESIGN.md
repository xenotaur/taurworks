---
execution_id: 2026_08_15_19_11_30_TAURWORKS_STORAGE_MODEL_DESIGN
prompt_id: PROMPT(AD_HOC:TAURWORKS_STORAGE_MODEL_DESIGN)[2026-08-15T19:09:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/106
commit:
created_at: 2026-08-15T19:11:30-04:00
agent: chatgpt
instruction_source: user design discussion captured in project/design/storage_model.md
session_transcript: pending
---

# Summary

Capture the proposed Taurworks Workspace/Taurspace storage model as a durable,
documentation-only design artifact, using LRH `lrh-design` and `lrh-proposal`
conventions for proposal structure while preserving Taurworks' existing
`project/design/*.md` organization.

# Result

- Added `project/design/storage_model.md` with `status: proposed`.
- Defined persistent-local, mirrored, and transient storage semantics.
- Separated storage class from observed symlink topology and limited Taurworks
  ownership to explicitly managed mappings.
- Defined an audit-first `taurworks storage` command direction with versioned
  JSON output and one `taurworks-storage-audit` Agent Skill backed by the CLI.
- Staged mutating storage operations after read-only audit dogfooding.
- Updated `project/design/README.md` to index the proposed design.
- Opened draft PR #106 for semantic review.

# Validation

- Reviewed `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, existing Taurworks design
  documents, and execution-record conventions.
- Reviewed LRH `lrh-design` and `lrh-proposal` skill guidance and proposal
  schema/body conventions.
- Searched Taurworks for existing storage/symlink design scope and found no
  duplicate storage subsystem or matching backlog item.
- No executable code changed; runtime tests were not applicable to this
  GitHub-only documentation change.

# Follow-up

Review and refine PR #106. If adopted, update canonical Taurworks design/config
artifacts and derive staged implementation work beginning with read-only
`taurworks storage show` and `taurworks storage audit --format md|json`.
