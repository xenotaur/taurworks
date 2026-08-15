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
instruction_source: project/design/proposals/proposed/taurworks-storage-model/00_proposal.md
session_transcript: pending
---

# Summary

Capture the proposed Taurworks Workspace/Taurspace storage model as a durable,
documentation-only design proposal, using LRH `lrh-design` and `lrh-proposal`
conventions for proposal structure and lifecycle while preserving Taurworks'
existing canonical `project/design/*.md` documents until the proposal is
adopted.

# Result

- Added `project/design/proposals/proposed/taurworks-storage-model/00_proposal.md`
  with `status: proposed`, placing the artifact inside the LRH proposal
  lifecycle discovered by `lrh validate`.
- Defined persistent-local, mirrored, and transient storage semantics.
- Separated storage class from observed symlink topology and limited Taurworks
  ownership to explicitly managed mappings.
- Added a storage-root separation invariant and `STORAGE_ROOT_OVERLAP` audit
  finding so configured roots cannot silently collapse lifecycle boundaries.
- Added non-normative classification examples for Admin/project documents,
  local and remote-backed Git repositories, agent worktrees, corpora/checkpoints,
  and regenerable build state without turning examples into automatic policy.
- Defined an audit-first `taurworks storage` command direction with versioned
  JSON output and one `taurworks-storage-audit` Agent Skill backed by the CLI.
- Staged mutating storage operations after read-only audit dogfooding.
- Updated `project/design/README.md` to index the lifecycle-managed proposal.
- Opened draft PR #106 for semantic review.

# Validation

- Reviewed `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, existing Taurworks design
  documents, and execution-record conventions.
- Reviewed LRH `lrh-design` and `lrh-proposal` skill guidance, proposal schema,
  body conventions, and validator discovery semantics.
- Self-review found and corrected the initial flat `project/design/storage_model.md`
  placement: LRH discovers design proposals only beneath
  `project/design/proposals/`, so the proposal now lives in the `proposed`
  lifecycle bucket matching its `status`.
- Searched Taurworks for existing storage/symlink design scope and found no
  duplicate storage subsystem or matching backlog item.
- Python CI passed on the earlier documentation-only PR head; the updated head
  should be allowed to run CI again before merge.
- No executable code changed; local runtime tests were not run from this
  GitHub-only session.

# Follow-up

Review the revised PR #106 and let CI complete on the updated head. If adopted,
update canonical Taurworks design/config artifacts and derive staged
implementation work beginning with read-only `taurworks storage show` and
`taurworks storage audit --format md|json`.
