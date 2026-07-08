---
id: FOCUS-CURRENT
title: Legacy migration tooling and side-effect audit follow-ups
status: active
updated: 2026-07-06
basis: activation_config_slices_1_3_complete
confidence: high
---

# Current Focus

Taurworks has completed global resolution (XDG-style global config, explicit
workspace root, global project registry, and workspace/registry-aware `tw
projects`/`tw activate` resolution) and the first three declarative-activation
slices (`[activation].message`, `[activation.exports]`, and Conda environment
activation). Focus now shifts to the remaining `WI-ACTIVATION-CONFIG-0001`
slices, the still-untracked side-effect audit follow-ups, and deciding how far
to take `taurworks dev ...` beyond read-only diagnostics.

## Active direction

1. Design and implement `taurworks legacy inspect PROJECT` as conservative,
   read-only extraction of `Admin/project-setup.source` patterns.
2. Design and implement `taurworks legacy migrate PROJECT --apply` for simple
   detected patterns, preserving existing config and requiring manual review
   for unsupported shell constructs.
3. Address the side-effect audit's outstanding recommendations
   (`project/audits/side_effects.md`), most notably that legacy top-level
   `taurworks refresh`/`taurworks create` (and therefore `tw refresh`/`tw
   create`) still create a Conda environment by default despite sounding like
   safe metadata operations.
4. Defer trusted user-script hooks until legacy inspect/migrate has been
   dogfooded; require explicit opt-in, warnings, inspection/dry-run modes, and
   per-project trust when that design work starts.
5. Keep `taurworks project activate --print` read-only and `tw activate` as the
   only shell-mutating layer.

## In scope now

- Legacy `Admin/project-setup.source` inspect/migrate tooling design and
  implementation.
- Side-effect audit follow-ups: gating legacy Conda environment creation
  behind an explicit command/flag, reducing `tw activate`'s `eval` surface,
  and treating `taurworks project activate --shell` output as sensitive.
- Deciding scope for `taurworks dev ...` workflow automation beyond `dev
  where`/`dev status`.

## Out of scope now

- Implementing trusted user-script hooks before legacy inspect/migrate is
  dogfooded.
- Automatic legacy `Admin/project-setup.source` fallback sourcing.
- Broad repo workflow automation under `taurworks dev ...` without further
  design.
- Shell startup-file edits.
- Multi-repo project management.
- Breaking command renames or removals.

## Already implemented (do not re-plan)

- XDG-style global config: `taurworks config where`, `taurworks workspace
  show`, `taurworks workspace set PATH`.
- Global project registry: `taurworks project register/unregister`,
  `taurworks project registry list`.
- Workspace/registry-aware `tw projects`/`taurworks projects` listing and
  `tw activate NAME` resolution, per the canonical priority list in
  `project/design/config_model.md`.
- Declarative activation message, exports, and Conda environment activation.
- Minimal read-only `taurworks dev where`/`dev status`.

## Safety stance

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating function from sourced taurworks-shell.sh
  (cd, configured exports, configured Conda activation)

workspace-only / legacy-admin fallback
  cd only, with warning

legacy Admin/project-setup.source
  recognized for migration/design, not automatic sourcing

user scripts/hooks
  future explicit opt-in only
```

Automatic sourcing of legacy project setup scripts is intentionally deferred
because it crosses a stronger trust boundary than `cd`-only activation.
