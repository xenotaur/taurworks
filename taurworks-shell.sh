# Source this file from bash or zsh to enable Taurworks shell helpers.
#
# Usage:
#   source /path/to/taurworks-shell.sh
#   tw activate [PATH_OR_NAME]
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

_tw_activate() {
    local output
    local status
    local resolved_working_dir
    local working_dir_configured
    local working_dir_exists

    output=$(command taurworks project activate "$@" --print 2>&1)
    status=$?
    if [ "$status" -ne 0 ]; then
        printf '%s\n' "$output" >&2
        return "$status"
    fi

    working_dir_configured=$(printf '%s\n' "$output" | _tw_activation_field "working_dir_configured")
    working_dir_exists=$(printf '%s\n' "$output" | _tw_activation_field "working_dir_exists")
    resolved_working_dir=$(printf '%s\n' "$output" | _tw_activation_field "resolved_working_dir")

    if [ "$working_dir_configured" != "True" ]; then
        printf '%s\n' "tw activate: no configured working directory is available." >&2
        printf '%s\n' "$output" >&2
        return 1
    fi

    if [ "$resolved_working_dir" = "" ] || [ "$resolved_working_dir" = "none" ]; then
        printf '%s\n' "tw activate: Taurworks did not report a resolved working directory." >&2
        printf '%s\n' "$output" >&2
        return 1
    fi

    if [ "$working_dir_exists" != "True" ]; then
        printf '%s\n' "tw activate: resolved working directory does not exist: $resolved_working_dir" >&2
        printf '%s\n' "$output" >&2
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

    command taurworks "$@"
}
