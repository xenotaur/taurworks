---
execution_id: 2026_07_18_23_40_50_WI_TL_BREAKGLASS_0001_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TL_BREAKGLASS_0001_IMPL_REVIEW)[2026-07-18T23:31:19-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_18_23_25_02_WI_TL_BREAKGLASS_0001
pr: https://github.com/xenotaur/taurworks/pull/73
commit: b5ebc39
created_at: 2026-07-18T23:40:50-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/73
session_transcript: pending
---

# Summary

Address one open review comment on PR #73 (WI-TL-BREAKGLASS-0001
implementation): the trusted-branch legacy-admin guidance unconditionally
claimed sourcing "will be sourced automatically," which is wrong whenever
`--no-legacy` is passed.

# Result

Verified valid by tracing `taurworks-shell.sh`'s `_tw_activate`: the entire
legacy-sourcing block (line 312, `if [ "$legacy_setup_exists" = "True" ] &&
[ "$no_legacy" != "1" ]`) -- including the trusted branch -- is skipped when
`--no-legacy` is passed, regardless of trust status. `--no-legacy` is
shell-only state never sent to the Python diagnostics layer, so my original
3-way conditional's "trusted + enabled -> will be sourced automatically"
branch was itself non-deterministic, the same class of bug the WI was
fixing in the first place.

Fixed (commit b5ebc39): collapsed the guidance conditional in
`src/taurworks/project_resolution.py` from 3-way to 2-way. Only "Tier 1
disabled" remains a deterministic assertion ("was not sourced" -- true
regardless of any shell-only flag, since the whole legacy block is a no-op
when Tier 1 is off). Every "Tier 1 enabled" case, trusted or not, now gets
the same neutral wording: sourcing "depends on trust status and
--legacy/--no-legacy choices made by tw activate."

Updated the two regression tests in `tests/project_resolution_test.py`
added by the primary implementation: the trusted+enabled test (renamed
`test_trusted_and_enabled_guidance_is_also_outcome_neutral`) now asserts
the neutral wording instead of the removed "will be sourced automatically"
claim; the untrusted+enabled test's assertion was updated to match the
updated neutral wording.

Nothing was skipped.

# Validation

- Python 3.11.10, black 26.3.1, ruff 0.15.12 (Taurworks pinned conda env)
- `scripts/format --check --diff` -- 28 files unchanged
- `scripts/lint` -- all checks passed
- `scripts/test` -- 281 tests OK
- `lrh validate` -- no new errors (4 known pre-existing `contributors.md`
  errors remain)

# Follow-up

- On merge: closeout via `/lrh-closeout` (mark this record and the primary
  record landed, resolve `WI-TL-BREAKGLASS-0001`).
- Resolving the GitHub review conversation is a human action.
