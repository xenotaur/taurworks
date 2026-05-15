# Activation Extension Design

## Status

This document is a future design note. It does not describe implemented
activation behavior beyond the current `cd`-only sourced shell helper. It also
must not be used as permission to add environment activation, startup hooks, or
legacy setup sourcing without a separate implementation PR.

## Purpose

Taurworks currently supports activation through an explicitly sourced helper:

```bash
tw activate ProjectName
```

The current implementation resolves a Taurworks project and changes the current
shell directory to the configured working directory. Historical Taurworks-style
project setup scripts, especially `Admin/project-setup.source`, could do more:
source shared shell utilities, activate a Conda environment, change directory,
and print a readiness message.

Those extra behaviors are useful, but they cross stronger trust boundaries than
changing directories. This design defines a safe path for future activation
extensions while preserving the current read-only and shell-mutating boundaries.

## Current activation baseline

The validated baseline is `cd`-only activation through an explicitly sourced
shell helper:

```bash
source /path/to/taurworks-shell.sh
tw project create TestProject --working-dir test_repo --create-working-dir
tw activate TestProject
```

For this baseline:

- `taurworks project activate --print` is the read-only source of activation
  guidance and diagnostics.
- `tw activate`, provided by the sourced `taurworks-shell.sh` helper, is the
  explicit wrapper that may mutate the current shell by changing directory.
- Legacy `Admin/project-setup.source` files may be classified for visibility,
  but they are not sourced automatically and are not fallback activation targets.

## Safety boundary to preserve

Future work should preserve this separation:

```text
taurworks project activate --print
  read-only diagnostic/guidance command

tw activate
  explicit sourceable shell wrapper that may mutate shell state

startup hooks
  future trusted-code execution requiring explicit design and opt-in
```

The boundary matters because shell state changes are not all equivalent:

- printing activation guidance is read-only;
- changing directory mutates only the current shell location;
- activating environments may mutate `PATH`, shell functions, prompt state, and
  process environment variables;
- sourcing startup hooks executes project-controlled code in the user's current
  shell and can perform arbitrary shell actions.

## Phase 2 declarative activation configuration

Implementation status: planned design only. No declarative activation behavior is implemented by this document.

Activation extensions should be represented declaratively in `.taurworks/config.toml` before any imperative hook is considered. A future configuration may look like this:

```toml
[activation]
message = "Ready for work on project LCATS"

[activation.environment]
type = "conda"
name = "LCATS"

[activation.exports]
CREDENTIALS = "~/Workspace/Novarc/Celeste/NovarcCelesteBuilder.pem"
NODE_OPTIONS = "--max-old-space-size=8192"
```

or:

```toml
[activation]
message = "Ready for work on project Taurworks"

[activation.environment]
type = "venv"
path = ".venv"
```

Phase 2 should design and implement declarative activation in small slices:

1. activation success message;
2. declarative environment strategy such as Conda or venv;
3. declarative exported environment variables;
4. clear verbose/debug diagnostics and failure modes.

The `[activation.exports]` table is data, not shell code. Values should be treated as literal export values with documented path-expansion rules rather than evaluated command substitutions. This phase should avoid arbitrary user-script sourcing.

## Readiness message

A low-risk first extension is a configurable readiness message:

```toml
[activation]
message = "Ready for work on project Taurworks"
```

Design expectations:

- The message is printed only after the activation action succeeds.
- The default may preserve the current concise `tw activate` destination message
  so existing shell workflows remain predictable.
- The configured message should be treated as text, not shell code.
- The message should not hide failures from project resolution, working-directory
  validation, or future environment activation.
- Diagnostics should stay available through verbose/debug activation paths rather
  than making default activation noisy.

Recommendation: implement message-only polish before environment activation or
startup hooks because it improves ergonomics without executing additional code.

## Declarative environment activation

Environment activation should support multiple environment systems. Taurworks
should not assume every project uses Conda.

### Conda

A future Conda configuration may look like this:

```toml
[activation.environment]
type = "conda"
name = "Taurworks"
```

Design considerations:

- Activation should be explicit through `tw activate`, not through the read-only
  `taurworks project activate --print` command.
- Diagnostics should explain the selected environment type and name before or
  during activation when verbose/debug output is requested.
- Failures to locate Conda or the named environment should be reported clearly
  and should not be mistaken for a successful activation.
- Implementation should avoid hard-coding Conda as the only environment model.

### Python virtual environments

A future venv configuration may look like this:

```toml
[activation.environment]
type = "venv"
path = ".venv"
```

Design considerations:

- Relative paths should resolve from the Taurworks project root or configured
  working directory according to a documented rule before implementation.
- Missing activation scripts should produce actionable errors.
- The selected shell family may matter because venv activation scripts differ by
  shell.

### Docker, devcontainers, and project-specific workflows

Some projects should not activate a local shell environment at all. Future
extensions may need to represent Docker, devcontainer, Nix, Pixi, or other
project-specific workflows. Those systems may require separate commands rather
than direct shell mutation.

Design considerations:

- Container-oriented workflows may be better modeled as guidance or `dev`
  commands instead of shell activation side effects.
- Project-specific workflows should remain inspectable and should not become a
  hidden arbitrary-script execution path.
- If a workflow cannot be represented declaratively, Taurworks should require an
  explicit trusted hook rather than silently guessing behavior.

Recommendation: add declarative environment activation after message-only polish,
starting with a narrow type registry and documented failure modes.

## Future safe user-script support

Implementation status: future design only. User scripts and hooks must not be sourced by default.

Taurworks should eventually support user scripts or hooks only behind explicit opt-in, such as a per-project config flag or a `tw config` trust command. This future phase is intentionally separate from Phase 2 declarative activation.

Required safety properties:

1. Hooks are trusted code, not configuration data.
2. `tw activate` should warn clearly before first use of a trusted hook and when trust changes.
3. Inspection and dry-run modes should show what would run without running it.
4. Opt-in should be per project, not inherited globally by accident.
5. Legacy `Admin/project-setup.source` files are recognized for migration visibility but are not sourced by default.
6. A later migration path may help users convert `Admin/project-setup.source` into declarative activation config plus an explicitly trusted hook when necessary.

The safety boundary remains:

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating wrapper

workspace-only / legacy-admin fallback
  cd only, with warning

legacy Admin/project-setup.source
  recognized, but not sourced by default

user scripts/hooks
  future explicit opt-in only
```

## Trusted startup hooks

A startup hook would intentionally execute project-controlled code in the user's
current shell. A future configuration may look like this:

```toml
[activation]
startup_script = ".taurworks/activate.source"
```

Safety requirements before any implementation:

1. Hooks must be explicit opt-in configuration, not discovered and sourced by
   filename convention alone.
2. `tw activate` should display user-visible warnings before first use or when
   trust state changes.
3. Taurworks must not automatically source arbitrary scripts found in a project
   tree.
4. A trust or confirmation model should be designed, such as recording that the
   user approved a specific script path and content digest.
5. Documentation must state plainly that startup hooks execute code in the user
   shell and may change environment variables, aliases, functions, shell options,
   prompt state, files, or other shell-visible state.

Additional design questions:

- How does a user revoke trust for one project or all projects?
- Should hooks run before or after declarative environment activation?
- How should Taurworks detect that a hook changed after being trusted?
- What should happen in non-interactive shells?
- How should dry-run or print-only diagnostics present hook guidance without
  executing the hook?

Recommendation: defer trusted startup hooks until declarative activation is
stable and the trust model is documented in detail.

## Legacy `Admin/project-setup.source` migration

The legacy pattern is:

```text
<project>/Admin/project-setup.source
```

Taurworks should prefer migration or one-off tooling over automatic fallback
sourcing. A migration tool could inspect a legacy script, generate a proposed
`.taurworks/config.toml`, and point the user to any remaining manual steps.
Examples of extractable intent may include project name, working directory,
readiness text, or a Conda environment name.

Automatic fallback sourcing is not recommended as default behavior because:

- filename-based discovery would execute project-controlled code without a clear
  Taurworks opt-in;
- users may reasonably expect `tw activate` to remain `cd`-only until they
  configure stronger behavior;
- legacy scripts may rely on assumptions that are not valid for all shells or
  all machines;
- invisible fallback would blur the boundary between read-only diagnostics,
  `cd`-only activation, environment activation, and arbitrary shell code;
- a bad or stale legacy script could mutate the user's current shell before the
  user understands why.

If a legacy bridge is ever added, it should require explicit opt-in and clear
warnings, such as a configuration flag that names the legacy script and marks it
as trusted. Even then, migration to declarative configuration plus a small
project-owned hook should be preferred.

Recommendation: classify legacy-admin projects for visibility now, add explicit
migration tooling later, and avoid automatic legacy fallback sourcing.

## Options considered

### Option A: Message-only polish

Add only configurable activation success text.

Pros:

- low trust risk;
- improves parity with legacy readiness messages;
- easy to review and test;
- does not execute code or activate environments.

Cons:

- does not restore environment setup behavior.

Recommendation: do first.

### Option B: Declarative environment activation

Add a constrained environment model such as Conda and venv entries under
`[activation.environment]`.

Pros:

- supports common setup needs without arbitrary hooks;
- keeps behavior inspectable;
- can produce useful diagnostics and validation.

Cons:

- still mutates shell environment;
- requires careful shell integration and failure handling;
- must avoid assuming Conda for all projects.

Recommendation: do second, after message-only polish.

### Option C: Explicit trusted startup hook

Add a sourceable project hook only when configured and trusted.

Pros:

- covers project-specific setup that cannot be modeled declaratively;
- gives legacy users an escape hatch.

Cons:

- executes arbitrary code in the user's shell;
- requires trust, confirmation, revocation, and change-detection design;
- can obscure activation behavior if warnings and diagnostics are weak.

Recommendation: do third, only with explicit trust semantics.

### Option D: Legacy migration tooling

Add a command or documented workflow that helps convert
`Admin/project-setup.source` projects into Taurworks metadata.

Pros:

- helps existing projects move forward;
- avoids silent execution of legacy scripts;
- can produce reviewable configuration changes.

Cons:

- cannot reliably infer every custom shell behavior;
- may still require manual review and project-specific hooks.

Recommendation: do fourth, with clear limits and no automatic fallback sourcing.

## Recommended phased approach

1. **Message-only polish:** support a future `[activation].message` while keeping
   current concise output as the default.
2. **Declarative environment activation:** add a narrow, documented environment
   model for types such as Conda and venv without assuming all projects use one
   environment system.
3. **Explicit trusted startup hook:** add sourceable hooks only after trust,
   warning, confirmation, revocation, and changed-content behavior is designed.
4. **Legacy migration tooling:** help users migrate
   `Admin/project-setup.source` projects to `.taurworks/config.toml` and, where
   necessary, explicit trusted hooks.

The default should not become automatic legacy `Admin/project-setup.source`
fallback sourcing. That behavior would execute project-controlled code based on a
filename convention and would weaken the trust boundary that Taurworks has kept
explicit so far.

## Non-goals for this design PR

This design does not implement:

- environment activation;
- startup hooks;
- automatic legacy setup sourcing;
- shell wrapper behavior changes;
- `dev` command workflow automation.
