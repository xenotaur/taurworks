---
id: FOCUS-CURRENT
title: Packaging/install cleanup complete; legacy-migrate-tl-fallback deferred
status: active
updated: 2026-07-30
basis: packaging_and_install_series_resolved_legacy_migrate_deferred
confidence: high
---

# Current Focus

`project/design/packaging_and_install.md`'s four-gap packaging/install audit
is fully landed: the repo/package split (`WI-BIN-REPO-SPLIT-0001`, PR #88),
the one-step `taurworks setup` install command (`WI-TAURWORKS-SETUP-0001`,
PR #93), the `tw` PATH-loss diagnostic (`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`,
PR #94), and the `--debug`/`TAURWORKS_DEBUG` flag
(`WI-TAURWORKS-DEBUG-FLAG-0001`, PR #95) are all resolved. This design is
fully delivered; no further work is planned against it without a new need
being raised.

`WI-LEGACY-MIGRATE-TL-FALLBACK-0001` (automating
`Admin/project-setup.source` retirement once a project is fully migrated to
declarative `config.toml`) remains proposed rather than active. It is being
deliberately held — possibly permanently — pending confirmation, now that
the packaging work above has landed, that legacy `Admin/project-setup.source`
projects still exist that would actually benefit from it.

The two side-effect audit recommendations that were never captured as work
items remain assessed-and-deferred in `project/design/backlog.md`
(unchanged since 2026-07-23).

## Active direction

1. Confirm whether `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` is still needed,
   now that the packaging/install work has landed — do not pick it up
   without first confirming it's still needed.
2. Deciding scope for `taurworks dev ...` workflow automation beyond `dev
   where`/`dev status` remains an open, undecided question.
3. Keep `taurworks project activate --print` read-only and `tw activate`/
   `tw shell refresh` as the only shell-mutating layers.

## In scope now

- Confirming whether `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` is still needed.
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
- One-step `taurworks setup` install command plus `scripts/install`,
  XDG-aware `tw`/`tl` shell-helper placement kept in sync with `tw shell
  refresh` (`WI-TAURWORKS-SETUP-0001`).
- `tw` Conda PATH-loss diagnostic covering all 8 `command taurworks ...`
  call sites in the shell helper (`WI-TW-PATH-LOSS-DIAGNOSTIC-0001`).
- `--debug`/`TAURWORKS_DEBUG` flag gating `manager.py`'s narration prints,
  with `cli.py`'s formatter modules audited for debug-shaped output
  (`WI-TAURWORKS-DEBUG-FLAG-0001`).
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
