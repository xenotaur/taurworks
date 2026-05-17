# Current Status

## Maturity snapshot
Taurworks is in a design-alignment phase moving from successful local `tw activate` dogfooding toward global workspace/registry resolution, status-aware project listing, and safe declarative activation planning while preserving current activation behavior.

## Current direction (documented)
- One primary executable: `taurworks`.
- Namespaced workspace lifecycle commands: `taurworks project ...`.
- Namespaced repo workflow commands: `taurworks dev ...`.
- Shared discovery/configuration core across namespaces.
- Planned XDG-style user config at `$XDG_CONFIG_HOME/taurworks/config.toml`, falling back to `~/.config/taurworks/config.toml`.
- Planned explicit workspace root and global project registry for projects outside immediate workspace discovery.
- Compatibility coverage for existing top-level commands (`create`, `refresh`, `activate`, `projects`).
- Explicit separation between read-only/path-emitting CLI commands and shell-mutating sourced `taurworks-shell.sh` `tw activate`; `tw root PROJECT` and `tw working PROJECT` are non-mutating convenience aliases for path composition.

## Implemented minimal project and dev slices
- `taurworks help` is equivalent to `taurworks --help`; `taurworks help COMMAND` routes to existing command help for current namespaces.
- `taurworks project --help` documents the project namespace and available discovery commands.
- `taurworks project where` provides read-only project/config/discovery diagnostics.
- `taurworks project list` provides read-only discovery listing and clear no-project behavior.
- `taurworks project refresh`, `taurworks project init`, `taurworks project create`, working-directory metadata commands, script-friendly `taurworks project root PROJECT` / `taurworks project working PROJECT` path emitters, and `taurworks project activate --print` provide safe scaffolding, composition paths, and inspectable guidance for initialized projects. Dogfooding confirmed that the sourced `taurworks-shell.sh` `tw activate` helper can use that guidance to change into the configured working directory.
- `taurworks dev --help`, `taurworks dev where`, and `taurworks dev status` provide minimal read-only repository/developer workflow diagnostics without running VCS commands or workflow automation.

## What this phase prioritizes
- Designing Phase 1a global config commands: `taurworks config where`, `taurworks workspace show`, and `taurworks workspace set PATH`.
- Designing Phase 1b registry commands: `taurworks project register NAME PATH`, `taurworks project unregister NAME`, and `taurworks project registry list`.
- Designing Phase 1c workspace/registry-aware `tw projects` and `taurworks projects` list merging.
- Designing stable `tw activate NAME` resolution from anywhere, with the canonical priority list maintained in `project/design/config_model.md` and registered projects preferred before workspace and local fallbacks.
- Keeping initialized-without-working-dir, workspace-only, and legacy-admin fallbacks to `cd`-only with warnings.
- Designing Phase 2 declarative activation for readiness messages, environment strategies, and exports without arbitrary script sourcing.
- Deferring scripts/hooks to future explicit opt-in trust design with warnings, inspection/dry-run, and per-project trust.

## What remains future implementation work
- Implementing XDG global config and workspace commands.
- Implementing global project registry commands.
- Implementing workspace/registry-aware project list and activation resolution.
- Expanding `taurworks dev ...` beyond read-only diagnostics into workflow automation.
- Implementing declarative activation in separate slices after design approval.
- Automatic legacy `Admin/project-setup.source` migration tooling.
- Multi-repo project management.
- Finalized migration/deprecation mechanics for compatibility commands.
- Expanded diagnostics and dry-run support across all command paths.

Automatic sourcing of legacy `Admin/project-setup.source` scripts is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
