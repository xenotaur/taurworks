---
id: ROADMAP-INIT
title: Unified Taurworks Direction Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing

This roadmap is phased and conservative. It prioritizes command-model alignment, safe incremental delivery, and explicit trust boundaries.

## Current phase snapshot (2026-07-31)

Phases 1 through 5A below, and the entire dogfood recovery plan
(`WI-INTERIM-TL-PIPX-0001`, `WI-LEGACY-BATCH-MIGRATION-0001`,
`WI-ACTIVATION-PRODUCERS-0001`, `WI-TRUSTED-LEGACY-SOURCING-0001`), are
implemented and merged. So is the follow-up simplification of `tl` into a
permanent break-glass fallback (`WI-TL-BREAKGLASS-0001`) and the fix for a
separate stale-shell-helper problem, `tw shell refresh`
(`WI-SHELL-HELPER-REFRESH-0001`).

A packaging/install audit (`project/design/packaging_and_install.md`, design
discussion 2026-07-22) found four gaps in taurworks' installability on a
machine other than its original author's. All four are now resolved (Phase
8 below is done): the repo/package split (`WI-BIN-REPO-SPLIT-0001`), the
one-step `taurworks setup` install command (`WI-TAURWORKS-SETUP-0001`), the
`tw` PATH-loss diagnostic (`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`), and the
`--debug`/`TAURWORKS_DEBUG` flag (`WI-TAURWORKS-DEBUG-FLAG-0001`). This
design is fully delivered; no further work is planned against it without a
new need being raised.

`WI-LEGACY-MIGRATE-TL-FALLBACK-0001` — automating retirement of a
now-redundant `Admin/project-setup.source` once a project is fully migrated
to declarative `config.toml`, found during 2026-07-22 real-workspace
dogfooding — was deliberately held pending confirmation that legacy
`Admin/project-setup.source` projects still existed needing it. A direct
audit of the real workspace on 2026-07-31 answered that: no
`Admin/project-setup.source` file remains anywhere; all 11 projects
identified during the 2026-07-22 dogfooding were already retired by hand.
The item is abandoned (`project/work_items/abandoned/`) rather than
implemented. The two side-effect audit recommendations that were never
captured as work items remain assessed and deferred to
`project/design/backlog.md` (see below).

`taurworks dev ...` workflow-automation scope (Phase 6 below) is now
decided: a delegate-only v1 (`clean`, `test`, `smoke`, `lint`, `format`,
`build`), with higher-risk commands (including `develop`, which is
dependency-mutating in this repo) deferred. Not yet implemented.

### In scope now

- Implementing Phase 6's v1 `taurworks dev ...` delegation scope.

### Out of scope now

- Automatic (unconsented) fallback sourcing of `Admin/project-setup.source`.
- General-purpose `legacy migrate` matcher upgrades to handle variable
  indirection (superseded by the one-time batch migration; still not
  planned, zero external users).
- venv/Docker/devcontainer environment activation strategies.
- The higher-risk `dev` commands deferred in Phase 6, and any built-in
  per-project-type default (Tier 3 of the resolution model) before
  delegate-only v1 is proven.
- Shell startup-file edits and automatic `conda init`.
- Multi-repo project management.
- Breaking removals or renames of compatibility commands.
- Broad refactors unrelated to project metadata and shell UX alignment.
- Publishing to PyPI (pipx installs from the local checkout; the README's
  current `pipx install taurworks` guidance is reconciled to the
  local-checkout form by WI-INTERIM-TL-PIPX-0001).

## Phase 1 — Document unified product direction (done)

- Align project artifacts around one executable: `taurworks`.
- Document `taurworks project ...` and `taurworks dev ...` responsibilities.
- Preserve current top-level commands as compatibility commands.

## Phase 2 — Formalize config/state model (done)

- Define precedence and config discovery behavior.
- Align XDG-style global config/state/cache with visible project-local metadata and repo-local workflow config.

## Phase 2A0 — Add XDG global config and workspace root (done)

- Use `$XDG_CONFIG_HOME/taurworks/config.toml`, falling back to `~/.config/taurworks/config.toml`.
- Store an explicit `[workspace].root` in schema version 1 global config.
- Implemented commands: `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`.
- `~/Workspace` is inferred only as non-mutating first-run inference when it exists and no config exists; explicit configuration is required before persisting state or treating it as authoritative.

## Phase 2A1 — Add global project registry (done)

- Store explicit registered project roots under `[projects.NAME]` in global config.
- Implemented commands: `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`.
- Support intentionally weird or nested project locations without recursive scanning by default.
- Report stale registry paths without silently deleting user intent.

## Phase 2A2 — Make listing and activation workspace/registry-aware (done)

- Merge registered projects, immediate workspace-root children, initialized projects, legacy-admin projects, and workspace-only projects in `tw projects` / `taurworks projects`.
- Resolve `tw activate NAME` from anywhere using the canonical priority in `project/design/config_model.md`: registered project, initialized workspace project, legacy-admin workspace project, workspace-only directory, local/enclosing fallback, then child path only for explicitly local commands.
- Script-friendly `tw project root PROJECT`, `tw project working PROJECT`, `tw root PROJECT`, and `tw working PROJECT` path emitters use the same resolution core; stdout remains path-only for shell composition.
- Fallback activation stays conservative: initialized projects with `working_dir` cd there; initialized without `working_dir`, workspace-only, and legacy-admin cd to project root with warnings; legacy scripts are not sourced by default.

## Phase 2A — Align project-root and working-directory metadata (done)

- `project_root` is the directory containing `.taurworks/`.
- `working_dir` is the default code/work directory, stored relative to `project_root` in `.taurworks/config.toml`.
- Absolute working-directory paths are rejected/deferred until explicitly designed.
- Empty project names in existing configs are treated as legacy metadata and repaired.
- `project working-dir show/set` shipped before activation behavior changed.

## Phase 2B — Resolve project init/create and working-directory dogfood findings (done)

- `project init [PATH] [--working-dir DIR] [--create-working-dir]` safely and idempotently initializes existing/current project roots.
- `project create NAME [--working-dir DIR] [--create-working-dir] [--nested]` creates a new project root, delegates to init/refresh, and refuses accidental nested same-name creation unless `--nested` is supplied.
- Target resolution is centralized for project lifecycle, working-directory, and read-only activation commands with diagnostics that show `input`, `project_root`, and `resolved_by`.
- `project working-dir show [PATH_OR_NAME]` is target-aware; `project working-dir set DIR --project PATH_OR_NAME` is the preferred mutation shape.
- `--create-working-dir` or `working-dir set --create` is required before creating missing working directories.
- `project activate --print` uses the shared resolver while remaining read-only.

## Phase 2C — Polish explicit shell activation (done)

- `taurworks project activate --print` remains read-only activation guidance.
- `tw activate` is shell-mutating only through the explicitly sourced `taurworks-shell.sh` function.
- Default `tw activate` output is concise; detailed diagnostics live behind `--verbose`/`--debug`.
- Missing project and missing working-directory failures stay concise by default.
- `tw help` is an alias for `tw --help`.

## Phase 2D — Classify project-list status (done)

- `tw projects` / `taurworks projects` distinguish initialized projects with `.taurworks/config.toml`, workspace-only directories, and legacy-admin directories with `Admin/project-setup.source`.
- Superseded by Phase 2A2 for activation targets: initialized projects remain the richest activation targets, while initialized-without-working-dir, workspace-only, and legacy-admin projects may be `cd`-only warning fallbacks.
- Legacy-admin fallback sourcing is not default behavior.
- Old `Admin/project-setup.source` scripts remain for a future explicit migration or trust flow (Phase 5/5A).

## Phase 3 — Introduce/document namespaced project lifecycle (done)

- `taurworks project` namespace covers lifecycle operations.
- Existing `create`, `refresh`, `activate`, and `projects` command behavior is preserved during transition.

## Phase 4 — Add minimal read-only `taurworks dev` scaffold (done)

- `taurworks dev ...` was introduced conservatively.
- Safe diagnostics: `dev where` and `dev status`.
- The scaffold remains read-only: it reports workspace context and future VCS automation boundaries without running workflow commands.
- `dev test`, `dev clean`, and other workflow automation remain deferred until trust boundaries are clear (see "In scope now").

## Phase 5 — Design and implement declarative activation (message/exports/Conda done; venv/Docker/hooks deferred)

- Readiness messages such as "Ready for work on project X" are implemented (`[activation].message`).
- `[activation.exports]` declarative environment data is implemented.
- Conda environment activation (`[activation.environment] type = "conda"`) is implemented in `tw activate`.
- venv, Docker/devcontainer, and other environment activation strategies remain deferred to separate designs.
- `taurworks legacy inspect PROJECT` and `taurworks legacy migrate PROJECT --apply` are implemented (`WI-ACTIVATION-CONFIG-0001`, PR #65). Dogfooding found the migrate matcher handles none of the 12 real legacy scripts (variable indirection); rather than generalizing the matcher, the real corpus is being migrated once via `WI-LEGACY-BATCH-MIGRATION-0001`, and the missing producer commands are tracked in `WI-ACTIVATION-PRODUCERS-0001`.
- Arbitrary user-script sourcing remains out of scope for this phase.

## Phase 5A — Trust-gated legacy script sourcing (re-scoped 2026-07-11, done)

- Re-scoped after dogfooding: instead of a new hook-file schema, the first
  trusted "hook" is the existing legacy `Admin/project-setup.source`,
  sourced by `tw activate` behind a two-tier consent model
  (WI-TRUSTED-LEGACY-SOURCING-0001).
- Tier 1: a user-global enable switch in XDG config, off by default; while
  off, behavior is unchanged and prompt-free.
- Tier 2: per-project trust records (script path plus sha256 content digest)
  stored only in the user-owned global config — never inside the project, so
  arriving content cannot approve itself. Content changes force re-consent.
- First-use prompts show an inspect-style summary; `--legacy`/`--no-legacy`
  give per-invocation control; non-interactive shells fail open to cd-only.
- Preserve no default automatic legacy `Admin/project-setup.source` sourcing.
- Sizing and priority are determined by WI-LEGACY-BATCH-MIGRATION-0001's
  findings on how many projects genuinely need arbitrary shell after
  declarative migration.

## Phase 6 — `taurworks dev ...` workflow automation (scoped 2026-07-31, not yet implemented)

Scoped 2026-07-31, resolving the "deciding scope for `taurworks dev ...`
workflow automation" question this roadmap had left open since Phase 4.
`design.md`'s "Dev command resolution model" (explicit configured command
→ project-local script, e.g. `scripts/test` → built-in default by project
type) governs how each in-scope command resolves.

- **v1 scope, delegate-only** (Tiers 1-2 only; no built-in per-project-type
  defaults yet): `clean`, `test`, `smoke`, `lint`, `format`, `build`. Each
  is a conventional, expected, reversible-or-regenerable operation, and
  this repo's own `scripts/` already has a matching script to delegate to
  for dogfooding.
- **Deferred** (higher-risk: irreversible, packaging/release,
  dependency-mutating, or not-yet-semantically-defined): `init`,
  `develop`, `coverage`, `update`, `precommit`, `publish`, `sandbox`,
  `version`, `validate` — until core `dev` delegation behavior and
  guardrails are proven on the v1 set first. `develop` is grouped here,
  not v1: this repo's own `scripts/develop` runs `pip install`, making it
  dependency-mutating like `update`, not reversible like `clean`/`test`.

## Phase 7 — Define compatibility migration path (not started)

- After compatibility is preserved and namespaced commands are stable, define deprecation/migration for legacy top-level commands.

## Phase 8 — Packaging and install cleanup (done)

Prompted by `project/design/packaging_and_install.md`'s 2026-07-22 audit of
four gaps blocking taurworks from working on a machine other than its
original author's. All four are resolved:

- Repo/package split: `bin/`'s personal-dotfile material split into
  a separate sibling repo (`xenotaur/taurscripts`, full history preserved),
  `migrate_legacy_projects.py` relocated under the package, `sourceme/`
  wired into `setup.py` packaging (`WI-BIN-REPO-SPLIT-0001`, PR #88).
- One-step install/setup command: `taurworks setup` plus a
  `scripts/install` shim, superseding the prior multi-step manual install
  sequence (`WI-TAURWORKS-SETUP-0001`, PR #93).
- `tw` PATH-loss diagnostic: a clear diagnostic instead of a bare shell
  "command not found" when a Conda environment switch hides the installed
  `taurworks` executable, covering all 8 `command taurworks ...` call
  sites in the shell helper (`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`, PR #94).
- `--debug`/`TAURWORKS_DEBUG` flag: gates `manager.py`'s narration prints
  (final result lines stay unconditional) and audits `cli.py`'s formatter
  modules for debug-shaped output (none found)
  (`WI-TAURWORKS-DEBUG-FLAG-0001`, PR #95).

No further work is planned against this design without a new need being
raised.

## Design backlog

The 2026-05-17 post-merge side-effect audit (`project/audits/side_effects.md`)
produced seven follow-up recommendations; five are resolved or
reviewed-and-accepted (including the Conda-environment-creation gating
originally called out as most notable, resolved by
`WI-LEGACY-CONDA-GATING-0001`). The remaining two were assessed on
2026-07-23 and deliberately deferred rather than formalized as work
items — see `project/design/backlog.md` for the full rationale and revisit
triggers, and `project/audits/side_effects.md` for full per-recommendation
status. Deferred ideas not yet ready for a work item generally live in
`project/design/backlog.md`; check it before proposing new work.
