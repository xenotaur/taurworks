# Current Status

## Maturity snapshot
Taurworks has moved past global workspace/registry resolution and the first
declarative-activation slices, all of which are implemented and merged. The
project is now past design-alignment for that sequence; remaining work is
legacy migration tooling, deferred trusted hooks, and outstanding side-effect
audit follow-ups (see [current_focus.md](../focus/current_focus.md)).

## Current direction (documented)
- One primary executable: `taurworks`.
- Namespaced workspace lifecycle commands: `taurworks project ...`.
- Namespaced repo workflow commands: `taurworks dev ...` (currently read-only
  diagnostics).
- Shared discovery/configuration core across namespaces.
- XDG-style user config at `$XDG_CONFIG_HOME/taurworks/config.toml`, falling
  back to `~/.config/taurworks/config.toml`.
- Explicit workspace root and global project registry for projects outside
  immediate workspace discovery.
- Compatibility coverage for existing top-level commands (`create`, `refresh`,
  `activate`, `projects`).
- Explicit separation between read-only/path-emitting CLI commands and
  shell-mutating sourced `taurworks-shell.sh` `tw activate`; `tw root PROJECT`
  and `tw working PROJECT` are non-mutating convenience aliases for path
  composition.

## Implemented project and dev slices
- `taurworks help` is equivalent to `taurworks --help`; `taurworks help
  COMMAND` routes to existing command help for current namespaces.
- `taurworks project --help` documents the project namespace and available
  discovery commands.
- `taurworks project where` provides read-only project/config/discovery
  diagnostics.
- `taurworks config where`, `taurworks workspace show`, and `taurworks
  workspace set PATH` provide XDG-style global config diagnostics and
  mutation.
- `taurworks project register/unregister NAME` and `taurworks project
  registry list` provide the global project registry.
- `taurworks project list` / `taurworks projects` merge registered projects,
  workspace children, initialized projects, legacy-admin projects, and
  workspace-only projects into a single status-aware view.
- `taurworks project refresh`, `taurworks project init`, `taurworks project
  create`, working-directory metadata commands, script-friendly `taurworks
  project root PROJECT` / `taurworks project working PROJECT` path emitters,
  and `taurworks project activate --print` provide safe scaffolding,
  composition paths, and inspectable guidance for initialized projects.
- `tw activate`, provided by the sourced `taurworks-shell.sh` helper, resolves
  a project from anywhere (registered, workspace, or local fallback), changes
  into the configured working directory, activates a configured Conda
  environment (`[activation.environment] type = "conda"`), applies configured
  `[activation.exports]`, and prints an optional `[activation].message`.
- `taurworks dev --help`, `taurworks dev where`, and `taurworks dev status`
  provide minimal read-only repository/developer workflow diagnostics without
  running VCS commands or workflow automation.

## What this phase prioritizes
- Designing and implementing `taurworks legacy inspect PROJECT` (read-only
  extraction of `Admin/project-setup.source` patterns) and `taurworks legacy
  migrate PROJECT --apply` (writes declarative config for simple patterns).
- Working through the side-effect audit's follow-up recommendations
  (`project/audits/side_effects.md`), especially gating legacy Conda
  environment creation in `taurworks refresh`/`create` behind an explicit
  command or flag instead of default behavior.
- Deciding how far `taurworks dev ...` should expand beyond read-only
  diagnostics before designing trust boundaries for workflow automation.
- Deferring trusted user-script hooks until legacy inspect/migrate is
  dogfooded.

## What remains future implementation work
- Legacy `Admin/project-setup.source` inspect/migrate commands.
- Trusted per-project startup hooks behind explicit opt-in.
- Gating legacy Conda environment creation behind an explicit
  command/flag (side-effect audit recommendation).
- Expanding `taurworks dev ...` beyond read-only diagnostics into workflow
  automation.
- Multi-repo project management.
- Finalized migration/deprecation mechanics for compatibility commands.
- Expanded diagnostics and dry-run support across all command paths.

Automatic sourcing of legacy `Admin/project-setup.source` scripts is
intentionally deferred because it crosses a stronger trust boundary than
`cd`-only activation.
