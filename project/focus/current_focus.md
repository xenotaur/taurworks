---
updated: 2026-05-14
basis: tw_activate_dogfood
confidence: high
---

# Current Focus

Taurworks is currently focused on **post-dogfood shell and control-plane polish**. The `project_root` / `working_dir` metadata model remains correct, and dogfooding confirmed that the explicit `tw activate` shell helper can change into a configured working directory while missing project activation fails safely.

## Active direction

1. Polish the `tw` shell UX without changing successful activation semantics.
2. Make default `tw activate` output concise, with detailed activation diagnostics available only through `--verbose` or `--debug`.
3. Keep missing project and missing working-directory failures concise by default.
4. Add `tw help` as an alias for `tw --help`.
5. Classify `tw projects` / `taurworks projects` entries as initialized, workspace-only, or legacy-admin.
6. Keep activation limited to initialized projects with `.taurworks/config.toml` for now.
7. Add a minimal read-only `taurworks dev ...` namespace scaffold, preferring safe diagnostics such as `dev where` and/or `dev status`.
8. Design future activation extensions before implementing readiness messages, environment activation, trusted startup hooks, or legacy setup migration.

## In scope now

- Control-plane documentation for the next PR sequence after successful `tw activate` dogfooding.
- UX polish for existing activation output and help aliasing.
- Project-list status vocabulary:
  - initialized projects with `.taurworks/config.toml`;
  - workspace-only directories;
  - legacy-admin directories with `Admin/project-setup.source`.
- A safe, read-only `dev` namespace scaffold.
- Activation-extension design that explicitly covers readiness messages, Conda/venv/Docker environment strategies, trusted startup hooks, legacy migration, and trust boundaries.

## Out of scope now

- Implementing behavior changes in this design-alignment PR.
- Changing the core `tw activate` activation behavior.
- Adding automatic legacy `Admin/project-setup.source` fallback sourcing.
- Treating legacy-admin projects as activation targets before migration.
- Broad repo workflow automation under `taurworks dev ...`.
- Shell startup-file edits.
- Multi-repo project management.
- Breaking command renames or removals.

## Safety stance

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating wrapper

legacy Admin/project-setup.source
  migration/design topic, not automatic fallback
```

Automatic sourcing of legacy project setup scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
