---
id: WI-ACTIVATION-CONFIG-0001
status: active
---

# WI-ACTIVATION-CONFIG-0001: Implement declarative activation config

## Status
Planned implementation package after Phase 1 dogfooding.

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
  shell quoting, documented leading `~` expansion, and secret-conscious output;
- future trusted hooks behind explicit opt-in only;
- legacy inspect/migrate commands that prefer declarative fields over copying or
  executing scripts.

## Non-goals
This work item must not introduce:

- automatic legacy `Admin/project-setup.source` sourcing;
- arbitrary user-command execution by default;
- shell startup-file edits;
- automatic `conda init`;
- secret values in normal output;
- shell-state mutation from `taurworks project activate --print`.

## Implementation slices
1. Implement activation message and exports.
2. Implement Conda activation in `tw activate` without running `conda init`.
3. Implement `taurworks legacy inspect PROJECT` as conservative read-only
   extraction.
4. Implement `taurworks legacy migrate PROJECT --apply` for simple scripts while
   preserving existing config and requiring manual review for unsupported shell.
5. Design and implement trusted hooks only after declarative activation has been
   dogfooded.

## Validation expectations
Each implementation slice should include unit tests for parsing, validation,
rendering, failure modes, and safety boundaries, plus the repository standard
format/lint/test checks.
