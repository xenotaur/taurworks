# Source this file from bash or zsh to enable Taurworks shell helpers.
#
# Usage:
#   taurworks setup                          # one-step install of tw/tl (preferred)
#   taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
#   source ~/.config/taurworks/taurworks-shell.sh
#   tw activate [PATH_OR_NAME]
#   tw activate [PATH_OR_NAME] --verbose
#   tw activate [PATH_OR_NAME] --legacy      # source a legacy setup script once
#   tw activate [PATH_OR_NAME] --no-legacy   # never source, even if trusted
#   tw shell refresh                         # regenerate + re-source this file
#
# The taurworks executable remains read-only for activation. This sourced
# function is the explicit layer that may mutate the current shell by exporting
# validated activation variables and running `cd` to the resolved project working
# directory.
#
# Trust-gated legacy sourcing (`taurworks config legacy-sourcing enable` plus
# `taurworks project trust set NAME`) is off by default. While the Tier 1
# switch is off, none of the functions below run and behavior is unchanged.
#
# `tw shell refresh` fixes the "stale shell helper" problem: this file is a
# one-time snapshot from `taurworks shell print`, and sourcing it only reads
# it once, like `.bashrc`. It never auto-updates when the taurworks package
# changes, and an already-sourced shell keeps running whatever it last
# sourced, silently. `tw shell refresh` regenerates the file at its
# resolved location (TAURWORKS_SHELL_HELPER_PATH, else a valid absolute
# XDG_CONFIG_HOME, else ~/.config/taurworks/taurworks-shell.sh -- the same
# precedence `taurworks setup` uses) from the currently installed package
# and re-sources it into the current shell -- it cannot reach any other
# already-open shell (see project/design/shell_helper_refresh.md).

_tw_legacy_prompt_choice() {
    # Read one line of a user's response and normalize it to s/t/n/k
    # (source once / trust / decline / skip -- decline and skip currently
    # behave identically and neither is persisted). Split out from
    # _tw_offer_legacy_trust so it can be exercised directly with piped
    # stdin in tests, independent of the real TTY gate in _tw_activate.
    local raw
    read -r raw
    case "$raw" in
        [sS]*) printf 's\n' ;;
        [tT]*) printf 't\n' ;;
        [nN]*) printf 'n\n' ;;
        *) printf 'k\n' ;;
    esac
}

_tw_source_legacy_script() {
    local script_path
    script_path=$1
    if ! source "$script_path"; then
        printf '%s\n' "tw activate: legacy setup script exited with an error: $script_path" >&2
        return 1
    fi
    return 0
}

_tw_offer_legacy_trust() {
    # Interactive consent prompt for sourcing an untrusted (or edited-since-
    # trusted) legacy setup script. Only called when a real TTY was already
    # confirmed by the caller. project_root (an absolute path) is used for
    # the `taurworks legacy inspect`/`taurworks project trust set` calls
    # instead of project_name: by this point the shell has already cd'd
    # into the activated project, and a bare name re-resolved from that cwd
    # can mis-resolve (e.g. an unregistered, non-workspace project whose
    # name isn't findable as "current project" from its own directory).
    local script_path project_name project_root stale choice

    script_path=$1
    project_name=$2
    project_root=$3
    stale=$4

    # Re-check resolvability here (not just at the top of `tw()`): this
    # function is only reached after `_tw_activate` may have already run
    # `conda activate`, which can hide `taurworks` on $PATH even when it
    # was resolvable at the start of the `tw` invocation.
    if ! _tw_require_taurworks; then
        return 1
    fi

    if [ "$stale" = "True" ]; then
        printf '%s\n' "tw activate: the trusted legacy setup script for '$project_name' has changed since it was trusted:" >&2
    else
        printf '%s\n' "tw activate: an untrusted legacy setup script exists for '$project_name':" >&2
    fi
    command taurworks legacy inspect "$project_root" >&2
    printf '%s' "tw activate: [s]ource once, [t]rust and source, or anything else to skip this time? " >&2
    choice=$(_tw_legacy_prompt_choice)

    case "$choice" in
        s)
            _tw_source_legacy_script "$script_path"
            ;;
        t)
            if command taurworks project trust set "$project_root" >&2; then
                _tw_source_legacy_script "$script_path"
            else
                printf '%s\n' "tw activate: failed to record trust; not sourcing." >&2
            fi
            ;;
        *)
            printf '%s\n' "tw activate: skipped sourcing $script_path for this activation; run \`tw activate --legacy\` to source once, or \`taurworks project trust set $project_root\` to trust it." >&2
            ;;
    esac
}

_tw_activation_field() {
    # Extract the first stable Taurworks diagnostic line matching a key.
    # Expected input lines are formatted like: "- key: value".
    awk -v key="$1" '
        index($0, "- " key ": ") == 1 {
            sub("^- " key ": ", "")
            print
            exit
        }
    '
}

_tw_activation_detail_command() {
    local path_or_name

    path_or_name=$1
    if [ "$path_or_name" = "" ]; then
        printf '%s\n' 'Run `taurworks project activate --print` for details.' >&2
    else
        printf '%s\n' "Run \`taurworks project activate $path_or_name --print\` for details." >&2
    fi
}

_tw_activation_target_label() {
    if [ "$1" = "" ]; then
        printf '%s\n' "the current project"
    else
        printf '%s\n' "$1"
    fi
}

_tw_taurworks_executable_path() {
    # `command -v taurworks` alone doesn't distinguish a real executable on
    # $PATH from a shell function or alias of the same name: bash prints
    # just the bare name (with exit 0) for a function/alias match, but the
    # later `command taurworks ...` call sites use the `command` builtin,
    # which bypasses function/alias lookup entirely -- so a function-only
    # match would pass this check yet still hit a bare "command not found"
    # at the real call site, exactly the failure this guard exists to
    # replace. Only trust an absolute path that is actually a regular,
    # executable file.
    local resolved
    resolved=$(command -v taurworks 2>/dev/null)
    case "$resolved" in
        /*)
            if [ -f "$resolved" ] && [ -x "$resolved" ]; then
                printf '%s\n' "$resolved"
                return 0
            fi
            ;;
    esac
    return 1
}

_tw_require_taurworks() {
    # Guards every `command taurworks ...` call site in this file against
    # PATH loss (most commonly a `conda activate` into an environment that
    # lacks the package). Called once up front in `tw()` -- covering `tw
    # activate`'s own pre-Conda-activation calls, `tw shell refresh`, `tw
    # help`, and the general fallthrough, all via that single check -- and
    # again in `_tw_offer_legacy_trust`, which can only be reached *after*
    # `_tw_activate` has already run `conda activate`, so PATH may have
    # changed since `tw()`'s check ran. Two call sites, at most, per `tw`
    # invocation; never re-checks within a single function body where PATH
    # cannot have changed since the top of that function.
    if _tw_taurworks_executable_path >/dev/null; then
        return 0
    fi
    printf '%s\n' "tw: \`taurworks\` is not on \$PATH." >&2
    if [ -n "${CONDA_DEFAULT_ENV-}" ]; then
        printf '%s\n' "tw: the active Conda environment ('$CONDA_DEFAULT_ENV') likely does not have taurworks installed." >&2
        printf '%s\n' "tw: switch back to the environment where taurworks is installed, or install it here (e.g. \`scripts/install\` from a checkout, or \`pipx install <path-to-checkout>\` -- taurworks is not published to PyPI), then retry. \`tl\` remains usable in the meantime -- it never depends on taurworks being resolvable." >&2
    else
        printf '%s\n' "tw: check \`which taurworks\` / \`pipx list\` and confirm its install location is on \$PATH, then retry." >&2
    fi
    return 1
}

_tw_activate() {
    local output
    local status
    local resolved_working_dir
    local working_dir_configured
    local working_dir_exists
    local guidance
    local activation_message
    local activation_message_configured
    local activation_export_count
    local activation_export_commands
    local environment_configured
    local environment_type
    local environment_name
    local project_name
    local project_root
    local legacy_setup_exists
    local legacy_setup_path
    local legacy_sourcing_enabled
    local legacy_trusted
    local legacy_trust_stale
    local path_or_name
    local verbose
    local legacy_once
    local no_legacy
    local target_label

    path_or_name=""
    verbose=0
    legacy_once=0
    no_legacy=0

    while [ "$#" -gt 0 ]; do
        case "$1" in
            --verbose|--debug)
                verbose=1
                ;;
            --legacy)
                legacy_once=1
                ;;
            --no-legacy)
                no_legacy=1
                ;;
            --)
                shift
                if [ "$#" -gt 0 ] && [ "$path_or_name" = "" ]; then
                    path_or_name=$1
                    shift
                fi
                if [ "$#" -gt 0 ]; then
                    printf '%s\n' "tw activate: unexpected argument: $1" >&2
                    return 2
                fi
                break
                ;;
            *)
                if [ "$path_or_name" = "" ]; then
                    path_or_name=$1
                else
                    printf '%s\n' "tw activate: unexpected argument: $1" >&2
                    return 2
                fi
                ;;
        esac
        shift
    done

    if [ "$path_or_name" = "" ]; then
        if output=$(command taurworks project activate --shell 2>&1); then
            status=0
        else
            status=$?
        fi
    else
        if output=$(command taurworks project activate "$path_or_name" --shell 2>&1); then
            status=0
        else
            status=$?
        fi
    fi

    if [ "$status" -ne 0 ]; then
        if [ "$verbose" = "1" ]; then
            printf '%s\n' "$output" >&2
        else
            guidance=$(printf '%s\n' "$output" | _tw_activation_field "guidance")
            target_label=$(_tw_activation_target_label "$path_or_name")
            printf '%s\n' "tw activate: activation failed for $target_label." >&2
            if [ "$guidance" != "" ]; then
                printf '%s\n' "tw activate: $guidance" >&2
            else
                printf '%s\n' "$output" >&2
            fi
            _tw_activation_detail_command "$path_or_name"
        fi
        return "$status"
    fi

    local TAURWORKS_ACTIVATION_WORKING_DIR
    local TAURWORKS_ACTIVATION_WORKING_DIR_EXISTS
    local TAURWORKS_ACTIVATION_WORKING_DIR_CONFIGURED
    local TAURWORKS_ACTIVATION_GUIDANCE
    local TAURWORKS_ACTIVATION_MESSAGE
    local TAURWORKS_ACTIVATION_MESSAGE_CONFIGURED
    local TAURWORKS_ACTIVATION_EXPORT_COUNT
    local TAURWORKS_ACTIVATION_EXPORT_COMMANDS
    local TAURWORKS_ACTIVATION_ENVIRONMENT_CONFIGURED
    local TAURWORKS_ACTIVATION_ENVIRONMENT_TYPE
    local TAURWORKS_ACTIVATION_ENVIRONMENT_NAME
    local TAURWORKS_ACTIVATION_PROJECT_NAME
    local TAURWORKS_ACTIVATION_PROJECT_ROOT
    local TAURWORKS_ACTIVATION_LEGACY_SETUP_EXISTS
    local TAURWORKS_ACTIVATION_LEGACY_SETUP_PATH
    local TAURWORKS_ACTIVATION_LEGACY_SOURCING_ENABLED
    local TAURWORKS_ACTIVATION_LEGACY_TRUSTED
    local TAURWORKS_ACTIVATION_LEGACY_TRUST_STALE

    if ! eval "$output"; then
        printf '%s\n' "tw activate: failed to read Taurworks activation shell data." >&2
        return 1
    fi

    working_dir_configured=$TAURWORKS_ACTIVATION_WORKING_DIR_CONFIGURED
    working_dir_exists=$TAURWORKS_ACTIVATION_WORKING_DIR_EXISTS
    resolved_working_dir=$TAURWORKS_ACTIVATION_WORKING_DIR
    guidance=$TAURWORKS_ACTIVATION_GUIDANCE
    activation_message=$TAURWORKS_ACTIVATION_MESSAGE
    activation_message_configured=$TAURWORKS_ACTIVATION_MESSAGE_CONFIGURED
    activation_export_count=$TAURWORKS_ACTIVATION_EXPORT_COUNT
    activation_export_commands=$TAURWORKS_ACTIVATION_EXPORT_COMMANDS
    environment_configured=$TAURWORKS_ACTIVATION_ENVIRONMENT_CONFIGURED
    environment_type=$TAURWORKS_ACTIVATION_ENVIRONMENT_TYPE
    environment_name=$TAURWORKS_ACTIVATION_ENVIRONMENT_NAME
    project_name=$TAURWORKS_ACTIVATION_PROJECT_NAME
    project_root=$TAURWORKS_ACTIVATION_PROJECT_ROOT
    legacy_setup_exists=$TAURWORKS_ACTIVATION_LEGACY_SETUP_EXISTS
    legacy_setup_path=$TAURWORKS_ACTIVATION_LEGACY_SETUP_PATH
    legacy_sourcing_enabled=$TAURWORKS_ACTIVATION_LEGACY_SOURCING_ENABLED
    legacy_trusted=$TAURWORKS_ACTIVATION_LEGACY_TRUSTED
    legacy_trust_stale=$TAURWORKS_ACTIVATION_LEGACY_TRUST_STALE

    if [ "$resolved_working_dir" = "" ] || [ "$resolved_working_dir" = "none" ]; then
        printf '%s\n' "tw activate: Taurworks did not report a resolved working directory." >&2
        _tw_activation_detail_command "$path_or_name"
        return 1
    fi

    if [ "$working_dir_exists" != "True" ]; then
        printf '%s\n' "tw activate: resolved working directory does not exist: $resolved_working_dir" >&2
        _tw_activation_detail_command "$path_or_name"
        return 1
    fi

    if [ "$environment_configured" = "True" ]; then
        if [ "$environment_type" != "conda" ]; then
            printf '%s\n' "tw activate: unsupported activation environment type: $environment_type" >&2
            return 1
        fi
        if ! type conda >/dev/null 2>&1; then
            printf '%s\n' "tw activate: conda activation is unavailable in this shell; configure conda activate before using Taurworks Conda activation." >&2
            return 1
        fi
        if ! conda activate "$environment_name"; then
            printf '%s\n' "tw activate: failed to activate Conda environment: $environment_name" >&2
            return 1
        fi
    fi

    if [ "$activation_export_commands" != "" ]; then
        if ! eval "$activation_export_commands"; then
            printf '%s\n' "tw activate: failed to apply Taurworks activation exports." >&2
            return 1
        fi
    fi

    if ! cd -- "$resolved_working_dir"; then
        printf '%s\n' "tw activate: failed to change directory to: $resolved_working_dir" >&2
        return 1
    fi

    if [ "$working_dir_configured" != "True" ] && [ "$guidance" != "" ]; then
        printf '%s\n' "tw activate: warning: $guidance" >&2
    elif [ "$environment_configured" != "True" ] && [ "$guidance" != "" ]; then
        printf '%s\n' "tw activate: note: $guidance" >&2
    fi
    if [ "$activation_export_count" != "" ] && [ "$activation_export_count" != "0" ]; then
        printf '%s\n' "tw activate: exported $activation_export_count variable(s)"
    fi
    printf '%s\n' "tw activate: changed directory to $resolved_working_dir"
    if [ "$activation_message_configured" = "True" ]; then
        printf '%s\n' "$activation_message"
    fi

    if [ "$legacy_setup_exists" = "True" ] && [ "$no_legacy" != "1" ]; then
        if [ "$legacy_sourcing_enabled" = "True" ] && [ "$legacy_trusted" = "True" ]; then
            _tw_source_legacy_script "$legacy_setup_path"
        elif [ "$legacy_sourcing_enabled" = "True" ] && [ "$legacy_once" = "1" ]; then
            _tw_source_legacy_script "$legacy_setup_path"
        elif [ "$legacy_sourcing_enabled" = "True" ] && [ -t 0 ] && [ -t 1 ]; then
            _tw_offer_legacy_trust "$legacy_setup_path" "$project_name" "$project_root" "$legacy_trust_stale"
        elif [ "$legacy_sourcing_enabled" = "True" ]; then
            printf '%s\n' "tw activate: note: an untrusted legacy setup script exists at $legacy_setup_path; re-run with --legacy to source it once, or run \`taurworks project trust set $project_root\` to trust it." >&2
        elif [ "$legacy_once" = "1" ]; then
            printf '%s\n' "tw activate: --legacy requires legacy sourcing to be enabled; run \`taurworks config legacy-sourcing enable\` first." >&2
        fi
    fi
}

_tw_shell_refresh() {
    local target_path
    local parent_dir
    local tmp_path
    local link_target

    if [ "$#" -gt 0 ]; then
        printf '%s\n' "tw shell refresh: unexpected argument: $1" >&2
        return 2
    fi

    # Resolution precedence matches `taurworks setup`
    # (src/taurworks/setup_command.py): TAURWORKS_SHELL_HELPER_PATH first,
    # then a valid absolute XDG_CONFIG_HOME, then the ~/.config fallback --
    # so a refresh always targets the same file `taurworks setup` wrote.
    # Uses the `${VAR-}` unset-safe expansion form throughout (not
    # `${VAR:-...}` alone) so this stays safe to source under `set -u`/
    # nounset even when the caller never exported these optional variables
    # at all, not merely left them empty. A relative
    # TAURWORKS_SHELL_HELPER_PATH is canonicalized against the current
    # directory (matching setup_command.py's equivalent CWD-relative
    # handling) rather than used as-is, so both always agree on the same
    # absolute file.
    if [ -n "${TAURWORKS_SHELL_HELPER_PATH-}" ]; then
        case "$TAURWORKS_SHELL_HELPER_PATH" in
            /*) target_path="$TAURWORKS_SHELL_HELPER_PATH" ;;
            *) target_path="$(pwd)/$TAURWORKS_SHELL_HELPER_PATH" ;;
        esac
    else
        case "${XDG_CONFIG_HOME-}" in
            /*) target_path="$XDG_CONFIG_HOME/taurworks/taurworks-shell.sh" ;;
            *) target_path="$HOME/.config/taurworks/taurworks-shell.sh" ;;
        esac
    fi

    # If the configured path is a symlink (e.g. into a dotfiles checkout),
    # write through to its target instead of replacing the link itself --
    # `mv` onto an existing symlink replaces the link, not what it points
    # to. Only one hop is resolved; that covers the common case and avoids
    # depending on non-portable `readlink -f`/`realpath` flags.
    if [ -L "$target_path" ]; then
        link_target=$(readlink -- "$target_path")
        case "$link_target" in
            /*) target_path="$link_target" ;;
            *) target_path="$(dirname -- "$target_path")/$link_target" ;;
        esac
    fi

    parent_dir=$(dirname -- "$target_path")

    if ! mkdir -p -- "$parent_dir"; then
        printf '%s\n' "tw shell refresh: failed to create directory: $parent_dir" >&2
        return 1
    fi

    tmp_path="$target_path.tmp.$$"
    if ! command taurworks shell print > "$tmp_path"; then
        printf '%s\n' "tw shell refresh: \`taurworks shell print\` failed; left $target_path unchanged." >&2
        rm -f -- "$tmp_path"
        return 1
    fi

    if ! mv -f -- "$tmp_path" "$target_path"; then
        printf '%s\n' "tw shell refresh: failed to install refreshed helper at: $target_path" >&2
        rm -f -- "$tmp_path"
        return 1
    fi

    if ! source "$target_path"; then
        printf '%s\n' "tw shell refresh: wrote $target_path but failed to source it." >&2
        return 1
    fi

    printf '%s\n' "tw shell refresh: refreshed and re-sourced $target_path"
}

tw() {
    # Single up-front resolvability check, covering every call site below
    # except _tw_offer_legacy_trust's (which re-checks itself -- see
    # _tw_require_taurworks's comment -- since it can only run after
    # _tw_activate may have already changed PATH via `conda activate`).
    if ! _tw_require_taurworks; then
        return 1
    fi

    if [ "$1" = "activate" ]; then
        shift
        _tw_activate "$@"
        return $?
    fi

    if [ "$1" = "shell" ] && [ "${2-}" = "refresh" ]; then
        shift 2
        _tw_shell_refresh "$@"
        return $?
    fi

    if [ "$1" = "help" ]; then
        shift
        if [ "$#" -eq 0 ]; then
            command taurworks --help
        else
            command taurworks "$@" --help
        fi
        return $?
    fi

    command taurworks "$@"
}
