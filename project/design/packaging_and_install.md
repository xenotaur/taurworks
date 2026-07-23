# Packaging and Install Design

## Status

This document is a design note. Nothing described here is implemented yet.
It proposes the packaging/install cleanup needed before taurworks is
public-release-ready: a one-step install for a new user on a fresh machine
or a Conda environment without taurworks, a real split between the
`taurworks` package and unrelated legacy dotfile scripts, a warning instead
of a silent failure when `taurworks` isn't on `$PATH`, and debug output
gated behind a flag instead of always-on.

## Purpose

taurworks today only reliably works on its original author's own machine,
because the install path assumes hand-editing `.bashrc` around undocumented
steps. Four concrete gaps:

1. **No install script.** `README.md` documents `pipx install --editable
   <path>` for `taurworks`/`tw`, but `tl` is installed by a different,
   separately-undocumented method. The README documents sourcing
   `sourceme/aliases.source` from a repo checkout path, but the user's own
   live setup instead sources a separately-placed `~/bin/tl.source` — a
   detail from the user's own description of their setup, not something
   version-controlled state can confirm on its own. Either way, `tw` and
   `tl` are installed by different methods today, and the README's
   documented `tl` method isn't the only one actually in use.
2. **The repo mixes two concerns.** `bin/` (27 files: `dot.bashrc`, byobu
   configs, `screen` wrappers, `migrate_legacy_projects.py`, etc.) is mostly
   pre-taurworks personal dotfile material with no dependency on the
   `taurworks` package — except `migrate_legacy_projects.py`, which does
   import `taurworks` internals (see Decisions #2 below). `sourceme/`
   (`aliases.source` for `tl`, `completions.source`, `man.source`) is
   taurworks' own shell-integration surface, parallel to
   `taurworks-shell.sh`.
3. **No PATH-loss diagnostic.** Switching into a Conda environment that
   lacks `taurworks` currently fails as a bare shell `command not found`
   with no indication of why or what to do.
4. **Unconditional progress narration.** `src/taurworks/manager.py`'s
   legacy top-level commands (`create`, `refresh`, `activate`, `projects`)
   print ~56 unconditional lines of step-by-step narration (`"Creating
   Conda environment..."`, `"✔ Taurworks config already up to date"`) with
   no flag to suppress them. `src/taurworks/cli.py`'s namespaced commands
   already route through formatter functions in `global_config.py`,
   `project_resolution.py`, etc., which is the right shape — but nothing
   currently distinguishes "normal output" from "the exact intermediate
   values that helped debug this" for either code path.

## Decisions

Made in discussion with the user (2026-07-22). Recorded here as decisions,
not options-to-relitigate; see "Options considered" below for the
alternatives that were weighed and why they lost.

1. **Install/setup command:** `taurworks setup`. A CLI-driven subcommand,
   not a standalone script, is the primary mechanism — it's usable
   regardless of whether taurworks was installed via `pipx`, `pip`, or (once
   supported) a future PyPI release, without a separate script to keep in
   sync with the package. A new `scripts/install` shim is to be added as a
   thin wrapper: `pipx install . --force && taurworks setup`, for the
   source-checkout entry point where a user hasn't run any taurworks command
   yet. Deliberately **not** `--editable`: `--editable` ties the installed
   command to the checkout it was installed from, so moving or deleting the
   clone afterward breaks the install. That trade-off is fine for
   `./scripts/develop`'s existing dev-install use case (see
   `README.md`'s "Developer setup" section), where the checkout is expected
   to persist and be edited in place, but wrong for a public end-user
   install, which should be a self-contained `pipx` install independent of
   the checkout's later fate. `--editable` stays documented as the
   development-install option; the new public shim uses a plain install.
2. **Repo split:** split `bin/` out (except `migrate_legacy_projects.py`,
   which stays with `taurworks`); keep `sourceme/` in `taurworks`. Most of
   `bin/`'s contents are unrelated personal dotfile material, not part of
   the `taurworks` package's public surface — they belong in a separate
   `taurscripts` package (or deletion, see open question below), not
   bundled with a public-release CLI tool. `bin/migrate_legacy_projects.py`
   is the one exception: it imports `taurworks.legacy`, `taurworks.manager`,
   and `taurworks.project_internals`, and `tests/migrate_legacy_projects_test.py`
   imports it directly by that file path — it is Taurworks-specific tool
   code, not unrelated material, and must be retained and relocated under
   the `taurworks` boundary (exact destination is an implementation
   decision, not this design) rather than moved to `taurscripts` or deleted
   along with the rest of `bin/`. `sourceme/` is `tl`'s actual delivery
   mechanism and is intended to stay packaged with `taurworks` since
   `taurworks setup` needs to place it — note `setup.py`'s `package_data`
   currently only declares `resources/shell/taurworks-shell.sh`, so wiring
   `sourceme/`'s content into packaging (whether by adding it to
   `package_data` or another mechanism) is implementation work this design
   assumes but does not yet specify.
3. **PyPI:** stays out of scope for this design. The public-release bar is
   "installable cleanly from a git checkout," not "on PyPI." This avoids
   forcing real semver discipline (`setup.py`'s `version = "0.1"` is
   currently frozen and unread at runtime) as a side effect of a packaging
   cleanup that doesn't need it.
4. **Conda PATH-loss:** runtime detection. `tw` (the sourced shell function)
   checks whether `taurworks` resolves on `$PATH` before delegating, and
   prints a pointed diagnostic naming the likely cause (Conda env switch)
   and the fix, instead of a bare `command not found`.
5. **Debug flag scope:** broad. One global `--debug` flag / `TAURWORKS_DEBUG`
   env var, applied both to `manager.py`'s legacy narration (the main
   target) and audited across `cli.py`'s namespaced formatter output for
   anything that's actually debug-shaped (internal resolution traces, not
   normal command results).

## What `taurworks setup` does

Idempotent, safe to re-run, modeled on the existing `tw shell refresh`
precedent (`shell_helper_refresh.md`) for the "regenerate + report" shape:

1. Print the packaged shell helper to the standard location — reuses
   `taurworks shell print`'s existing packaged-resource logic, unchanged.
   `$TAURWORKS_SHELL_HELPER_PATH`, if already set, takes precedence over
   both defaults below. Otherwise, default to
   `$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh` when `XDG_CONFIG_HOME`
   is set to a valid absolute path — matching the resolution
   `global_config.py` already uses for Taurworks' own config file — and
   fall back to `~/.config/taurworks/taurworks-shell.sh` only when
   `XDG_CONFIG_HOME` is unset or invalid. Writing the shell helper under a
   plain `~/.config` regardless of a configured `XDG_CONFIG_HOME` would
   split Taurworks' user state across two roots and print a startup-file
   `source` line pointing at the wrong location for that user.
2. Place the packaged `tl` source file at a documented, stable location
   (see open question below on exactly where) instead of the current
   ad-hoc "copy `sourceme/aliases.source` somewhere and remember where you
   put it" flow.
3. Print the exact `source` lines to add to the shell startup file — never
   edit `.bashrc`/`.zshrc`/`.profile` itself, preserving the existing
   guardrail (`README.md`'s "Safety and shell-integration guardrails"
   section, restated in `shell_helper_refresh.md`'s non-goals).
4. Report what it did and did not change, the same truth-first-summary
   convention `project refresh`/`project init` already use.

`taurworks setup` is explicitly **not** an activation-shell-mutating
command — it never needs to be sourced, because it only writes files and
prints instructions. This preserves the existing safety boundary
(`README.md:31-36`, `shell_helper_refresh.md`'s safety-boundary section): a
plain subprocess still cannot and does not try to mutate the parent shell.
The `source ...` step remains a manual, explicit, one-time action, same as
today, and re-running `taurworks setup` after an upgrade slots in next to
the already-designed `tw shell refresh` (regenerate-and-resource *within* an
already-sourced shell) rather than replacing it — `setup` is for
first-install and for placing `tl`; `tw shell refresh` stays the fix for a
shell that's already sourced but stale.

## PATH-loss diagnostic

Add a check inside the sourced `tw` function, before it delegates to
`command taurworks ...`: if `taurworks` does not resolve, print a diagnostic
to stderr identifying the likely cause (an active Conda environment that
doesn't have `taurworks` installed) and the fix (switch back, or `pipx
install` isn't Conda-env-scoped so this shouldn't normally happen — check
`which taurworks` / `pipx list`), then return non-zero instead of letting
the shell's own bare `command not found` be the only signal.

A single check at initial delegation is not sufficient by itself: `tw
activate` itself runs `conda activate <name>` mid-function and can make
further internal `command taurworks ...` calls afterward (for example
`legacy inspect` or `project trust set` during interactive untrusted-legacy
handling) — if the newly-activated environment hides `taurworks`, the
entry check already passed before `conda activate` ran, and those
later internal calls would still hit a bare `command not found` with no
diagnostic. The check therefore needs to guard every internal
`command taurworks ...` call site within `tw`, not only the outermost
entry point — either by re-checking resolvability at each call site, or by
resolving and caching the executable path once before any Conda activation
happens in a given invocation and using that resolved path for every
subsequent internal call in the same invocation. Exact mechanism is
implementation detail for the work item; the requirement is that no
internal call path can silently regress to a bare shell error post-Conda-
activation.

This is read-only diagnostic logic living in the already-sourced shell
function — no new subprocess, no change to `taurworks`'s Python side,
consistent with the same "only the shell side can compare live state"
reasoning `shell_helper_refresh.md` used for its hash-mismatch warning.

`tl` gets no equivalent change: it never depends on `taurworks` being
resolvable in the first place (that's the entire point of it being a
break-glass fallback, per `WI-TL-BREAKGLASS-0001`), so there's nothing for
it to detect.

## Debug flag

Add a global `--debug` flag on the top-level `argparse` parser
(`src/taurworks/cli.py:299`) and an equivalent `TAURWORKS_DEBUG` environment
variable (flag wins if both are set). `TAURWORKS_SHELL_HELPER_PATH` is an
existing precedent for env-var-based configuration in the shell-helper
layer, though it is env-var-only today with no corresponding CLI flag;
`--debug`/`TAURWORKS_DEBUG` adds the flag-plus-env-var pairing as a new,
slightly richer pattern rather than reusing an existing one. Threaded
through as a single boolean available to command handlers, not per-command
flags — there's one coherent "give me more detail" axis here, not several
independent ones per subcommand.

Audit scope (broad, per decision above):

- `src/taurworks/manager.py`: all ~56 unconditional `print()` calls in
  `create`, `refresh`, `activate`, and `projects` move behind the debug
  flag *except* the final actionable lines each command already prints on
  success/failure (e.g. `"To activate, run: tw activate {project_name}"`,
  `"✔ Project '{project_name}' created successfully."` at the end of a run)
  — those are the actual result, not narration, and stay unconditional.
- `src/taurworks/cli.py` and its formatter modules (`global_config.py`,
  `project_resolution.py`, `project_registry.py`, `dev.py`, `legacy.py`):
  audit each formatter for output that's actually a debug trace (internal
  resolution steps, intermediate diagnostic fields not needed for the
  command's stated purpose) versus the command's actual documented result.
  Most of this is already correctly shaped as "the result," per the
  existing README documentation of exactly what each command prints — this
  audit is expected to find few or no changes here, but the user asked for
  it to be checked rather than assumed clean.

This is implementation-detail auditing, not a design decision — the
per-line classification happens in the work item, not this doc.

## Options considered

### Install mechanism: script vs. CLI subcommand vs. tightened docs (decided: hybrid)

- **Standalone `install.sh`.** Pro: works before `taurworks` is even
  installed. Con: a second thing to keep in sync with the package, and it's
  unusable for anyone who installs by a means other than a git checkout
  (impossible to `curl | bash` a script that lives inside the repo it's
  installing, without picking a hosting/distribution story that's out of
  scope while PyPI is out of scope).
- **`taurworks setup` CLI subcommand only.** Pro: single mechanism,
  versioned with the package, works for `pip`/`pipx`/future-PyPI installs
  identically. Con: chicken-and-egg for a fresh git checkout — you need
  `taurworks` importable before you can run `taurworks setup`, so there's
  still one prior step (`pipx install`) that has to be documented
  separately.
- **Tightened documented sequence, no new code.** Pro: zero new
  maintenance surface. Con: doesn't fix the actual `tl`-placement gap; still
  relies on a user copy-pasting multiple commands correctly, which is
  exactly the failure mode that produced today's undocumented `~/bin/tl.source`.
- **Decision: hybrid.** `taurworks setup` is the real mechanism, callable
  after any install method. A new `scripts/install` is to be added only as
  a documented, one-line shim for the from-git-checkout path (`pipx
  install . --force && taurworks setup`, non-editable — see Decisions #1),
  not a second implementation.

### Repo split granularity (decided: split `bin/`, keep `sourceme/`)

- **Split both `bin/` and `sourceme/` into `taurscripts`.** Full purity, but
  `sourceme/`'s only real content (`tl`'s source file) is intentionally
  feature-frozen and dependency-free by design (`WI-TL-BREAKGLASS-0001`) —
  moving it to a second package to version and install would add release
  overhead for something explicitly designed to never change, and `taurworks
  setup` needs to be able to place it as part of one coherent install step.
- **Split neither; just note the split as a documentation note.** Doesn't
  address the user's stated pain point that the repo is "trying to do two
  things at once."
- **Decision:** with one exception, `bin/`'s contents share no dependency
  relationship with the `taurworks` Python package and aren't part of any
  documented public surface — they're pure historical personal dotfile
  material. The exception is `migrate_legacy_projects.py`, which imports
  `taurworks` internals and is imported by a test under that exact path
  (see Decisions #2); it stays under the `taurworks` boundary rather than
  moving with the rest of `bin/`. `sourceme/`
  is taurworks' own delivery mechanism for `tl` and stays.

## Open questions for the follow-up work item(s)

These are implementation-level questions, deliberately left open here
rather than pre-decided, since they don't change this design's shape:

- **Where does `taurworks setup` place the `tl` source file?** Candidates:
  `tl.source` alongside `taurworks-shell.sh` under the same
  `$XDG_CONFIG_HOME`-aware `taurworks` config directory (see "What
  `taurworks setup` does" above; one config directory for both halves of
  the activation stack) vs. keeping it path-relative to a checkout (current
  README behavior, but breaks for anyone who deletes the checkout after
  install). Recommend the former for symmetry with the shell helper's own
  location, but this needs a
  quick check against `WI-TL-BREAKGLASS-0001`'s framing of `tl` as
  dependency-free — placing it under the same config directory as `tw`
  doesn't create a code dependency, only a shared install location, so it
  should be compatible; confirm during implementation.
- **`bin/` disposition: `taurscripts` package or deletion?** Applies to
  `bin/`'s contents other than `migrate_legacy_projects.py`, which is
  already decided to stay under the `taurworks` boundary (Decisions #2).
  For the rest, depends on whether anything outside this repo (or outside
  the original author's own machine) actually uses `bin/`'s contents today.
  If nothing does, deletion is simpler than migrating dead weight into a
  new package. Audit actual usage before deciding; do not assume.
- **Exact `--debug` line-by-line classification in `manager.py`/`cli.py`.**
  Listed by module above; the specific keep/gate decision per print
  statement belongs in the implementing work item, not this design.

## Non-goals for this design

- Changing `tw activate`/`tw shell refresh` semantics — this is purely
  about install/packaging delivery, not activation behavior (unchanged from
  `shell_helper_refresh.md`'s non-goals).
- PyPI publication (see Decisions #3).
- Introducing real semantic-version bump discipline for `taurworks` itself
  — not needed for a content-hash-free, git-checkout-based install story.
- Automatically editing `.bashrc`, `.zshrc`, `.profile`, or any shell
  startup file — `taurworks setup` prints the `source` line; the user adds
  it themselves, unchanged guardrail.
- Deciding `bin/`'s exact destination (new package vs. deletion) — flagged
  as an open question above, resolved during implementation after a usage
  audit.
