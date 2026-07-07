---
id: WI-ACTIVATION-CONFIG-0001
title: Implement declarative activation config
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
---

# WI-ACTIVATION-CONFIG-0001: Implement declarative activation config

## Status
Slices 1-3 (activation message, exports, Conda activation) are implemented and
merged. Remaining active scope is slices 4-6: legacy inspect, legacy migrate,
and trusted hooks.

## Objective
Implement the safe declarative subset of legacy activation behavior from
`.taurworks/config.toml` without automatically sourcing arbitrary project
scripts.

## Design source
Use `project/design/activation_extension.md` as the source of truth for this work
item. The design covers:

- `[activation].message` readiness text;
- `[activation.environment] type = "conda"` and `name` as the only initially
  designed environment activation strategy;
- `[activation.exports]` literal environment variable data with validation,
  shell quoting, documented leading `~` expansion, secret-conscious output, and
  a separate machine-readable payload channel for `tw activate`;
- future trusted hooks behind explicit opt-in only;
- legacy inspect/migrate commands that prefer declarative fields over copying or
  executing scripts.

## Non-goals
This work item must not introduce:

- automatic legacy `Admin/project-setup.source` sourcing;
- arbitrary user-command execution by default;
- shell startup-file edits;
- automatic `conda init`;
- secret values in normal diagnostic output;
- shell-state mutation from `taurworks project activate --print`;
- evaluating human-formatted `--print` diagnostics as shell activation payload.

## Implementation slices
1. Implement activation message only. **Done.**
2. Implement exports with a separate machine-readable payload channel for
   `tw activate` and redacted human diagnostics. **Done.**
3. Implement Conda activation in `tw activate` without running `conda init`.
   **Done.**
4. Implement `taurworks legacy inspect PROJECT` as conservative read-only
   extraction. **Remaining.**
5. Implement `taurworks legacy migrate PROJECT --apply` for simple scripts while
   preserving existing config and requiring manual review for unsupported shell.
   **Remaining.**
6. Design and implement trusted hooks only after declarative activation has been
   dogfooded. **Remaining.**

## Validation expectations
Each implementation slice should include unit tests for parsing, validation,
rendering, failure modes, and safety boundaries, plus the repository standard
format/lint/test checks.
