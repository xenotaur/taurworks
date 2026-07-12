---
id: WI-TRUSTED-LEGACY-SOURCING-0001
title: Two-tier trust-gated sourcing of legacy setup scripts in tw activate
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
---

# WI-TRUSTED-LEGACY-SOURCING-0001: Trust-gated legacy script sourcing

## Summary
Allow `tw activate` to source a project's legacy setup script behind a
two-tier consent model: a user-global enable switch, plus per-project trust
records with content digests, both stored only in the user-owned global
config — realizing the roadmap's Phase 5A intent with legacy
`Admin/project-setup.source` as the first supported "hook".

## Problem / Context
Some legacy behavior (notably `source ~/bin/utilities.source` for AWS logins)
cannot be expressed declaratively, so some projects will always need
arbitrary shell at activation. The dogfood discussions (2026-07-11) replaced
the original "never source" stance with a consent design: sourcing is safe
when the content was witnessed by an explicit user action, per the
direnv-allow precedent. Trust records must live outside the project so that
arriving content (e.g. a clone placed at a project root) can never approve
itself. WI-LEGACY-BATCH-MIGRATION-0001's review determines how many projects
actually need this; its scope or priority may shrink accordingly.

## Scope
- Tier 1: global enable switch in the XDG user config, off by default.
- Tier 2: per-project trust records (script path + sha256) in a dedicated
  `[trust.NAME]` table in the same user-owned config, with
  `taurworks project trust set/unset/list` commands.
- `tw activate` prompt-and-source flow with digest change detection and
  per-invocation override flags.

## Required Changes
1. Add a Tier 1 setting (e.g. `[activation] legacy_sourcing = false`) to the
   global config model in `src/taurworks/global_config.py`, plus a
   `taurworks config` subcommand to set/show it. While false: no prompting,
   no sourcing — current behavior exactly.
2. Add per-project trust records in a dedicated `[trust.NAME]` table in the
   global config: approved script path and sha256 content digest. Trust
   records must not live under `[projects.NAME]` — the registry requires
   every `[projects.NAME]` entry to have a non-empty `root`
   (`src/taurworks/project_registry.py` `_project_entry_root`) and the
   registry list iterates all such entries, so a trust-only entry would
   break existing registry handling. Add the commands
   `taurworks project trust set NAME`, `taurworks project trust unset NAME`,
   and `taurworks project trust list` (nested-subcommand style matching
   `taurworks project registry list` and `taurworks project working-dir
   set/show`). Records are written only by these user-invoked commands.
3. Extend the `--shell` payload
   (`src/taurworks/project_resolution.py`
   `format_project_activate_shell_output`) with legacy-script path/existence
   and trust status fields; extend `_tw_activate` in
   `src/taurworks/resources/shell/taurworks-shell.sh` to: prompt on a TTY
   when Tier 1 is on and the project is untrusted (showing a
   `legacy inspect`-style summary; choices: source once / trust / never /
   skip), source the script when trusted, and re-prompt when the digest
   mismatches.
4. Add `--legacy` (one-shot source, still requires Tier 1 on) and
   `--no-legacy` flags to `tw activate`.
5. Unit tests for config read/write, digest verification, payload fields,
   and (where feasible) the shell flow; document the model in
   `project/design/activation_extension.md`.

## Non-Goals
- Never store trust state anywhere inside the project directory
  (`.taurworks/` included) — a project must not be able to grant itself
  trust.
- No sourcing under any path when Tier 1 is off, and none without Tier 2
  consent or an explicit `--legacy` flag when it is on.
- No automatic `conda init`, no shell startup-file edits.
- No transitive hashing of files outside the project
  (e.g. `~/bin/utilities.source` — user-domain, like `.bashrc`).
- No signing, expiry, or multi-user trust machinery — direnv-level only.

## Acceptance Criteria
- With Tier 1 off (default), all activation behavior is byte-identical to
  pre-change output; no prompts appear anywhere.
- With Tier 1 on and a project untrusted, the first `tw activate` shows the
  summary prompt once; the decision persists; subsequent activations source
  without prompting.
- Editing the trusted script causes exactly one re-prompt on next activation.
- Trust records exist only in the XDG global config file; nothing in any
  project directory changed.
- In a real shell against a trusted legacy project, `tw activate` results in
  the script's Conda env, working directory, and exports being live.
- `scripts/test` passes; `lrh validate` introduces no new errors.

## Validation
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Manual shell test of prompt → trust → source → digest-change → re-prompt

## Risk Notes
- Prompting inside a sourced shell function needs a TTY guard or
  non-interactive shells will hang; `--no-legacy`/absent-TTY must fail open
  to cd-only behavior with a warning.
- The sourced script runs with full shell privileges by design; the summary
  prompt is the informed-consent moment and must not undersell that.

## Dependencies / Order
Sized and prioritized by WI-LEGACY-BATCH-MIGRATION-0001's execution record
(count of projects genuinely needing sourcing). If that count is zero, this
item may be deferred without breaking any other item.
