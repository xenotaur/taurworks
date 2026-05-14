import importlib.resources

SHELL_HELPER_RESOURCE = "resources/shell/taurworks-shell.sh"


class ShellHelperResourceError(RuntimeError):
    """Raised when the packaged Taurworks shell helper cannot be read."""


def read_shell_helper_text() -> str:
    """Return the packaged sourceable Taurworks shell helper text."""
    resource = importlib.resources.files("taurworks").joinpath(SHELL_HELPER_RESOURCE)
    try:
        return resource.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ShellHelperResourceError(
            f"Packaged shell helper resource not found: {SHELL_HELPER_RESOURCE}"
        ) from exc
