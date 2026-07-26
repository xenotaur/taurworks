---
id: FOCUS-CURRENT
title: Packaging/install cleanup (tracked separately); legacy-migrate-tl-fallback deferred
status: active
updated: 2026-07-25
basis: bin_repo_split_resolved_legacy_migrate_deferred
confidence: high
---

# Current Focus

`project/design/packaging_and_install.md`'s four-gap packaging/install audit
is partially landed: the repo/package split (`WI-BIN-REPO-SPLIT-0001`) is
resolved. The remaining three gaps — a one-step `taurworks setup` install
command, a `tw` PATH-loss diagnostic, and a `--debug` flag to gate
`manager.py`'s narration — remain proposed and ready to implement
(`WI-TAURWORKS-SETUP-0001`, `WI-TW-PATH-LOSS-DIAGNOSTIC-0001`,
`WI-TAURWORKS-DEBUG-FLAG-0001`). That work is tracked in a separate thread,
not this one.

`WI-LEGACY-MIGRATE-TL-FALLBACK-0001` (automating
`Admin/project-setup.source` retirement once a project is fully migrated to
declarative `config.toml`) remains proposed rather than active. It is being
deliberately held — possibly permanently — pending confirmation, after the
packaging work above lands, that legacy `Admin/project-setup.source`
projects still exist that would actually benefit from it.

The two side-effect audit recommendations that were never captured as work
items remain assessed-and-deferred in `project/design/backlog.md`
(unchanged since 2026-07-23).

## Active direction

1. Packaging/install cleanup (tracked in a separate thread): implement
   `taurworks setup` + `scripts/install` (`WI-TAURWORKS-SETUP-0001`), the
   `tw` PATH-loss diagnostic (`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`), and the
   `--debug`/`TAURWORKS_DEBUG` flag (`WI-TAURWORKS-DEBUG-FLAG-0001`). All
   three are prompt-ready with no blockers.
2. `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` stays deferred — do not pick it up
   without first confirming it's still needed.
3. Deciding scope for `taurworks dev ...` workflow automation beyond `dev
   where`/`dev status` remains an open, undecided question.
4. Keep `taurworks project activate --print` read-only and `tw activate`/
   `tw shell refresh` as the only shell-mutating layers.

## In scope now

- Landing the three proposed packaging/install work items (tracked
  separately from this focus document's own thread).
- Deciding `taurworks dev ...` workflow-automation scope.

## Out of scope now

- Implementing `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` without first
  confirming it's still needed.
- Upgrading the `legacy migrate` matcher to handle variable indirection
  (explicitly not planned; zero external users; superseded by the
  one-time real-corpus batch migration).
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
- `taurworks legacy inspect`/`taurworks legacy migrate --apply`
  (`WI-ACTIVATION-CONFIG-0001`), plus the one-time human-reviewed batch
  migration of the real legacy corpus (`WI-LEGACY-BATCH-MIGRATION-0001`).
- Trust-gated legacy script sourcing, two-tier consent model
  (`WI-TRUSTED-LEGACY-SOURCING-0001`).
- `tl` simplified and reframed as a permanent, dependency-free break-glass
  fallback (`WI-INTERIM-TL-PIPX-0001`, `WI-TL-BREAKGLASS-0001`).
- `tw shell refresh`, fixing the stale-shell-helper problem
  (`WI-SHELL-HELPER-REFRESH-0001`).
- Conda environment creation gated behind explicit `--create-env`
  (`WI-LEGACY-CONDA-GATING-0001`); most other side-effect audit
  recommendations resolved or reviewed-and-accepted (see
  `project/audits/side_effects.md` for full per-recommendation status).
- `bin/`'s personal-dotfile material split into a separate sibling repo
  (`xenotaur/taurscripts`, with full history preserved),
  `migrate_legacy_projects.py` relocated under the package, and
  `sourceme/` wired into `setup.py` packaging (`WI-BIN-REPO-SPLIT-0001`).
- Minimal read-only `taurworks dev where`/`dev status`.
- Contributors roster (`project/contributors/*.md`) replacing the
  previously-broken placeholder.

## Safety stance

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating function from sourced taurworks-shell.sh
  (cd, configured exports, configured Conda activation, trust-gated
  legacy sourcing)

tw shell refresh
  explicit shell-mutating function that regenerates and re-sources the
  helper itself

tl
  permanent, dependency-free break-glass fallback; never depends on tw
  or the installed taurworks package version

workspace-only / legacy-admin fallback
  cd only, with warning

legacy Admin/project-setup.source
  sourced only behind explicit two-tier trust consent, never by default
```

Automatic (unconsented) sourcing of legacy project setup scripts remains
out of scope; the implemented model requires an explicit user-global
enable switch plus per-project content-digest trust, both recorded outside
the project itself.
