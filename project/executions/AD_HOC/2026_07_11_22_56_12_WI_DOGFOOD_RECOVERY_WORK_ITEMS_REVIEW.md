---
execution_id: 2026_07_11_22_56_12_WI_DOGFOOD_RECOVERY_WORK_ITEMS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_DOGFOOD_RECOVERY_WORK_ITEMS_REVIEW)[2026-07-11T21:21:58-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/66
commit: 98ca395
created_at: 2026-07-11T22:56:12-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/66
session_transcript: pending
---

# Summary

Address the four open review comments on PR #66 (dogfood recovery plan work
items and roadmap amendment): one Codex P2 comment and three Copilot
comments, all doc-level changes to two proposed work items and the roadmap.

`rerun_of` is empty because PR #66 was created via the `/lrh-work-item`
skill (planning artifacts), not `/lrh-implement`, so no primary execution
record exists for this branch.

# Result

All four comments were valid and fixed (commit 98ca395):

1. **Codex P2 — trust records would break registry handling.** Confirmed:
   `project_registry._project_entry_root` requires a non-empty `root` on
   every `[projects.NAME]` entry and the registry list iterates all entries.
   WI-TRUSTED-LEGACY-SOURCING-0001 now specifies a dedicated `[trust.NAME]`
   table, separate from the registry, with the rationale recorded.
2. **Copilot — ambiguous trust command spellings.** Full nested forms
   specified: `taurworks project trust set NAME`,
   `taurworks project trust unset NAME`, `taurworks project trust list`,
   matching the `project registry list` / `project working-dir set/show`
   style.
3. **Copilot — personal checkout path in README snippet.**
   WI-INTERIM-TL-PIPX-0001 now uses `<path-to-checkout>` and explicitly
   requires reconciling the README's existing `pipx install taurworks` /
   `pip install taurworks` guidance (unpublishable — PyPI is out of scope).
4. **Copilot — roadmap/README contradiction on pipx.** The roadmap's PyPI
   out-of-scope bullet now notes the README guidance is reconciled by
   WI-INTERIM-TL-PIPX-0001.

Nothing was skipped.

# Validation

- `scripts/version tools` — not present in this repo; equivalent direct
  commands used: Python 3.11.8, black 26.3.1, ruff 0.15.12
- `scripts/format --check --diff` — 26 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 193 tests OK (23.4s)
- `lrh validate` — no new errors (4 known pre-existing
  `contributors.md` errors remain)
- `lrh work-items readiness --status proposed` — 4/4 prompt-ready

# Follow-up

- Update `session_transcript` from `pending` to `claude-app:<session-id>`
  after the session ends.
- On merge: set `status: landed` here, and resolve review conversations on
  GitHub (human decision).
