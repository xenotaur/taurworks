# Activation Extension Design

## Status

This document is a design note. Taurworks now implements the first three
safe declarative activation slices (optional readiness messages, literal
environment-variable exports, and Conda environment activation), all consumed
by the sourced `tw activate` helper, plus `taurworks legacy inspect`/`migrate`
and the two-tier trust-gated legacy-script sourcing described below
(`WI-TRUSTED-LEGACY-SOURCING-0001`). It still must not be used as permission
to add venv/Docker activation without a separate implementation PR.

## Purpose

Taurworks currently supports activation through an explicitly sourced helper:

```bash
tw activate ProjectName
```

The current implementation resolves a Taurworks project, activates a
configured `[activation.environment] type = "conda"` environment, exports any
validated literal `[activation.exports]`, changes the current shell directory
to the configured working directory, and prints an optional
`activation.message`.
Historical Taurworks-style project setup scripts, especially
`Admin/project-setup.source`, could do more: source shared shell utilities,
activate a Conda environment, change directory, and print a readiness message.

Those extra behaviors are useful, but they cross stronger trust boundaries than
changing directories. This design defines a safe path for future activation
extensions while preserving the current read-only and shell-mutating boundaries.

## Current activation baseline

The validated baseline is explicit activation through a sourced shell helper:

```bash
source /path/to/taurworks-shell.sh
tw project create TestProject --working-dir test_repo --create-working-dir
tw activate TestProject
```

For this baseline:

- `taurworks project activate --print` is the read-only source of redacted
  activation guidance and diagnostics.
- `taurworks project activate --shell` is a read-only machine-payload mode for
  the sourced helper; it emits generated shell assignments only after activation
  export names validate.
- `tw activate`, provided by the sourced `taurworks-shell.sh` helper, is the
  explicit wrapper that may mutate the current shell by exporting configured
  variables and changing directory.
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

Implementation status: implemented: optional `activation.message`, literal
string `[activation.exports]`, and Conda environment activation via
`[activation.environment] type = "conda"`. Legacy inspect/migrate tooling and
arbitrary hooks remain planned design only.

Activation extensions are represented declaratively in `.taurworks/config.toml`
before any imperative hook is considered. Phase 2 is the safe subset of legacy
project setup behavior. The implemented slices cover readiness text, literal
exported environment variables, and Conda activation. venv/Docker-style
environment strategies and arbitrary shell scripts remain outside Phase 2.

A complete Phase 2 configuration may look like this:

```toml
schema_version = 1

[project]
name = "ExampleProject"

[paths]
working_dir = "example-project"

[activation]
message = "Ready for work on ExampleProject"

[activation.exports]
PROJECT_RESOURCE = "~/example/project/resource.txt"
NODE_OPTIONS = "--max-old-space-size=8192"
```

The schema is intentionally data-shaped:

- `[activation].message` is user-facing text printed after successful activation.
- `[activation.environment]` is intentionally deferred. A later implementation
  may describe one known environment strategy such as Conda.
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

Implementation status: implemented. Conda is the only supported environment
strategy:

```toml
[activation.environment]
type = "conda"
name = "EnvName"
```

Implemented behavior:

- `type` is required when `[activation.environment]` is present.
- `name` is required for `type = "conda"` and names the Conda environment to
  activate.
- Unknown environment `type` values produce an actionable unsupported-type
  error instead of falling back to arbitrary scripts.
- Conda activation is a shell-state mutation and happens only behind
  explicitly sourced `tw activate`, not direct read-only `taurworks project
  activate --print` execution.
- `tw activate` reads a distinct machine-readable activation payload
  (`taurworks project activate --shell`) to evaluate. Human-facing `taurworks
  project activate --print` output stays diagnostic and redacted; it is not
  used as the handoff for secret-bearing shell code.
- Taurworks does not run `conda init` automatically and does not edit shell
  startup files. If the user's shell is not prepared for Conda activation,
  Taurworks prints a clear diagnostic telling the user to initialize or
  configure Conda outside Taurworks.
- Failures to locate Conda, initialize the shell hook, or activate the named
  environment stop activation before exports and readiness messages are
  reported as successful.
- Normal output avoids excessive detail; verbose/debug output may report
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

Done: Conda was added after message behavior and export payload separation
were designed and reviewed, keeping the environment type handling narrow and
explicit.

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
- The implemented slice does not expand `~`; export values are shell-quoted and
  exported literally. Any future `~` expansion must be documented and tested in
  the PR that adds it.
- Normal diagnostic output must not echo sensitive values. Diagnostics may
  mention variable names, counts, or redacted placeholders, but should avoid
  printing full values unless the user requests an explicit debug/dry-run mode
  that warns about disclosure.
- Secret-bearing shell code uses a separate machine-readable handoff from
  redacted diagnostics: `taurworks project activate --shell` is consumed by
  `tw activate`, while redacted human diagnostics stay on `--print`.
- `tw activate` must validate that it is reading the machine payload mode before
  evaluating output. It should not evaluate human-formatted `--print` diagnostics.
- Exports preserve the safety boundary: they are data-driven environment
  mutations performed by `tw activate`, not arbitrary code execution.
- Export failures should stop subsequent activation steps and should not print
  the success message.

Recommendation: implement exports after message-only polish and before Conda
activation, because export rendering, machine-payload separation, and redaction
rules are useful independently of any environment manager.

## User scripts and hooks (implemented: trust-gated legacy sourcing)

Implementation status: implemented (`WI-TRUSTED-LEGACY-SOURCING-0001`). This
section originally sketched a future generic `[activation.hooks]` schema
(arbitrary `source`/`run` lists per project). Dogfooding
(`WI-LEGACY-BATCH-MIGRATION-0001`) found the actual remaining need was
narrower and more concrete: every real legacy project sources
`~/bin/utilities.source` for behavior declarative config cannot model. Rather
than a general hook schema, Taurworks implements trust-gated sourcing of the
one concrete artifact that already exists: legacy `Admin/project-setup.source`
itself, as the first (and currently only) supported "hook." A generic
multi-source/multi-command hook schema remains unimplemented and is not
proposed by this update.

The implemented model is two-tier, direnv-allow-style consent:

**Tier 1 — global enable switch**, off by default, in the user-owned global
config:

```toml
[activation]
legacy_sourcing = false
```

Commands: `taurworks config legacy-sourcing show|enable|disable`. While off,
`tw activate` never sources a legacy script and never prompts, regardless of
any per-project trust record — behavior is byte-identical to before this
feature existed.

**Tier 2 — per-project trust records**, also in the user-owned global config,
in a dedicated table separate from the project registry:

```toml
[trust.PROJECT_NAME]
path = "/absolute/path/to/Admin/project-setup.source"
digest = "sha256 hex digest of the script's current content"
```

Commands: `taurworks project trust set|unset|list NAME`. `trust set` always
overwrites any existing record for the project — it is an explicit "I have
reviewed and approve this exact content" action, not a merge.

Trust records are never stored inside any project directory (not even
`.taurworks/`): storing them in `[projects.NAME]` was considered and rejected,
because the registry requires every `[projects.NAME]` entry to have a
non-empty `root` and iterates all such entries
(`project_registry._project_entry_root`), so a trust-only entry there would
break existing registry handling — hence the separate `[trust.NAME]` table.
Keeping trust exclusively in user-owned global config (never project-local)
is also the load-bearing safety property: a project's own files — including
a cloned or synced repository landing at a project root — can never grant
themselves trust. Only a command the user runs can.

### `tw activate` flow

When `legacy_setup_exists` is true (checked after the existing config-driven
activation steps, so trust-gated sourcing composes with declarative
activation rather than replacing it — this also means it still applies to a
project already migrated to `config.toml` that has a leftover legacy script):

- **Tier 1 off:** nothing happens; no output related to this feature.
- **Tier 1 on, trusted (recorded digest matches the script's current sha256):**
  source silently.
- **Tier 1 on, `--legacy` flag passed:** source once, regardless of trust
  state. Requires Tier 1 to already be on.
- **Tier 1 on, untrusted, interactive TTY:** print a `taurworks legacy
  inspect`-style summary, then prompt: `[s]ource once`, `[t]rust and
  source`, `[n]ever ask again`, or `[k]ip`. Trusting calls `taurworks
  project trust set` before sourcing.
- **Tier 1 on, untrusted, non-interactive (no TTY), no `--legacy`:** fail open
  to the existing cd-only behavior with a one-line note pointing at
  `--legacy` and `trust set`. Never hangs waiting for input.
- **Tier 1 on, previously trusted but the script's content has changed
  (digest mismatch):** treated as untrusted for sourcing purposes, with the
  interactive prompt wording calling out that the script changed since it
  was trusted. Editing a trusted script causes exactly one re-prompt on the
  next activation; trusting again re-records the new digest.
- **`--no-legacy` flag:** never source for this invocation, even if trusted.

The prompt-parsing logic (`_tw_legacy_prompt_choice`) is a small, separately
testable function so it can be exercised with piped stdin in tests without
needing a real TTY; the outer `[ -t 0 ] && [ -t 1 ]` gate in `_tw_activate` is
what actually decides whether to prompt versus fail open.

The safety boundary is now:

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating wrapper for cd, declarations, and supported env
  setup, plus trust-gated legacy-script sourcing when Tier 1 is enabled

workspace-only fallback
  cd only, with warning

legacy Admin/project-setup.source, Tier 1 off (default)
  recognized, but not sourced

legacy Admin/project-setup.source, Tier 1 on, untrusted
  cd-only fallback, or one-time consent prompt on a real TTY, or --legacy
  for an explicit one-shot source

legacy Admin/project-setup.source, Tier 1 on, trusted
  sourced silently on each activation until content changes or trust is
  revoked with `taurworks project trust unset`
```

A generic hook schema (arbitrary `run = [...]` commands, non-legacy-script
sources) remains unimplemented; this design does not propose adding one.

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

All six items are now done:

1. **Activation message (done):** parse `[activation].message`, print it only
   after successful activation, and keep the current concise output when the
   field is absent.
2. **Exports and payload separation (done):** implemented for literal string
   values without `~` expansion. Taurworks parses `[activation.exports]`,
   validates export names, renders shell-quoted exports only through `--shell`
   for `tw activate`, redacts values in normal diagnostics, and keeps
   `taurworks project activate --print` read-only and human-safe.
3. **Conda activation in `tw activate` (done):** supports `[activation.environment]
   type = "conda"` plus `name`, emits/evaluates the required shell setup only in
   the sourceable wrapper path, reports missing Conda or shell setup clearly, and
   never runs `conda init`.
4. **Legacy inspect (done, `WI-ACTIVATION-CONFIG-0001`):** `taurworks legacy
   inspect PROJECT` conservatively extracts common legacy patterns and
   reports manual-review items without executing scripts.
5. **Legacy migrate for simple scripts (done, `WI-ACTIVATION-CONFIG-0001` +
   the `WI-LEGACY-BATCH-MIGRATION-0001` one-time real-corpus migration):**
   `taurworks legacy migrate PROJECT --apply` writes declarative config for
   simple detected patterns while preserving existing values and requiring
   review for unsupported behavior.
6. **Trusted legacy-script sourcing (done, `WI-TRUSTED-LEGACY-SOURCING-0001`):**
   two-tier consent (global switch + per-project sha256 trust records in
   user-owned global config only), with opt-in, warnings, revocation
   (`trust unset`), content-change detection, and `legacy inspect` used as
   the pre-consent summary — see "User scripts and hooks" above.

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

1. **Activation message (done):** support a future `[activation].message` while keeping
   current concise output as the default when the message is absent.
2. **Exports (done):** support `[activation.exports]` only after the implementation has
   a separate machine-readable payload channel for `tw activate` and redacted
   human diagnostics.
3. **Conda activation (done):** add narrow, documented support for
   `[activation.environment] type = "conda"` and `name`; defer venv, Docker,
   and other systems to separate designs.
4. **Legacy inspect and simple migration (done):** help users review and migrate
   `Admin/project-setup.source` projects to declarative config without executing
   those scripts.
5. **Explicit trusted legacy-script sourcing (done):** sourceable only after
   explicit per-project trust (content-digest verified) behind a global
   opt-in switch; see "User scripts and hooks" above.

The default remains that legacy `Admin/project-setup.source` is never sourced
automatically based on filename alone. What is implemented is consented
sourcing: a project only gets sourced after the user has explicitly enabled
the feature and explicitly trusted that project's script content, both
recorded outside the project itself. Silent, filename-triggered sourcing —
the thing this design always ruled out — remains ruled out.

## Non-goals for this design PR

This design does not implement:

- Conda activation;
- export rendering;
- activation message behavior;
- startup hooks;
- automatic legacy setup sourcing;
- shell wrapper behavior changes;
- `dev` command workflow automation.
