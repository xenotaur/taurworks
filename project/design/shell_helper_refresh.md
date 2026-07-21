# Shell Helper Refresh Design

## Status

This document is a design note. Nothing described here is implemented yet.
It proposes a mechanism for the "stale shell helper" problem: the packaged
`tw` shell integration is a static, sourced snapshot that never notices when
the installed `taurworks` package moves on without it.

## Purpose

`taurworks shell print` emits a sourceable shell helper. The documented setup
is:

```bash
mkdir -p ~/.config/taurworks
taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
source ~/.config/taurworks/taurworks-shell.sh
```

`source` reads the file into the current shell exactly once, the same way
`.bashrc` is read at login. Two independent staleness problems follow from
that:

1. **On-disk drift.** The file at `~/.config/taurworks/taurworks-shell.sh` is
   a snapshot taken at print-time. If the `taurworks` package is upgraded
   afterward (`pipx upgrade`, a new editable-install commit, etc.), the file
   on disk does not change until someone reruns `shell print` and
   overwrites it.
2. **In-shell drift.** Even after the file on disk is refreshed, every shell
   that already `source`d the old version keeps running the shell functions
   it loaded at `source` time. A subprocess — including `taurworks` itself —
   cannot rewrite the function table of its parent shell, so regenerating
   the file does nothing for shells that are already open.

Both failures are currently silent: there is no error, no warning, nothing
that distinguishes a stale `tw` from a current one. This bit real usage
during 2026-07-11 through 2026-07-18 dogfooding — guidance-string and
trust-gated-sourcing behavior from two merged PRs were silently absent from
an already-sourced `tw` for most of a session.

## Current baseline

- `taurworks shell print` is a read-only Python subcommand
  (`src/taurworks/cli.py:272`, `src/taurworks/shell_resources.py`) that reads
  a packaged resource file and writes it to stdout. It has no notion of "the
  currently installed file" — it only ever emits the current package's copy.
- The printed file (`src/taurworks/resources/shell/taurworks-shell.sh`)
  defines `tw()`, `_tw_activate()`, and the trust-gated legacy-sourcing
  helpers. None of that code is version-stamped today; there is no marker
  that lets a sourced instance of `_tw_activate` learn that a newer instance
  exists.
- This repo does have a package version (`setup.py:5`, `version="0.1"`), but
  it is a static string that has never been bumped and is not read anywhere
  at runtime — nothing in `src/taurworks/` calls
  `importlib.metadata.version("taurworks")` or otherwise surfaces it, and
  `src/taurworks/__init__.py` is empty. So it cannot serve as a meaningful
  staleness signal today without first introducing real bump discipline
  (a separate decision from this one, see Option E below).
- `tw refresh` is **not available as a new name** — `taurworks refresh
  PROJECT_NAME` already exists as a top-level legacy compat command (Conda
  env refresh for a named project, `src/taurworks/cli.py:351`), and the `tw`
  dispatcher's fallthrough (`command taurworks "$@"`) already routes bare
  `tw refresh ...` to it. Any new shell-refresh verb needs a name that does
  not collide with that.
- `README.md` already carries a "Stale shell-helper mitigation" note
  (currently around `README.md:139-152`, added by `WI-TL-BREAKGLASS-0001`)
  that describes this exact problem and its manual workaround, and names the
  future fix as "a `tw install`/`tw refresh` command... being designed
  separately." That placeholder name is superseded by this design's
  `tw shell refresh` (see the naming-collision point above); the
  implementing work item must update that note to name the actual command
  rather than leaving the placeholder in place.

## Safety boundary to preserve

This inherits the same boundary documented in
[`activation_extension.md`](activation_extension.md) and restated in
`README.md:31-36`: a plain `taurworks` subcommand is a child process and
cannot mutate its parent shell. Concretely:

```text
taurworks shell print
  read-only: emits the current packaged helper text to stdout, nothing else

tw shell refresh   (proposed)
  explicit sourceable shell function: may overwrite the on-disk helper file
  and re-source it into the current shell

already-open shells that have not run tw shell refresh
  keep running whatever they last sourced, unchanged, by construction
```

Regenerating the file on disk is Python's job and is safe and easy. Getting
that regenerated content back into a *running* shell can only be done by
shell-function code that is already loaded in that shell — never by the
`taurworks` executable itself, and never for a different shell process
entirely. No design in this document can make an already-open shell in
*another terminal tab* refresh itself; only the shell where `tw shell
refresh` is actually invoked can be updated. Nothing short of the user
re-sourcing (or restarting) that other tab reaches it, and that limit is not
solvable from inside this shell's own subprocess model — it is not a gap in
this design, it is the same constraint the rest of the repo already accepts
for `tw activate`.

## The bootstrapping wrinkle

A shell that has already sourced a `taurworks-shell.sh` predating this
feature has no version marker and no comparison logic loaded into it at
all — the code to notice staleness doesn't exist in that shell's memory
yet. There is no channel available to inject new function bodies into an
already-running shell from outside; that is the identical constraint that
motivates the feature in the first place. **At least one manual re-source is
unavoidable** for any shell already open when this ships, and that is
acceptable — it's the same one-time-per-shell property tools like `direnv`,
`nvm`, or shell-completion upgrades already have; it is a known, accepted
shape for shell-integration upgrades industry-wide.

There is a real subtlety in whether *Python* can shortcut this by warning
proactively, worth spelling out because it looked promising and doesn't
work: `_tw_activate` currently does
`output=$(command taurworks project activate --shell 2>&1)` — stdout **and**
stderr are captured together and the combined text is later passed to
`eval`. That means the `--shell` payload contract already requires
everything Python writes in that mode, on either stream, to be a valid shell
assignment (or nothing) — Python cannot safely print a free-text warning
line to stderr in `--shell` mode today; `eval` would try to execute it as a
command. So a proactive staleness nudge cannot be "print an extra line" —
it has to be another well-formed `KEY=value` assignment appended to the
existing payload. That constraint doesn't block anything (see Option B),
but it does confirm the mechanism has to be a new *shell-comparison*, not a
new *Python-side print*: Python can report facts about itself, but only the
shell side can compare those facts against what it has loaded and decide
whether to say something.

Given that, the honest scoping is: ship the fix so shells **entering** it
from here forward are self-sustaining (see the phased recommendation below),
and accept that shells already open at ship time need exactly one manual
re-source to get in. After that one hop, they stay current on their own.

## Options considered

### Option A: `tw shell refresh` — explicit on-demand regenerate + re-source

Add a new shell function, sibling to `tw activate`, dispatched the same way
(`tw()` special-cases `shell refresh` before falling through to plain
delegation, exactly like it special-cases `activate` and `help` today):

```bash
tw shell refresh
```

Behavior: regenerate the on-disk helper file by calling
`taurworks shell print` (the existing read-only command, unchanged), write
it to the configured location, then `source` it into the current shell.
Target path resolution: default to the documented standard location
(`~/.config/taurworks/taurworks-shell.sh`), overridable via an environment
variable (`TAURWORKS_SHELL_HELPER_PATH`) for anyone who installed it
elsewhere — `taurworks shell print` stays a pure stdout emitter with no
opinion about paths, so this needs no change to that command's contract.

Pros:

- Solves both stated problems (on-disk drift and in-shell drift) in one
  user-invoked action, symmetric with how `tw activate` is the explicit
  shell-mutating sibling of read-only `taurworks project activate --print`.
- No CLI/payload schema changes required; reuses `taurworks shell print`
  as-is.
- Fully explicit and reversible — consistent with this repo's stated
  guardrail to make state-changing operations explicit (`README.md`'s
  "Safety and shell-integration guardrails" section).
- Needs no versioning scheme at all; unconditionally fetches whatever is
  currently packaged.

Cons:

- Purely reactive — the user has to know or remember to run it. On its own
  this does not solve the "silently missing for most of a session" failure
  mode from the dogfooding incident; it only makes the fix cheap once you
  decide to look.
- Does not touch any *other* already-open shell.

Recommendation: do first. It's low-risk, immediately useful on its own, and
is the thing Option B's warnings need to be able to point at.

### Option B: passive staleness detection, piggybacked on `tw activate`

Bake a content hash of the packaged helper into the printed file at
print-time (a Python-computed `hashlib.sha256` digest of
`read_shell_helper_text()`, truncated for readability — no new dependency,
no subprocess, no `sha256sum`/`shasum` portability question, since it's
computed in-process on the Python side). Store it as a constant near the
top of the generated script, e.g. `_TW_SHELL_HELPER_HASH="<hex>"`.

Extend the existing `taurworks project activate --shell` payload — which
`_tw_activate` already parses via `eval` on every `tw activate` call — with
one more assignment: `TAURWORKS_ACTIVATION_SHELL_HELPER_HASH="<hex>"`,
computed fresh from the currently installed package. `_tw_activate` compares
that against its own baked-in `_TW_SHELL_HELPER_HASH`. On mismatch, print one
non-blocking stderr note (activation still completes normally — fail-open,
same as other advisory warnings in this function today) pointing at
`tw shell refresh`.

Because this rides the subprocess call `_tw_activate` already makes, it adds
no new process spawn. Because it's an *additive* assignment line, an old
(pre-this-feature) sourced shell simply `eval`s the line into an unused
shell global and ignores it — harmless, and exactly why this has to be a shell
comparison rather than a Python-originated warning, per the bootstrapping
section above.

Pros:

- Closes the actual silent-drift gap the incident exposed, with no burden on
  the user to remember anything.
- Fail-open: a hash mismatch never blocks or degrades activation itself.
- Zero added subprocess cost (rides the existing `--shell` call).
- Self-sustaining once a shell is on a hash-aware version: running
  `tw shell refresh` (Option A) always pulls in both the fix *and* the
  latest comparison logic at once, so a shell that has entered this system
  never silently falls back out of it.

Cons:

- Only triggers on `tw activate`, not on other `tw ...` delegated commands
  (`tw root`, `tw project list`, etc.). Acceptable: those commands delegate
  straight through to `command taurworks ...` with no baked-in shell-side
  logic of their own, so there's nothing in them that can go stale in the
  same way — the risk this option covers is specifically staleness in the
  *shell function bodies themselves* (activate's flags, the legacy-trust
  prompt, etc.), and `tw activate` is where that logic lives and where the
  incident actually happened.
- Requires a small, additive field on an existing read-only-in-spirit
  payload (`project_resolution.py`); still just a fact about the installed
  package, not a new mutation.
- Still can't reach shells that never happen to run `tw activate` again.

Recommendation: do after Option A ships and gets one round of dogfooding
re-sourcing, precisely so the warning this option adds has something to
point users at that already exists.

### Option C: unconditional overwrite on every `tw` invocation (rejected)

Regenerate and silently re-source the helper file on every `tw` call, no
comparison, no confirmation.

Pros: simplest possible logic — "always fresh."

Cons:

- Silently rewrites a file whenever it's invoked, even if a user had hand-
  edited it, with no signal that anything changed.
- Constant disk writes for no benefit on the (common) case where nothing
  changed.
- Still cannot reach other open shells — the fundamental limit is unaffected
  by how eagerly the *current* shell tries to refresh.
- Directly at odds with this repo's stated conservative-mutation stance
  (`README.md`'s "Safety and shell-integration guardrails" section, "avoid
  implying hidden side effects") and with why `tw activate` itself is
  opt-in rather than automatic.

Recommendation: reject as a default. Option A already offers "get current"
as an explicit, cheap, one-word action; there is no reason to make it
implicit and lose the "was anything printed?" signal that lets a user notice
something changed.

### Option D: trigger regeneration from `scripts/develop` / pipx install-upgrade (rejected as primary)

Have `scripts/develop`, or a wrapper around `pipx install`/`pipx upgrade`,
regenerate `~/.config/taurworks/taurworks-shell.sh` automatically right
after install/upgrade.

Pros: keeps the on-disk file in sync at the moment of install/upgrade
without the user having to think about the shell layer at all.

Cons:

- `pipx` has no post-install/post-upgrade hook to attach to; this would mean
  wrapping `pipx` calls in a custom script, adding a maintenance surface for
  a partial fix.
- Partial by the user's own framing, and correctly so: it can regenerate the
  file on disk, but it categorically cannot reach any shell that is already
  open at the moment `pipx upgrade` runs — the exact same subprocess/parent-
  shell boundary applies here as everywhere else in this document. A user
  who upgrades in one terminal and keeps working in another gets no benefit
  in the second terminal regardless of what this option does.
- Silently overwrites the file with no user-visible action, which is a
  bigger surprise than Option A's explicit, user-invoked write.

Recommendation: do not implement as the primary mechanism. Options A and B
together already give a strictly better answer for the case this option is
trying to help with (a stale already-open shell) — this option cannot help
there at all, and where it could help (a shell not yet opened since
upgrade), the existing documented `source ...` step in a shell's startup
file already covers it for free once the file on disk is current. If wanted
at all, this belongs as a documentation nudge ("after upgrading, run
`tw shell refresh`") rather than an automatic hook.

### Option E: package `__version__` string instead of a content hash

Compare a semantic version string instead of a content hash.

Pros: human-readable ("you're on 0.4.0, latest installed is 0.5.0") instead
of an opaque hex digest.

Cons: `setup.py:5` does declare `version="0.1"`, but it is a static string
that has never been bumped and is not read anywhere at runtime — no code in
`src/taurworks/` calls `importlib.metadata.version("taurworks")` or
otherwise surfaces it, and `src/taurworks/__init__.py` is empty. Making that
string meaningful for staleness detection is a separate, larger decision
(establishing real bump discipline, deciding where it's read from, whether
it lines up with any future PyPI release) that this design shouldn't force
as a side effect of fixing shell staleness. A content hash needs none of
that: it answers exactly the question that matters ("did the shell helper's
actual behavior change since I sourced it?") without requiring anyone to
remember to bump anything, and works correctly even while the existing
version string stays frozen at `0.1`.

Recommendation: use a content hash for now (Option B). Revisit a
human-readable version string only if/when the project adopts real package
versioning for other reasons.

## Recommended phased approach

1. **`tw shell refresh` (Option A).** New shell function, dispatched by
   `tw()` alongside `activate`/`help`, that reruns `taurworks shell print`,
   overwrites the on-disk file at the documented (or
   `TAURWORKS_SHELL_HELPER_PATH`-overridden) location, and re-sources it.
   No CLI payload changes. Document it in `README.md` next to the existing
   `tw activate` shell-helper section, and add a CHANGELOG/upgrade note:
   "after upgrading `taurworks`, run `tw shell refresh` once per open shell
   (or re-source manually if your `tw` predates this command)."
2. **Passive hash-mismatch warning on `tw activate` (Option B).** Bake a
   content hash into the printed helper; add the corresponding live hash as
   one more field on the existing `taurworks project activate --shell`
   payload; compare in `_tw_activate` and print one non-blocking note
   pointing at `tw shell refresh` on mismatch. Ship this only after step 1
   has had at least one real dogfooding cycle, so the warning always has a
   concrete, already-shipped fix to name.
3. **Documentation cleanup (small, can ride with step 1).**
   `project/design/README.md`'s "Current design priorities" bullet list
   still describes legacy inspect/migrate and trusted hooks as not-yet-done;
   both shipped (`WI-ACTIVATION-CONFIG-0001`, `WI-LEGACY-BATCH-MIGRATION-0001`,
   `WI-TRUSTED-LEGACY-SOURCING-0001`). Fold an update into whichever PR lands
   step 1, or split it into its own small doc fix — either is fine, it's
   unrelated to the mechanism itself.

Explicitly not proposed: automatic regeneration triggered by install/upgrade
tooling (Option D), unconditional silent overwrite on every invocation
(Option C), or a semver-based comparison (Option E). Both real problems —
on-disk drift and in-shell drift — are addressed by the combination of
Option A (fixes it on demand, one word) and Option B (tells you when you
need to, for the one path where staleness is actually dangerous): nothing
here tries to make an already-open, never-touched-again shell fix itself,
because nothing running as a subprocess of that shell ever can.

## Non-goals for this design

- Automatically editing `.bashrc`, `.zshrc`, `.profile`, or any shell
  startup file — unchanged from the existing guardrail (`README.md:53-56`
  and `README.md`'s "Safety and shell-integration guardrails" section).
- Reaching or refreshing any shell other than the one in which
  `tw shell refresh` is actually invoked.
- Introducing a package-wide semantic version (Option E); a content hash is
  sufficient and is the recommended mechanism.
- Any change to activation semantics, trust-gating, or `config.toml`
  schema — this is purely about the shell-integration delivery layer.
- Detecting or preserving hand-edits to
  `~/.config/taurworks/taurworks-shell.sh`. The file remains fully
  generated and disposable by documented convention (`README.md` already
  tells users to add customizations to their own startup file *after* the
  `source` line, not inside the generated file); `tw shell refresh`
  overwrites it unconditionally, same as regenerating it manually today.
