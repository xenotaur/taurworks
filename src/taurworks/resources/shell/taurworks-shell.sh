# Source this file from bash or zsh to enable Taurworks shell helpers.
#
# Usage:
#   taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
#   source ~/.config/taurworks/taurworks-shell.sh
#   tw activate [PATH_OR_NAME]
#   tw activate [PATH_OR_NAME] --verbose
#
# The taurworks executable remains read-only for activation. This sourced
# function is the explicit layer that may mutate the current shell by running
# `cd` to the resolved project working directory.

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

_tw_activate() {
    local output
    local status
    local resolved_working_dir
    local working_dir_configured
    local working_dir_exists
    local path_or_name
    local verbose
    local target_label

    path_or_name=""
    verbose=0

    while [ "$#" -gt 0 ]; do
        case "$1" in
            --verbose|--debug)
                verbose=1
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
        if output=$(command taurworks project activate --print 2>&1); then
            status=0
        else
            status=$?
        fi
    else
        if output=$(command taurworks project activate "$path_or_name" --print 2>&1); then
            status=0
        else
            status=$?
        fi
    fi

    if [ "$status" -ne 0 ]; then
        if [ "$verbose" = "1" ]; then
            printf '%s\n' "$output" >&2
        else
            target_label=$(_tw_activation_target_label "$path_or_name")
            printf '%s\n' "tw activate: no configured working directory is available for $target_label." >&2
            _tw_activation_detail_command "$path_or_name"
        fi
        return "$status"
    fi

    working_dir_configured=$(printf '%s\n' "$output" | _tw_activation_field "working_dir_configured")
    working_dir_exists=$(printf '%s\n' "$output" | _tw_activation_field "working_dir_exists")
    resolved_working_dir=$(printf '%s\n' "$output" | _tw_activation_field "resolved_working_dir")

    if [ "$working_dir_configured" != "True" ]; then
        if [ "$verbose" = "1" ]; then
            printf '%s\n' "$output" >&2
        else
            target_label=$(_tw_activation_target_label "$path_or_name")
            printf '%s\n' "tw activate: no configured working directory is available for $target_label." >&2
            _tw_activation_detail_command "$path_or_name"
        fi
        return 1
    fi

    if [ "$resolved_working_dir" = "" ] || [ "$resolved_working_dir" = "none" ]; then
        if [ "$verbose" = "1" ]; then
            printf '%s\n' "$output" >&2
        else
            printf '%s\n' "tw activate: Taurworks did not report a resolved working directory." >&2
            _tw_activation_detail_command "$path_or_name"
        fi
        return 1
    fi

    if [ "$working_dir_exists" != "True" ]; then
        if [ "$verbose" = "1" ]; then
            printf '%s\n' "$output" >&2
        else
            printf '%s\n' "tw activate: resolved working directory does not exist: $resolved_working_dir" >&2
            _tw_activation_detail_command "$path_or_name"
        fi
        return 1
    fi

    if ! cd -- "$resolved_working_dir"; then
        printf '%s\n' "tw activate: failed to change directory to: $resolved_working_dir" >&2
        return 1
    fi

    printf '%s\n' "tw activate: changed directory to $resolved_working_dir"
}

tw() {
    if [ "$1" = "activate" ]; then
        shift
        _tw_activate "$@"
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
