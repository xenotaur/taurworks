---
id: FOCUS-CURRENT
title: Side-effect audit follow-ups and tl-compatible legacy retirement automation
status: active
updated: 2026-07-22
basis: legacy_migration_and_trust_gating_complete
confidence: high
---

# Current Focus

Legacy `Admin/project-setup.source` inspect/migrate tooling, trust-gated
legacy sourcing, the `tl` break-glass helper, and the stale-shell-helper fix
(`tw shell refresh`) are all implemented and merged. Real-workspace
dogfooding (2026-07-11 through 2026-07-22) found and fixed a further class
of bug: a project can be fully migrated to declarative `config.toml` while
its now-redundant `Admin/project-setup.source` lingers, which risks silently
duplicating declarative activation behavior if the script is ever trusted.
Focus now shifts to `WI-LEGACY-MIGRATE-TL-FALLBACK-0001`, which automates
the by-hand retirement recipe found during that dogfooding, and to deciding
whether to formalize the two side-effect audit recommendations that were
never captured as work items.

## Active direction

1. `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` (in progress): teach
   `taurworks legacy migrate --apply` an opt-in `--keep-tl-fallback` flag
   that moves a fully-covered `Admin/project-setup.source` to
   `.taurworks/project-setup.source` (`tl`'s existing fallback location),
   gated on the migration being fully literal (`unsupported_count == 0`) so
   a partial migration is never silently retired with behavior lost.
2. Decide whether to formalize two still-open side-effect audit
   recommendations (`project/audits/side_effects.md`) as work items: wiring
   `scripts/audit-side-effects` into CI as an enforced gate (recommendation
   #7), and whether to pursue making legacy `taurworks refresh`/`create`
   fully metadata-only (recommendation #1 in full; open question tracked in
   `WI-LEGACY-CONDA-GATING-0001`'s Open Questions).
3. Keep `taurworks project activate --print` read-only and `tw activate`/
   `tw shell refresh` as the only shell-mutating layers.

## In scope now

- Landing `WI-LEGACY-MIGRATE-TL-FALLBACK-0001`.
- Deciding whether/how to formalize the two remaining side-effect audit
  follow-ups above as work items.
- Deciding scope for `taurworks dev ...` workflow automation beyond `dev
  where`/`dev status`.

## Out of scope now

- Upgrading the `legacy migrate` matcher to handle variable indirection
  (explicitly not planned per `project/roadmap/roadmap.md`; zero external
  users; superseded by the one-time real-corpus batch migration).
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
- Minimal read-only `taurworks dev where`/`dev status`.

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
