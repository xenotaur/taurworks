---
execution_id: 2026_11_11_05_46_07_WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKING_DIR_REVERSE_DISCOVERY_0001_IMPL_REVIEW)[2026-11-11T05:13:13+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_11_03_45_54_WI_WORKING_DIR_REVERSE_DISCOVERY_0001
pr: https://github.com/xenotaur/taurworks/pull/119
commit:
created_at: 2026-11-11T05:46:07+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/taurworks/pull/119
session_transcript: pending
---

# Summary

Review-response for PR #119 (the WI-WORKING-DIR-REVERSE-DISCOVERY-0001
implementation), run inline from `/lrh-land` within `/lrh-execute`. One
Copilot thread on `a85ebe2`; Codex reported no findings on `e9429c3`. The
user approved the fix at the confirm gate.

# Result

- **The finding:** a workspace project whose `.taurworks/config.toml` isn't
  valid UTF-8 made `tomllib.load()` raise `UnicodeDecodeError`, which
  `classify_project_entry()` didn't catch. That aborted the reverse lookup
  with a traceback even when another project matched.
- **Reproduced:** `dev where` from a matching external target crashed with
  `UnicodeDecodeError`.
- **Fixed in `fe7391a`:** `UnicodeDecodeError` added to
  `classify_project_entry`'s per-project handler. The entry is now
  classified as having invalid activation metadata and is skipped by the
  lookup.
- **Regression test:**
  `manager_test.ReverseDiscoveryTest.test_non_utf8_project_config_is_skipped_not_fatal`.

# Validation

- `./scripts/format --check --diff`: pass
- `./scripts/lint`: pass
- `./scripts/test`: 394 tests OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Confirm-fixes on the new head.
