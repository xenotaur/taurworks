# Dogfood plan: validating this session's work

This document is a human-readable walkthrough of everything delivered in
this session, with the reasoning behind each check. The companion script,
[`dogfood-session-review.sh`](dogfood-session-review.sh), automates the
same checks with PASS/FAIL assertions so you can run the whole thing
unattended and get a summary, or step through it manually section by
section using this doc as a guide.

**Scope covered:**

| Work item | PR | What it changed |
|---|---|---|
| `WI-BIN-REPO-SPLIT-0001` | #88 | Split `bin/` (personal dotfiles) into a private sibling repo, `xenotaur/taurscripts` |
| `WI-TAURWORKS-SETUP-0001` | #93 | `taurworks setup` + `scripts/install` one-step install |
| `WI-TW-PATH-LOSS-DIAGNOSTIC-0001` | #94 | Clear diagnostic when a Conda switch hides `taurworks` from `$PATH` |
| `WI-TAURWORKS-DEBUG-FLAG-0001` | #95 | `--debug`/`$TAURWORKS_DEBUG` flag gating `manager.py` narration |
| `WI-LEGACY-MIGRATE-TL-FALLBACK-0001` | #97 | Abandoned (no code) — a workspace audit found nothing left to migrate |
| dev-scope decision | #98 | Decided `taurworks dev` v1 = `clean/test/smoke/lint/format/build`, delegate-only |
| `WI-DEV-WORKFLOW-AUTOMATION-0001` | #99, #100 | Implemented the six v1 `taurworks dev` commands |
| doc-work / roadmap refresh | #96, #101, #102 | Kept README/roadmap/`--help` text in sync with what shipped |

**Isolation:** every check runs against a throwaway `$HOME`/`$XDG_CONFIG_HOME`/
workspace, created fresh in a temp directory and deleted at the end. Nothing
here touches your real `~/Workspace`, your real `~/.config/taurworks`, or
your real shell.

---

## 0. Setup

```bash
cd /Users/centaur/Workspace/Taurworks/taurworks
git checkout master && git pull
```

The script creates its own isolated `$HOME`/`$XDG_CONFIG_HOME`/workspace
under `mktemp -d` and cleans up on exit (including on failure, via a trap).
It uses the `Taurworks` conda env's Python
(`/Users/centaur/anaconda3/envs/Taurworks/bin/python`) if present, falling
back to whatever `python3` is on `$PATH` otherwise — the fallback is noted
in the script's output since some checks assume the pinned tool versions
(`black`, `ruff`) this session used.

---

## 1. Packaging / install series

### 1a. The `bin/` split actually happened

`bin/` should no longer exist in this repo — it was moved, with full git
history, into a new private sibling repo.

```bash
ls bin/ 2>&1   # expect: No such file or directory
```

If `gh` is authenticated, the script also checks that `xenotaur/taurscripts`
exists and is private. This check is skipped (not failed) if `gh` isn't
authenticated, since it's a network-dependent nice-to-have, not core to
validating the split.

### 1b. One-step install, and idempotency

```bash
scripts/install
```

This should run a non-editable `pipx install . --force` followed by
`taurworks setup`, writing the shell helper and `tl.source` file to
`$XDG_CONFIG_HOME/taurworks/`. Rerunning `taurworks setup` alone should
report both files as unchanged — this is the idempotency guarantee the WI's
acceptance criteria required.

**What could go wrong:** if `pipx` isn't installed on your machine, this
step will fail before it even reaches the `taurworks setup` half. That's an
environment gap, not a regression in this session's work — the script
notes this distinction in its output.

### 1c. The shell helper actually defines `tw`/`tl`

```bash
source "$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh"
type tw
type tl
```

Both should report as shell functions, not "not found."

---

## 2. `tw` Conda PATH-loss diagnostic

**The scenario this WI fixed:** you `conda activate` into an environment
that doesn't have `taurworks` installed, and `tw <anything>` used to fail
with a bare, unhelpful `command not found`. Now it should name the likely
cause and suggest a next step.

```bash
env -i PATH="/usr/bin:/bin" CONDA_DEFAULT_ENV="some-other-env" bash -c '
  source "$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh"
  tw project list
  echo "exit: $?"
'
```

**Expect:** stderr mentions `Conda` and the environment name
(`some-other-env`), does **not** contain the literal string
`command not found`, and the exit code is non-zero.

This exercises the *fallthrough* delegation path specifically. The WI's
acceptance criteria also required all 8 call sites in the shell helper to
be guarded (including `tw activate`'s pre- and post-`conda activate` calls,
`tw shell refresh`, and `tw help`) — those are covered by the automated
test suite (section 6) rather than manually here, since reproducing all 8
by hand would be repetitive; the fallthrough case above is the
representative, easiest-to-eyeball one.

---

## 3. `--debug` / `$TAURWORKS_DEBUG` flag

**The scenario this WI fixed:** `taurworks create`/`refresh` used to print
~56 lines of step-by-step narration unconditionally. Now that narration is
opt-in.

```bash
taurworks create DogfoodProj
```

**Expect:** quiet output — just the final result line(s) (e.g. `✔ Project
'DogfoodProj' metadata created...`, `To activate, run: tw activate
DogfoodProj`), no "Creating..." step announcements.

```bash
taurworks --debug create DogfoodProj2
```

**Expect:** the same final result lines, *plus* step-by-step narration
("Creating Conda environment...", "Skipping Conda environment
creation...", etc.).

```bash
TAURWORKS_DEBUG=1 taurworks create DogfoodProj3
```

**Expect:** same narration as `--debug`, proving the env-var fallback
works.

---

## 4. `taurworks dev` v1 workflow automation

This is the largest single piece of work this session, so it gets the most
thorough check.

### 4a. Happy path — dogfooding against this repo's own `scripts/`

```bash
cd /Users/centaur/Workspace/Taurworks/taurworks
taurworks dev lint
taurworks dev smoke
taurworks dev clean
```

Each should delegate to the matching `./scripts/<name>` and produce the
same output/exit code as running that script directly. `dev clean` is safe
to run for real — it only removes regenerable `__pycache__`/`.ruff_cache`
directories (never source files); the script double-checks this by
comparing against `scripts/clean --dry-run`'s own preview before running
it for real.

`dev test` and `dev build` are included too but are slower/heavier
(`test` runs the full ~350-test suite; `build` produces a real wheel/sdist,
which the script cleans up afterward via `dev clean` again) — both are
still fast enough to include unconditionally.

### 4b. The two review-caught design fixes

**Tier 1 config must come from `project_root`, not a nested `working_dir`.**
This was a real bug caught in review of the *planning* PR (before any code
was written) — the WI originally conflated the two, which would have
silently missed a project's `[dev.commands]` override whenever
`working_dir` pointed somewhere nested.

```bash
mkdir -p "$TAURWORKS_WORKSPACE/NestedProj/repo/scripts"
mkdir -p "$TAURWORKS_WORKSPACE/NestedProj/.taurworks"
cat > "$TAURWORKS_WORKSPACE/NestedProj/.taurworks/config.toml" <<'EOF'
schema_version = 1
[paths]
working_dir = "repo"
[dev.commands]
test = "echo tier1-config-ran"
EOF
cat > "$TAURWORKS_WORKSPACE/NestedProj/repo/scripts/test" <<'EOF'
#!/bin/sh
pwd
echo tier2-script-ran
EOF
chmod +x "$TAURWORKS_WORKSPACE/NestedProj/repo/scripts/test"
cd "$TAURWORKS_WORKSPACE/NestedProj"
taurworks dev test
```

**Expect:** `tier1-config-ran` — the config override wins, proving it was
read from `project_root` (where `.taurworks/config.toml` actually lives)
rather than from the nested `working_dir` (where the old, buggy design
would have looked).

**Delegated commands must run with `cwd` set to the resolved working
directory.** This was the second review-caught bug in the same planning
round: without it, a delegated script invoked from a different directory
than expected would silently operate on the wrong files.

```bash
rm "$TAURWORKS_WORKSPACE/NestedProj/.taurworks/config.toml"   # force Tier 2
cat > "$TAURWORKS_WORKSPACE/NestedProj/.taurworks/config.toml" <<'EOF'
schema_version = 1
[paths]
working_dir = "repo"
EOF
cd "$TAURWORKS_WORKSPACE/NestedProj"
taurworks dev test
```

**Expect:** the printed `pwd` is `$TAURWORKS_WORKSPACE/NestedProj/repo`
(the resolved working directory), not
`$TAURWORKS_WORKSPACE/NestedProj` (where you actually ran the command
from).

### 4c. Failure modes — caught in review of the *implementation* PR

Three more real bugs were caught after the code was written: a malformed
config used to silently fall through to Tier 2 instead of reporting the
error, and both `shlex.split` and `subprocess.run` failures could leak a
raw Python traceback instead of a clean CLI error.

```bash
mkdir -p "$TAURWORKS_WORKSPACE/Broken/.taurworks"
cd "$TAURWORKS_WORKSPACE/Broken"
taurworks dev test
```
**Expect:** `no delegation target found`, mentioning both
`[dev.commands].test` and the `scripts/test` path it checked; exit 1.

```bash
cat > "$TAURWORKS_WORKSPACE/Broken/.taurworks/config.toml" <<'EOF'
schema_version = 1
[dev]
commands = "not-a-table"
EOF
taurworks dev test
```
**Expect:** `could not be read`, mentioning the underlying error; exit 1;
**no** `Traceback` in the output.

```bash
cat > "$TAURWORKS_WORKSPACE/Broken/.taurworks/config.toml" <<'EOF'
schema_version = 1
[dev.commands]
test = "pytest \"unterminated"
EOF
taurworks dev test
```
**Expect:** `could not be parsed`, exit 1, no `Traceback`.

---

## 5. Documentation consistency

Two review rounds this session caught cases where fixing one doc left a
sibling doc (or a different section of the same doc) stale. This section
spot-checks that the fixes actually landed everywhere.

```bash
taurworks dev --help | grep -i "workflow-automation slice"
grep -A2 "taurworks dev \.\.\." README.md | head -5
grep -A3 "^## Phase 4" project/roadmap/roadmap.md
```

**Expect:** the `--help` text, the README, and roadmap Phase 4 all agree
that the v1 commands are implemented — none of them should say `dev`
"does not run workflow automation" or "remains read-only" anymore.

---

## 6. Full automated suite

```bash
cd /Users/centaur/Workspace/Taurworks/taurworks
lrh validate
python -m black --check src tests
python -m ruff check src tests
PYTHONPATH=src:tests python -m unittest discover -s tests -p "*_test.py"
```

**Expect:** `lrh validate` reports 0 errors/warnings; black and ruff report
clean; the test suite ends in `OK` with ~350 tests (the exact count will
have grown further if any work has landed since this document was
written — that's fine, "OK" is what matters).

---

## Interpreting the results

The script prints a `PASS`/`FAIL` line per check and a summary at the end.
A `FAIL` means one of:

1. A real regression — something this session shipped has broken since.
   Worth investigating with `git log` / `git bisect` from this session's
   PRs (#88, #93–#102).
2. An environment gap on this machine (missing `pipx`, `gh` not
   authenticated, wrong Python on `$PATH`) — the script tries to
   distinguish these with explicit notes, but use judgment.

A `SKIP` (used for a couple of optional network-dependent checks) is not a
failure — it means the check couldn't run here, not that it failed.
