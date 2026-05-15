---
updated: 2026-05-15
basis: global_config_activation_design
confidence: high
---

# Current Focus

Taurworks is currently focused on **global resolution and activation design alignment**. The `project_root` / `working_dir` metadata model remains correct, and dogfooding showed that Taurworks now needs a configured workspace root and explicit project registry so `tw projects` and `tw activate` can resolve projects reliably from anywhere before activation becomes richer.

## Active direction

1. Design Phase 1a XDG-style global config and explicit workspace root commands.
2. Design Phase 1b global project registry commands for projects outside immediate workspace discovery.
3. Design Phase 1c workspace/registry-aware `tw projects` and `tw activate` resolution from anywhere, with the canonical priority list maintained in `project/design/config_model.md`.
4. Preserve `taurworks project activate --print` as read-only guidance and `tw activate` as the explicit shell-mutating wrapper.
5. Keep workspace-only and legacy-admin fallback activation to `cd`-only with warnings.
6. Design Phase 2 declarative `.taurworks/config.toml` activation for messages, environment strategies, and exports without arbitrary script sourcing.
7. Defer user scripts/hooks to a future explicit opt-in trust model with inspection and dry-run support.

## In scope now

- Control-plane documentation for the next PR sequence after the global resolution gap found during dogfooding.
- XDG-style global config and workspace-root design.
- Global project registry design for intentionally nested or unusual project locations.
- Workspace/registry-aware project listing and activation resolution design.
- Declarative activation config design for readiness messages, Conda/venv-style environments, and exports.
- Future safe user-script support boundaries: explicit opt-in, warnings, inspection/dry-run, per-project trust, and no default legacy sourcing.

## Out of scope now

- Implementing behavior changes in this design-alignment PR.
- Changing the core `tw activate` activation behavior in this design PR.
- Adding automatic legacy `Admin/project-setup.source` fallback sourcing.
- Sourcing legacy-admin scripts or treating them as more than `cd`-only warning fallbacks before explicit migration/trust design.
- Broad repo workflow automation under `taurworks dev ...`.
- Shell startup-file edits.
- Multi-repo project management.
- Breaking command renames or removals.

## Safety stance

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating function from sourced taurworks-shell.sh

workspace-only / legacy-admin fallback
  cd only, with warning

legacy Admin/project-setup.source
  recognized for migration/design, not automatic sourcing

user scripts/hooks
  future explicit opt-in only
```

Automatic sourcing of legacy project setup scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
