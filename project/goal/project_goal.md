# Project Goal

## Product goal
Taurworks is a unified developer and workspace orchestration CLI centered on one primary executable: `taurworks`.

It provides two coordinated layers:

1. **Workspace/project management** via `taurworks project ...`
2. **Repo-local developer workflow orchestration** via `taurworks dev ...`

## Intended value
Taurworks should make common project operations explicit, discoverable, and consistent across repositories while preserving project-specific flexibility.

The tool is not intended to replace established ecosystem tools (build systems, test runners, formatters, package managers, linters, release tooling, or environment managers). Instead, Taurworks should wrap and orchestrate these tools through stable command surfaces and predictable configuration/discovery behavior.

## Compatibility direction
Existing top-level commands such as `create`, `refresh`, `activate`, and `projects` remain compatibility commands until a deliberate migration/deprecation path is documented and implemented.

## Near-term goal

After successful `tw activate` dogfooding, Taurworks should preserve the safe split between read-only `taurworks project activate --print` guidance and explicit shell-mutating `tw activate`, while polishing shell UX, classifying project-list status, and designing activation extensions before executing project-controlled startup scripts. Automatic legacy `Admin/project-setup.source` sourcing is intentionally deferred because it crosses a stronger trust boundary than `cd`-only activation.
