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

Implementation status: planned design only. No declarative activation behavior is
implemented by this document.

Activation extensions should be represented declaratively in
`.taurworks/config.toml` before any imperative hook is considered. Phase 2 is the
safe subset of legacy project setup behavior: readiness text, one supported
environment activation strategy, and literal exported environment variables.
Arbitrary shell scripts remain outside Phase 2.

A complete Phase 2 configuration may look like this:

```toml
schema_version = 1

[project]
name = "ExampleProject"

[paths]
working_dir = "example-project"

[activation]
message = "Ready for work on ExampleProject"

[activation.environment]
type = "conda"
name = "ExampleProject"

[activation.exports]
PROJECT_RESOURCE = "~/example/project/resource.txt"
NODE_OPTIONS = "--max-old-space-size=8192"
```

The schema is intentionally data-shaped:

- `[activation].message` is user-facing text printed after successful activation.
- `[activation.environment]` describes one known environment strategy. The first
  implementation should support only `type = "conda"` with `name = "..."`.
- `[activation.exports]` is a TOML table of literal environment-variable values,
  not shell code.
- Omitted activation fields mean "do nothing extra" beyond the current resolved
  directory change and existing concise activation output.

Phase 2 implementation must not:

1. source arbitrary scripts by default;
2. run arbitrary user commands by default;
3. edit shell startup files such as `.bashrc`, `.zshrc`, or shell profile files;
4. run `conda init` automatically;
5. leak secrets in normal diagnostic output;
6. make `taurworks project activate --print` mutate shell state;
7. use one stdout stream for both human diagnostics and secret-bearing shell
   activation payloads.

## Activation message

A low-risk first extension is a configurable readiness message:

```toml
[activation]
message = "Ready for work on project X"
```

Design expectations:

- The message is optional.
- If the field is missing, `tw activate` should preserve the current concise
  success behavior rather than inventing a noisy default. A reasonable default is
  the existing destination-oriented message from the sourceable helper.
- The configured message is printed only after all activation steps that are
  enabled for the project succeed, including future environment activation and
  exports.
- The configured message is treated as plain text, not shell code. It must not
  be interpolated, evaluated, or allowed to hide failures.
- The message belongs to the shell-mutating `tw activate` workflow. The read-only
  `taurworks project activate --print` command may print guidance that includes
  the message as data, but it must not use the message as evidence that
  activation already happened.
- Verbose/debug diagnostics should remain available through explicit flags or
  direct `taurworks project activate ... --print` inspection instead of making
  normal activation output noisy.

Recommendation: implement message-only polish first because it improves parity
with legacy readiness messages without executing additional code.

## Environment activation

Phase 2 should design only the Conda path for the first implementation:

```toml
[activation.environment]
type = "conda"
name = "EnvName"
```

Design expectations for the initial implementation:

- `type` is required when `[activation.environment]` is present.
- `name` is required for `type = "conda"` and names the Conda environment to
  activate.
- Unknown environment `type` values should produce an actionable unsupported-type
  error instead of falling back to arbitrary scripts.
- Conda activation is a shell-state mutation and therefore belongs behind
  explicitly sourced `tw activate`, not direct read-only `taurworks project
  activate --print` execution.
- A future implementation should add a distinct machine-readable activation
  payload mode for `tw activate` to evaluate. Human-facing `taurworks project
  activate --print` output should remain diagnostic and redacted; it must not be
  the only handoff for secret-bearing shell code.
- Taurworks should not run `conda init` automatically and should not edit shell
  startup files. If the user's shell is not prepared for Conda activation,
  Taurworks should print a clear diagnostic telling the user to initialize or
  configure Conda outside Taurworks.
- Failures to locate Conda, initialize the shell hook, or activate the named
  environment should stop activation before exports and readiness messages are
  reported as successful.
- Normal output should avoid excessive detail; verbose/debug output may report
  the selected environment type and name.

Other environment systems are explicitly deferred:

- Python virtual environments may later use a shape such as
  `[activation.environment] type = "venv"` plus a documented relative `path`, but
  venv is not part of the first Phase 2 implementation.
- Docker, devcontainers, Nix, Pixi, and similar systems may be better modeled as
  guidance or `taurworks dev ...` workflows rather than direct activation side
  effects. They require separate design before implementation.
- If a setup cannot be represented declaratively, Taurworks should require a
  future trusted hook instead of guessing or sourcing scripts implicitly.

Recommendation: add Conda only after message behavior and export payload
separation are designed and reviewed, keeping the environment type handling
narrow and explicit.

## Exports

Phase 2 should represent exported variables as literal TOML data:

```toml
[activation.exports]
KEY = "value"
```

Design expectations:

- Keys must be valid shell environment variable names: start with `A-Z`, `a-z`,
  or `_`, followed by only `A-Z`, `a-z`, `0-9`, or `_`. Invalid names should be
  rejected before any shell output is produced for that activation.
- Values are TOML strings and should be treated as literal values. Taurworks must
  not evaluate command substitutions, parameter expansions, arithmetic
  expansions, globs, or shell pipelines in export values.
- The shell output used by `tw activate` must quote values safely for the target
  shell before evaluation. The initial implementation should document the shell
  family it supports and should prefer single-purpose quoting helpers over
  hand-built string concatenation.
- `~` expansion is allowed only when documented. The proposed rule is to expand
  a leading `~` or `~/` in export values to the current user's home directory
  before shell quoting, while leaving embedded tildes untouched.
- Normal diagnostic output must not echo sensitive values. Diagnostics may
  mention variable names, counts, or redacted placeholders, but should avoid
  printing full values unless the user requests an explicit debug/dry-run mode
  that warns about disclosure.
- Secret-bearing shell code must use a separate machine-readable handoff from
  redacted diagnostics. The proposed implementation shape is a future flag such
  as `taurworks project activate --emit-shell` or an equivalent payload channel
  whose stdout is consumed only by `tw activate`; redacted human diagnostics
  should stay on `--print` output or stderr.
- `tw activate` must validate that it is reading the machine payload mode before
  evaluating output. It should not evaluate human-formatted `--print` diagnostics.
- Exports preserve the safety boundary: they are data-driven environment
  mutations performed by `tw activate`, not arbitrary code execution.
- Export failures should stop subsequent activation steps and should not print
  the success message.

Recommendation: implement exports after message-only polish and before Conda
activation, because export rendering, machine-payload separation, and redaction
rules are useful independently of any environment manager.

## User scripts and hooks

Implementation status: future design only. User scripts and hooks must not be
sourced or run by default.

Some legacy projects need behavior that declarative messages, Conda activation,
and exports cannot safely model. Taurworks may support this later only as trusted
code behind explicit opt-in. A possible future shape is:

```toml
[activation.hooks]
enabled = false
source = [".taurworks/activate.source"]
run = []
```

The exact hook schema is not approved by this Phase 2 design. Any future hook
schema must satisfy these requirements before implementation:

1. `enabled` or an equivalent trust flag defaults to `false`.
2. Hooks are never discovered and sourced merely because a filename exists.
3. The user must opt in explicitly through project configuration or a future
   command such as `tw config trust PROJECT .taurworks/activate.source`.
4. Trust should be per project and should record enough detail to detect path or
   content changes, such as an approved script path and content digest.
5. Inspection and dry-run modes must show what would be sourced or run without
   executing it.
6. `tw activate` should warn clearly before first hook use and when trusted hook
   content changes.
7. Documentation must state that hooks are arbitrary code that may alter shell
   state, files, credentials, prompts, aliases, functions, and commands.

The safety boundary remains:

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating wrapper for cd, declarations, and supported env setup

workspace-only / legacy-admin fallback
  cd only, with warning

legacy Admin/project-setup.source
  recognized, but not sourced by default

user scripts/hooks
  future explicit opt-in trusted code only
```

Recommendation: defer hooks until after Phase 2 dogfooding confirms which legacy
behaviors remain impossible to express declaratively.

## Legacy `Admin/project-setup.source` migration

The legacy pattern is:

```text
<project>/Admin/project-setup.source
```

Taurworks should prefer migration tooling over automatic fallback sourcing. A
later migration package should provide:

```bash
taurworks legacy inspect PROJECT
taurworks legacy migrate PROJECT --apply
```

`taurworks legacy inspect PROJECT` should be conservative and read-only:

- locate the legacy script through the normal project resolver;
- report detected common patterns such as `conda activate NAME`, simple
  `export KEY=value` assignments, `cd PATH`, and readiness `echo`/`printf`
  messages;
- propose corresponding `.taurworks/config.toml` fields when extraction is
  unambiguous;
- report unsupported statements, dynamic shell constructs, sourced files,
  function calls, command substitutions, aliases, and shell conditionals as
  requiring manual review;
- redact likely sensitive export values by default while still showing variable
  names and whether a value was detected;
- avoid executing or sourcing the script.

`taurworks legacy migrate PROJECT --apply` should write changes only after the
user chooses to apply them:

- prefer declarative config fields over copying arbitrary scripts;
- preserve existing `.taurworks/config.toml` values unless the user explicitly
  chooses to replace them;
- write a reviewable diff or summary before applying changes;
- leave unsupported shell behavior as manual follow-up notes;
- require explicit opt-in before copying a legacy script into a future trusted
  hook location or enabling hook execution.

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

Recommendation: classify legacy-admin projects for visibility now, add inspect
and migrate commands later, and avoid automatic legacy fallback sourcing.

## Follow-up implementation package

Phase 2 should be implemented through small PRs after Phase 1 dogfooding:

1. **Activation message:** parse `[activation].message`, print it only after
   successful activation, and keep the current concise output when the field is
   absent.
2. **Exports and payload separation:** parse `[activation.exports]`, validate
   export names, perform documented leading `~` expansion, render shell-quoted
   exports only through a machine-readable payload channel for `tw activate`,
   redact values in normal diagnostics, and keep `taurworks project activate
   --print` read-only and human-safe.
3. **Conda activation in `tw activate`:** support `[activation.environment]
   type = "conda"` plus `name`, emit/evaluate the required shell setup only in
   the sourceable wrapper path, report missing Conda or shell setup clearly, and
   never run `conda init`.
4. **Legacy inspect:** add `taurworks legacy inspect PROJECT` to conservatively
   extract common legacy patterns and report manual-review items without
   executing scripts.
5. **Legacy migrate for simple scripts:** add `taurworks legacy migrate PROJECT
   --apply` to write declarative config for simple detected patterns while
   preserving existing values and requiring review for unsupported behavior.
6. **Trusted hooks after dogfood:** design and implement explicit hook trust only
   after declarative activation has been dogfooded; include opt-in, warnings,
   revocation, content-change detection, and dry-run/inspection support.

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

### Option B: Declarative export data

Add literal `[activation.exports]` data with validation, safe quoting, documented
leading `~` expansion, redacted diagnostics, and a separate machine-readable
payload channel for `tw activate`.

Pros:

- restores common safe legacy behavior without arbitrary hooks;
- keeps environment-variable changes inspectable;
- can produce useful diagnostics and validation without printing secrets.

Cons:

- still mutates the shell environment through exports;
- requires careful shell quoting and failure handling;
- must avoid leaking sensitive values in normal diagnostic output.

Recommendation: do after message-only polish and before Conda activation.

### Option C: Conda environment activation

Add narrow initial support for `[activation.environment] type = "conda"` plus
`name`.

Pros:

- supports the most common legacy setup step without sourcing project scripts;
- keeps the environment manager and environment name explicit.

Cons:

- mutates `PATH`, prompt state, and other shell-visible environment details;
- depends on user-managed Conda shell setup;
- must not run `conda init` or edit startup files.

Recommendation: do after export rendering and payload separation are safe.

### Option D: Explicit trusted startup hook

Add a sourceable project hook only when configured and trusted.

Pros:

- covers project-specific setup that cannot be modeled declaratively;
- gives legacy users an escape hatch.

Cons:

- executes arbitrary code in the user's shell;
- requires trust, confirmation, revocation, and change-detection design;
- can obscure activation behavior if warnings and diagnostics are weak.

Recommendation: do after declarative dogfooding, only with explicit trust
semantics.

### Option E: Legacy migration tooling

Add a command or documented workflow that helps convert
`Admin/project-setup.source` projects into Taurworks metadata.

Pros:

- helps existing projects move forward;
- avoids silent execution of legacy scripts;
- can produce reviewable configuration changes.

Cons:

- cannot reliably infer every custom shell behavior;
- may still require manual review and project-specific hooks.

Recommendation: do after inspect/migration requirements are reviewed, with clear
limits and no automatic fallback sourcing.

## Recommended phased approach

1. **Activation message:** support a future `[activation].message` while keeping
   current concise output as the default when the message is absent.
2. **Exports:** support `[activation.exports]` only after the implementation has
   a separate machine-readable payload channel for `tw activate` and redacted
   human diagnostics.
3. **Conda activation:** add narrow, documented support for
   `[activation.environment] type = "conda"` and `name`; defer venv, Docker,
   and other systems to separate designs.
4. **Legacy inspect and simple migration:** help users review and migrate
   `Admin/project-setup.source` projects to declarative config without executing
   those scripts.
5. **Explicit trusted startup hook:** add sourceable hooks only after trust,
   warning, confirmation, revocation, and changed-content behavior is designed.

The default should not become automatic legacy `Admin/project-setup.source`
fallback sourcing. That behavior would execute project-controlled code based on a
filename convention and would weaken the trust boundary that Taurworks has kept
explicit so far.

## Non-goals for this design PR

This design does not implement:

- Conda activation;
- export rendering;
- activation message behavior;
- startup hooks;
- automatic legacy setup sourcing;
- shell wrapper behavior changes;
- `dev` command workflow automation.
