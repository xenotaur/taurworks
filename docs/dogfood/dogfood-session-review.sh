#!/bin/bash
# Dogfood validation for this session's work on xenotaur/taurworks.
# See dogfood-session-review.md (companion doc) for the reasoning behind
# each check.
#
# Usage:
#   ./dogfood-session-review.sh [path-to-taurworks-repo]
#
# Defaults to the current directory if no path is given. Everything runs
# against an isolated $HOME/$XDG_CONFIG_HOME/workspace under mktemp -d,
# cleaned up on exit -- nothing here touches your real workspace or config.

set -u

REPO_ROOT="${1:-$PWD}"
if [ ! -f "$REPO_ROOT/src/taurworks/cli.py" ]; then
    echo "error: $REPO_ROOT does not look like the taurworks repo (no src/taurworks/cli.py found)" >&2
    echo "usage: $0 [path-to-taurworks-repo]" >&2
    exit 2
fi
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"

if [ -x /Users/centaur/anaconda3/envs/Taurworks/bin/python ]; then
    PYTHON_BIN=/Users/centaur/anaconda3/envs/Taurworks/bin/python
    PYTHON_ENV_NOTE="Taurworks conda env (pinned tool versions)"
else
    PYTHON_BIN="$(command -v python3 || command -v python)"
    PYTHON_ENV_NOTE="fallback python3 on \$PATH -- black/ruff versions may differ from what this session used"
fi

DOGFOOD_HOME="$(mktemp -d)"
cleanup() { rm -rf "$DOGFOOD_HOME"; }
trap cleanup EXIT

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILED_CHECKS=()

section() {
    echo
    echo "=== $1 ==="
}

pass() {
    echo "  PASS: $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
    echo "  FAIL: $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILED_CHECKS+=("$1")
}

skip() {
    echo "  SKIP: $1"
    SKIP_COUNT=$((SKIP_COUNT + 1))
}

echo "Dogfood review for: $REPO_ROOT"
echo "Python: $PYTHON_BIN ($PYTHON_ENV_NOTE)"
echo "Isolated home: $DOGFOOD_HOME"

export HOME="$DOGFOOD_HOME/home"
export XDG_CONFIG_HOME="$DOGFOOD_HOME/xdg"
export TAURWORKS_WORKSPACE="$DOGFOOD_HOME/workspace"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$TAURWORKS_WORKSPACE"
unset TAURWORKS_SHELL_HELPER_PATH TAURWORKS_DEBUG CONDA_DEFAULT_ENV 2>/dev/null

PYTHON_DIR="$(dirname "$PYTHON_BIN")"
export PATH="$PYTHON_DIR:$PATH"
export PYTHONPATH="$REPO_ROOT/src"

run_taurworks() {
    "$PYTHON_BIN" -m taurworks.cli "$@"
}

# ---------------------------------------------------------------------
section "1a. bin/ split (WI-BIN-REPO-SPLIT-0001)"
# ---------------------------------------------------------------------

if [ -e "$REPO_ROOT/bin" ]; then
    fail "bin/ still exists in the repo (expected it to be split out)"
else
    pass "bin/ does not exist in the repo"
fi

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if gh repo view xenotaur/taurscripts --json isPrivate --jq .isPrivate 2>/dev/null | grep -q true; then
        pass "xenotaur/taurscripts exists and is private"
    else
        fail "xenotaur/taurscripts not found or not private"
    fi
else
    skip "xenotaur/taurscripts existence check (gh not authenticated)"
fi

# ---------------------------------------------------------------------
section "1b/1c. One-step install + idempotency (WI-TAURWORKS-SETUP-0001)"
# ---------------------------------------------------------------------

PIPX_BIN="$(command -v pipx || true)"
if [ -n "$PIPX_BIN" ] && "$PIPX_BIN" --version >/dev/null 2>&1; then
    if (cd "$REPO_ROOT" && ./scripts/install >"$DOGFOOD_HOME/install.log" 2>&1); then
        pass "scripts/install completed"
    else
        fail "scripts/install failed (see $DOGFOOD_HOME/install.log) -- if the log shows 'ModuleNotFoundError: No module named pipx', that's pipx itself being broken on this machine (its shebang points at a Python without the pipx module installed), not a regression in this session's work"
    fi
elif [ -n "$PIPX_BIN" ]; then
    skip "scripts/install (pipx found at $PIPX_BIN but broken -- 'pipx --version' failed; a pre-existing environment issue, not a regression in this session's work)"
else
    skip "scripts/install (pipx not installed on this machine)"
fi

SHELL_HELPER="$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh"
TL_SOURCE="$XDG_CONFIG_HOME/taurworks/tl.source"

if [ -f "$SHELL_HELPER" ] && [ -f "$TL_SOURCE" ]; then
    pass "taurworks setup wrote both the shell helper and tl.source"
else
    # scripts/install may have been skipped; run setup directly via the
    # module so the rest of this script still has something to source.
    run_taurworks setup >"$DOGFOOD_HOME/setup1.log" 2>&1
    if [ -f "$SHELL_HELPER" ] && [ -f "$TL_SOURCE" ]; then
        pass "taurworks setup wrote both the shell helper and tl.source"
    else
        fail "taurworks setup did not write expected files (see $DOGFOOD_HOME/setup1.log)"
    fi
fi

RERUN_OUTPUT="$(run_taurworks setup 2>&1)"
if echo "$RERUN_OUTPUT" | grep -q "unchanged" && ! echo "$RERUN_OUTPUT" | grep -qi "error"; then
    pass "taurworks setup is idempotent on rerun"
else
    fail "taurworks setup rerun did not report unchanged (output: $RERUN_OUTPUT)"
fi

if [ -f "$SHELL_HELPER" ] && [ -f "$TL_SOURCE" ]; then
    # shellcheck disable=SC1090
    source "$SHELL_HELPER"
    # shellcheck disable=SC1090
    source "$TL_SOURCE"
    if type tw >/dev/null 2>&1 && type tl >/dev/null 2>&1; then
        pass "shell helper + tl.source together define both tw and tl"
    else
        fail "shell helper did not define tw/tl"
    fi
else
    skip "sourcing shell helper (not written)"
fi

# ---------------------------------------------------------------------
section "2. tw Conda PATH-loss diagnostic (WI-TW-PATH-LOSS-DIAGNOSTIC-0001)"
# ---------------------------------------------------------------------

if [ -f "$SHELL_HELPER" ]; then
    DIAG_OUTPUT="$(env -i PATH="/usr/bin:/bin" CONDA_DEFAULT_ENV="some-other-env" HOME="$HOME" bash -c "
        source '$SHELL_HELPER'
        tw project list
    " 2>&1)"
    DIAG_EXIT=$?
    if [ "$DIAG_EXIT" -ne 0 ] \
        && ! echo "$DIAG_OUTPUT" | grep -qi "command not found" \
        && echo "$DIAG_OUTPUT" | grep -qi "conda" \
        && echo "$DIAG_OUTPUT" | grep -q "some-other-env"; then
        pass "PATH-loss diagnostic fires with a clear message, not a bare command-not-found"
    else
        fail "PATH-loss diagnostic did not behave as expected (exit=$DIAG_EXIT, output: $DIAG_OUTPUT)"
    fi
else
    skip "PATH-loss diagnostic check (shell helper not written)"
fi

# ---------------------------------------------------------------------
section "3. --debug / \$TAURWORKS_DEBUG flag (WI-TAURWORKS-DEBUG-FLAG-0001)"
# ---------------------------------------------------------------------

QUIET_OUT="$(run_taurworks create DogfoodProjQuiet 2>&1)"
if ! echo "$QUIET_OUT" | grep -q "Creating" && echo "$QUIET_OUT" | grep -q "To activate, run"; then
    pass "taurworks create is quiet by default (no step narration)"
else
    fail "taurworks create default output unexpected: $QUIET_OUT"
fi

DEBUG_OUT="$(run_taurworks --debug create DogfoodProjDebug 2>&1)"
if echo "$DEBUG_OUT" | grep -q "Creating" || echo "$DEBUG_OUT" | grep -qi "Skipping Conda"; then
    pass "taurworks --debug create shows step narration"
else
    fail "taurworks --debug create did not show narration: $DEBUG_OUT"
fi

ENV_DEBUG_OUT="$(TAURWORKS_DEBUG=1 run_taurworks create DogfoodProjEnvDebug 2>&1)"
if echo "$ENV_DEBUG_OUT" | grep -q "Creating" || echo "$ENV_DEBUG_OUT" | grep -qi "Skipping Conda"; then
    pass "\$TAURWORKS_DEBUG=1 shows step narration (env-var fallback works)"
else
    fail "\$TAURWORKS_DEBUG=1 did not show narration: $ENV_DEBUG_OUT"
fi

# ---------------------------------------------------------------------
section "4a. taurworks dev v1 happy path (WI-DEV-WORKFLOW-AUTOMATION-0001)"
# ---------------------------------------------------------------------

(
    cd "$REPO_ROOT" || exit 1

    LINT_OUT="$(run_taurworks dev lint 2>&1)"
    if [ $? -eq 0 ]; then
        pass "taurworks dev lint delegates and succeeds"
    else
        fail "taurworks dev lint failed: $LINT_OUT"
    fi

    SMOKE_OUT="$(run_taurworks dev smoke 2>&1)"
    if [ $? -eq 0 ]; then
        pass "taurworks dev smoke delegates and succeeds"
    else
        fail "taurworks dev smoke failed: $SMOKE_OUT"
    fi

    TEST_OUT="$(run_taurworks dev test 2>&1)"
    if [ $? -eq 0 ]; then
        pass "taurworks dev test delegates and succeeds"
    else
        fail "taurworks dev test failed: $TEST_OUT"
    fi

    DRYRUN_TARGETS="$(./scripts/clean --dry-run 2>&1)"
    CLEAN_OUT="$(run_taurworks dev clean 2>&1)"
    if [ $? -eq 0 ]; then
        pass "taurworks dev clean delegates and succeeds (dry-run preview: $(echo "$DRYRUN_TARGETS" | tr '\n' ' '))"
    else
        fail "taurworks dev clean failed: $CLEAN_OUT"
    fi
)

# ---------------------------------------------------------------------
section "4b. Review-caught design fixes: project_root vs work_directory_guess"
# ---------------------------------------------------------------------

NESTED_PROJ="$TAURWORKS_WORKSPACE/NestedProj"
mkdir -p "$NESTED_PROJ/repo/scripts" "$NESTED_PROJ/.taurworks"
cat > "$NESTED_PROJ/.taurworks/config.toml" <<'EOF'
schema_version = 1
[paths]
working_dir = "repo"
[dev.commands]
test = "echo tier1-config-ran"
EOF
cat > "$NESTED_PROJ/repo/scripts/test" <<'EOF'
#!/bin/sh
pwd
echo tier2-script-ran
EOF
chmod +x "$NESTED_PROJ/repo/scripts/test"

TIER1_OUT="$(cd "$NESTED_PROJ" && run_taurworks dev test 2>&1)"
if echo "$TIER1_OUT" | grep -q "tier1-config-ran"; then
    pass "Tier 1 config read from project_root, even with a nested working_dir"
else
    fail "Tier 1 config was not used with nested working_dir: $TIER1_OUT"
fi

cat > "$NESTED_PROJ/.taurworks/config.toml" <<'EOF'
schema_version = 1
[paths]
working_dir = "repo"
EOF
CWD_OUT="$(cd "$NESTED_PROJ" && run_taurworks dev test 2>&1)"
EXPECTED_CWD="$(cd "$NESTED_PROJ/repo" && pwd)"
if echo "$CWD_OUT" | grep -qF "$EXPECTED_CWD"; then
    pass "Delegated subprocess runs with cwd set to the resolved working directory"
else
    fail "Delegated subprocess did not run in the resolved working directory: $CWD_OUT (expected $EXPECTED_CWD)"
fi

# ---------------------------------------------------------------------
section "4c. Review-caught error handling: config errors, parse errors, launch failures"
# ---------------------------------------------------------------------

BROKEN_PROJ="$TAURWORKS_WORKSPACE/Broken"
mkdir -p "$BROKEN_PROJ/.taurworks"

NEITHER_OUT="$(cd "$BROKEN_PROJ" && run_taurworks dev test 2>&1)"
NEITHER_EXIT=$?
if [ "$NEITHER_EXIT" -ne 0 ] && echo "$NEITHER_OUT" | grep -q "no delegation target found" \
    && echo "$NEITHER_OUT" | grep -q "\[dev.commands\].test"; then
    pass "Neither-tier-resolves failure is clear and non-zero"
else
    fail "Neither-tier-resolves case unexpected (exit=$NEITHER_EXIT): $NEITHER_OUT"
fi

cat > "$BROKEN_PROJ/.taurworks/config.toml" <<'EOF'
schema_version = 1
[dev]
commands = "not-a-table"
EOF
MALFORMED_OUT="$(cd "$BROKEN_PROJ" && run_taurworks dev test 2>&1)"
MALFORMED_EXIT=$?
if [ "$MALFORMED_EXIT" -ne 0 ] && echo "$MALFORMED_OUT" | grep -q "could not be read" \
    && ! echo "$MALFORMED_OUT" | grep -q "Traceback"; then
    pass "Malformed config fails cleanly, no fallthrough, no traceback"
else
    fail "Malformed config case unexpected (exit=$MALFORMED_EXIT): $MALFORMED_OUT"
fi

cat > "$BROKEN_PROJ/.taurworks/config.toml" <<'EOF'
schema_version = 1
[dev.commands]
test = "pytest \"unterminated"
EOF
UNPARSEABLE_OUT="$(cd "$BROKEN_PROJ" && run_taurworks dev test 2>&1)"
UNPARSEABLE_EXIT=$?
if [ "$UNPARSEABLE_EXIT" -ne 0 ] && echo "$UNPARSEABLE_OUT" | grep -q "could not be parsed" \
    && ! echo "$UNPARSEABLE_OUT" | grep -q "Traceback"; then
    pass "Unparseable command string fails cleanly, no traceback"
else
    fail "Unparseable command case unexpected (exit=$UNPARSEABLE_EXIT): $UNPARSEABLE_OUT"
fi

cat > "$BROKEN_PROJ/.taurworks/config.toml" <<'EOF'
schema_version = 1
[dev.commands]
test = "/nonexistent/binary-does-not-exist"
EOF
LAUNCH_OUT="$(cd "$BROKEN_PROJ" && run_taurworks dev test 2>&1)"
LAUNCH_EXIT=$?
if [ "$LAUNCH_EXIT" -ne 0 ] && echo "$LAUNCH_OUT" | grep -q "failed to run" \
    && ! echo "$LAUNCH_OUT" | grep -q "Traceback"; then
    pass "Unlaunchable command fails cleanly, no traceback"
else
    fail "Unlaunchable command case unexpected (exit=$LAUNCH_EXIT): $LAUNCH_OUT"
fi

# ---------------------------------------------------------------------
section "5. Documentation consistency"
# ---------------------------------------------------------------------

HELP_OUT="$(cd "$REPO_ROOT" && run_taurworks dev --help 2>&1)"
if echo "$HELP_OUT" | grep -qi "workflow-automation slice"; then
    pass "taurworks dev --help describes the v1 workflow-automation slice"
else
    fail "taurworks dev --help does not mention the v1 slice: $HELP_OUT"
fi

if grep -q "delegate-only v1 workflow-automation slice" "$REPO_ROOT/README.md"; then
    pass "README.md describes the v1 workflow-automation slice"
else
    fail "README.md does not mention the v1 slice"
fi

if grep -A5 "^## Phase 4" "$REPO_ROOT/project/roadmap/roadmap.md" | grep -qi "remains read-only"; then
    fail "roadmap.md Phase 4 still says the dev scaffold remains read-only (stale)"
else
    pass "roadmap.md Phase 4 no longer contradicts the v1 implementation"
fi

# ---------------------------------------------------------------------
section "6. Full automated suite"
# ---------------------------------------------------------------------

if command -v lrh >/dev/null 2>&1; then
    LRH_BIN=lrh
elif [ -x /Users/centaur/anaconda3/bin/lrh ]; then
    LRH_BIN=/Users/centaur/anaconda3/bin/lrh
else
    LRH_BIN=""
fi

if [ -n "$LRH_BIN" ]; then
    LRH_OUT="$(cd "$REPO_ROOT" && "$LRH_BIN" validate 2>&1)"
    if echo "$LRH_OUT" | grep -q "0 error(s), 0 warning(s)"; then
        pass "lrh validate: 0 errors, 0 warnings"
    else
        fail "lrh validate reported issues: $LRH_OUT"
    fi
else
    skip "lrh validate (lrh not found)"
fi

BLACK_OUT="$(cd "$REPO_ROOT" && "$PYTHON_BIN" -m black --check src tests 2>&1)"
if [ $? -eq 0 ]; then
    pass "black --check: clean"
else
    fail "black --check reported issues: $BLACK_OUT"
fi

RUFF_OUT="$(cd "$REPO_ROOT" && "$PYTHON_BIN" -m ruff check src tests 2>&1)"
if [ $? -eq 0 ]; then
    pass "ruff check: clean"
else
    fail "ruff check reported issues: $RUFF_OUT"
fi

TEST_SUITE_OUT="$(cd "$REPO_ROOT" && PYTHONPATH="$REPO_ROOT/src:$REPO_ROOT/tests" "$PYTHON_BIN" -m unittest discover -s tests -p "*_test.py" 2>&1)"
if echo "$TEST_SUITE_OUT" | grep -q "^OK"; then
    RAN_LINE="$(echo "$TEST_SUITE_OUT" | grep "^Ran ")"
    pass "full test suite: OK ($RAN_LINE)"
else
    fail "full test suite did not report OK (tail: $(echo "$TEST_SUITE_OUT" | tail -15))"
fi

# ---------------------------------------------------------------------
section "Summary"
# ---------------------------------------------------------------------

echo "  Passed:  $PASS_COUNT"
echo "  Failed:  $FAIL_COUNT"
echo "  Skipped: $SKIP_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo
    echo "Failed checks:"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  - $check"
    done
    exit 1
fi

echo
echo "All checks passed."
exit 0
