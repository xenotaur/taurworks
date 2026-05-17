# Source this file from bash or zsh to enable Taurworks shell helpers.
#
# Usage:
#   taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
#   source ~/.config/taurworks/taurworks-shell.sh
#   tw activate [PATH_OR_NAME]
#   tw activate [PATH_OR_NAME] --verbose
#
# The taurworks executable remains read-only for activation. This sourced
# function is the explicit layer that may mutate the current shell by exporting
# validated activation variables and running `cd` to the resolved project working
# directory.

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
    local guidance
    local activation_message
    local activation_message_configured
    local activation_export_count
    local activation_export_commands
    local environment_configured
    local environment_type
    local environment_name
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
    fi
    if [ "$activation_export_count" != "" ] && [ "$activation_export_count" != "0" ]; then
        printf '%s\n' "tw activate: exported $activation_export_count variable(s)"
    fi
    printf '%s\n' "tw activate: changed directory to $resolved_working_dir"
    if [ "$activation_message_configured" = "True" ]; then
        printf '%s\n' "$activation_message"
    fi
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
