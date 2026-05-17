import argparse
import sys

from taurworks import dev
from taurworks import global_config
from taurworks import manager
from taurworks import project_registry
from taurworks import project_resolution
from taurworks import shell_resources


def _handle_config_command(args):
    """Handle `taurworks config ...` commands."""
    if args.config_command == "where":
        diagnostics = global_config.gather_config_where_diagnostics()
        print(global_config.format_config_where_output(diagnostics))
        return

    args.config_parser.print_help()


def _handle_workspace_command(args):
    """Handle `taurworks workspace ...` commands."""
    if args.workspace_command == "show":
        diagnostics = global_config.gather_workspace_show_diagnostics()
        print(global_config.format_workspace_show_output(diagnostics))
        return

    if args.workspace_command == "set":
        diagnostics = global_config.gather_workspace_set_diagnostics(args.path)
        print(global_config.format_workspace_set_output(diagnostics))
        if not diagnostics["ok"]:
            raise SystemExit(1)
        return

    args.workspace_parser.print_help()


def _emit_project_path(path_or_name: str, path_kind: str, command_name: str) -> None:
    """Emit one resolved project path to stdout or diagnostics to stderr."""
    diagnostics = project_resolution.gather_project_path_diagnostics(
        path_or_name,
        path_kind,
    )
    if diagnostics["ok"]:
        print(diagnostics["path"])
        return

    print(
        project_resolution.format_project_path_error(diagnostics, command_name),
        file=sys.stderr,
    )
    raise SystemExit(1)


def _handle_project_command(args):
    """Handle scaffolded `taurworks project ...` commands."""
    if args.project_command == "root":
        _emit_project_path(args.path_or_name, "root", "taurworks project root")
        return

    if args.project_command == "working":
        _emit_project_path(args.path_or_name, "working", "taurworks project working")
        return

    if args.project_command == "where":
        diagnostics = project_resolution.gather_project_where_diagnostics()
        print(project_resolution.format_project_where_output(diagnostics))
        return

    if args.project_command == "list":
        diagnostics = project_resolution.gather_project_list_diagnostics()
        print(project_resolution.format_project_list_output(diagnostics))
        return

    if args.project_command == "register":
        diagnostics = project_registry.gather_project_register_diagnostics(
            args.name,
            args.path,
            force=args.force,
            allow_missing=args.allow_missing,
        )
        print(project_registry.format_project_register_output(diagnostics))
        if not diagnostics["ok"]:
            raise SystemExit(1)
        return

    if args.project_command == "unregister":
        diagnostics = project_registry.gather_project_unregister_diagnostics(args.name)
        print(project_registry.format_project_unregister_output(diagnostics))
        if not diagnostics["ok"]:
            raise SystemExit(1)
        return

    if args.project_command == "registry":
        if args.registry_command == "list":
            diagnostics = project_registry.gather_project_registry_list_diagnostics()
            print(project_registry.format_project_registry_list_output(diagnostics))
            if not diagnostics["ok"]:
                raise SystemExit(1)
            return

    if args.project_command == "refresh":
        diagnostics = project_resolution.gather_project_refresh_diagnostics(
            args.path_or_name
        )
        print(project_resolution.format_project_refresh_output(diagnostics))
        return
    if args.project_command == "init":
        diagnostics = project_resolution.gather_project_init_diagnostics(
            args.path_or_name,
            args.working_dir,
            create_working_dir=args.create_working_dir,
        )
        print(project_resolution.format_project_init_output(diagnostics))
        if not diagnostics["ok"]:
            raise SystemExit(1)
        return
    if args.project_command == "working-dir":
        if args.working_dir_command == "show":
            diagnostics = (
                project_resolution.gather_project_working_dir_show_diagnostics(
                    args.path_or_name
                )
            )
            print(
                project_resolution.format_project_working_dir_show_output(diagnostics)
            )
            if not diagnostics["ok"]:
                raise SystemExit(1)
            return
        if args.working_dir_command == "set":
            diagnostics = project_resolution.gather_project_working_dir_set_diagnostics(
                args.dir
            )
            print(project_resolution.format_project_working_dir_set_output(diagnostics))
            if not diagnostics["ok"]:
                raise SystemExit(1)
            return
    if args.project_command == "create":
        diagnostics = project_resolution.gather_project_create_diagnostics(
            args.path_or_name,
            args.working_dir,
            create_working_dir=args.create_working_dir,
            nested=args.nested,
            local=args.local,
            explicit_path=args.path,
        )
        print(project_resolution.format_project_create_output(diagnostics))
        if not diagnostics["ok"]:
            raise SystemExit(1)
        return
    if args.project_command == "activate":
        diagnostics = project_resolution.gather_project_activate_print_diagnostics(
            args.path_or_name
        )
        print(project_resolution.format_project_activate_print_output(diagnostics))
        if not diagnostics["ok"]:
            raise SystemExit(1)
        return

    args.project_parser.print_help()


def _handle_dev_command(args):
    """Handle minimal read-only `taurworks dev ...` commands."""
    if args.dev_command == "where":
        diagnostics = dev.gather_dev_where_diagnostics()
        print(dev.format_dev_where_output(diagnostics))
        return

    if args.dev_command == "status":
        diagnostics = dev.gather_dev_status_diagnostics()
        print(dev.format_dev_status_output(diagnostics))
        return

    args.dev_parser.print_help()


def _handle_shell_command(args):
    """Handle `taurworks shell ...` commands."""
    if args.shell_command == "print":
        try:
            sys.stdout.write(shell_resources.read_shell_helper_text())
        except shell_resources.ShellHelperResourceError as exc:
            print(f"taurworks shell print: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return

    args.shell_parser.print_help()


def main():
    parser = argparse.ArgumentParser(
        prog="taurworks", description="Manage taurworks projects."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # List projects
    parser_list = subparsers.add_parser(
        "projects", help="List available project environments."
    )
    parser_list.add_argument(
        "-l",
        "--details",
        action="store_true",
        help="Show detailed project information.",
    )

    # Create a project
    parser_create = subparsers.add_parser("create", help="Create a new project.")
    parser_create.add_argument(
        "project_name", type=str, help="Name of the project to create."
    )
    parser_create.add_argument(
        "--python",
        type=str,
        default="3.11",
        help="Specify Python version (default: 3.11).",
    )
    parser_create.add_argument(
        "--packages", type=str, help="Comma-separated list of additional packages."
    )
    parser_create.add_argument(
        "--file", type=str, help="Path to a Conda environment YAML file."
    )

    # Refresh a project
    parser_refresh = subparsers.add_parser(
        "refresh", help="Ensure a project is correctly set up."
    )
    parser_refresh.add_argument(
        "project_name", type=str, help="Name of the project to refresh."
    )
    parser_refresh.add_argument(
        "--python",
        type=str,
        default="3.11",
        help="Specify Python version (default: 3.11).",
    )
    parser_refresh.add_argument(
        "--packages", type=str, help="Comma-separated list of additional packages."
    )
    parser_refresh.add_argument(
        "--file", type=str, help="Path to a Conda environment YAML file."
    )

    # Activate a project
    parser_activate = subparsers.add_parser(
        "activate", help="Activate an existing project."
    )
    parser_activate.add_argument(
        "project_name", type=str, help="Name of the project to activate."
    )

    parser_root = subparsers.add_parser(
        "root",
        help="Print a project's registered root directory for shell composition.",
        description=(
            "Resolve PROJECT by name or path and print exactly one absolute "
            "project root path to stdout. Diagnostics are written to stderr on failure."
        ),
    )
    parser_root.add_argument(
        "path_or_name", metavar="PROJECT", help="Project name or path."
    )

    parser_working = subparsers.add_parser(
        "working",
        help="Print a project's preferred working directory for shell composition.",
        description=(
            "Resolve PROJECT by name or path and print exactly one absolute "
            "preferred working directory path to stdout. Diagnostics are written to stderr on failure."
        ),
    )
    parser_working.add_argument(
        "path_or_name",
        metavar="PROJECT",
        help="Project name or path.",
    )

    # `config` namespace
    parser_config = subparsers.add_parser(
        "config",
        help="User-global Taurworks configuration commands.",
        description=(
            "Inspect user-global Taurworks configuration. Read-only commands do "
            "not create config files."
        ),
    )
    config_subparsers = parser_config.add_subparsers(
        dest="config_command",
        required=False,
    )
    parser_config_where = config_subparsers.add_parser(
        "where",
        help="Show the resolved global config path (read-only).",
        description=(
            "Report the XDG-style global config path, whether it exists, and "
            "that no mutation is performed."
        ),
    )
    parser_config_where.set_defaults(config_parser=parser_config)
    parser_config.set_defaults(config_parser=parser_config)

    # `workspace` namespace
    parser_workspace = subparsers.add_parser(
        "workspace",
        help="User-global workspace root commands.",
        description=(
            "Show or set the user-global workspace root in the Taurworks "
            "XDG-style global config."
        ),
    )
    workspace_subparsers = parser_workspace.add_subparsers(
        dest="workspace_command",
        required=False,
    )
    parser_workspace_show = workspace_subparsers.add_parser(
        "show",
        help="Show configured or inferred workspace root (read-only).",
        description=(
            "Read global config if present and display a configured workspace "
            "root, or a clearly labeled inferred ~/Workspace when available."
        ),
    )
    parser_workspace_show.set_defaults(workspace_parser=parser_workspace)
    parser_workspace_set = workspace_subparsers.add_parser(
        "set",
        help="Set the configured workspace root in global config.",
        description=(
            "Write the workspace root to the XDG-style global config. The path "
            "must already be an existing directory."
        ),
    )
    parser_workspace_set.add_argument(
        "path",
        help="Existing workspace directory to store as [workspace].root.",
    )
    parser_workspace_set.set_defaults(workspace_parser=parser_workspace)
    parser_workspace.set_defaults(workspace_parser=parser_workspace)

    # `project` namespace
    parser_project = subparsers.add_parser(
        "project",
        help="Project discovery and safe lifecycle commands.",
        description=(
            "Project namespace for implemented discovery diagnostics and safe "
            "metadata lifecycle commands."
        ),
    )
    project_subparsers = parser_project.add_subparsers(
        dest="project_command",
        required=False,
    )

    parser_project_root = project_subparsers.add_parser(
        "root",
        help="Print a project's registered root directory.",
        description=(
            "Resolve PROJECT by name or path and print exactly one absolute "
            "project root path to stdout for shell composition. Diagnostics are written to stderr "
            "on failure."
        ),
    )
    parser_project_root.add_argument(
        "path_or_name",
        metavar="PROJECT",
        help="Project name or path.",
    )
    parser_project_root.set_defaults(project_parser=parser_project)

    parser_project_working = project_subparsers.add_parser(
        "working",
        help="Print a project's preferred working directory.",
        description=(
            "Resolve PROJECT by name or path and print exactly one absolute "
            "preferred working directory path to stdout for shell composition. Diagnostics are "
            "written to stderr on failure."
        ),
    )
    parser_project_working.add_argument(
        "path_or_name",
        metavar="PROJECT",
        help="Project name or path.",
    )
    parser_project_working.set_defaults(project_parser=parser_project)

    parser_project_where = project_subparsers.add_parser(
        "where",
        help="Show project/config/discovery resolution diagnostics (read-only).",
        description=(
            "Report current project/config/discovery resolution in a read-only "
            "diagnostic format."
        ),
    )
    parser_project_where.set_defaults(project_parser=parser_project)

    parser_project_list = project_subparsers.add_parser(
        "list",
        help="List discoverable Taurworks projects (read-only).",
        description=("List discoverable Taurworks projects in a read-only way."),
    )
    parser_project_list.set_defaults(project_parser=parser_project)

    parser_project_register = project_subparsers.add_parser(
        "register",
        help="Register an existing project root in global config.",
        description=(
            "Register a project by name under the XDG-style global [projects] "
            "registry. Registration does not modify project-local files."
        ),
    )
    parser_project_register.add_argument(
        "name",
        help="Registry name to store under [projects.NAME].",
    )
    parser_project_register.add_argument(
        "path",
        help="Project root path to normalize and store.",
    )
    parser_project_register.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing registry entry with the same name.",
    )
    parser_project_register.add_argument(
        "--allow-missing",
        action="store_true",
        help=(
            "Allow registering a path that does not currently exist. Existing "
            "paths must still be directories."
        ),
    )
    parser_project_register.set_defaults(project_parser=parser_project)

    parser_project_unregister = project_subparsers.add_parser(
        "unregister",
        help="Remove a project from the global registry without deleting files.",
        description=(
            "Remove a [projects.NAME] entry from global config. This command "
            "does not delete project-local files or metadata."
        ),
    )
    parser_project_unregister.add_argument(
        "name",
        help="Registry name to remove from global config.",
    )
    parser_project_unregister.set_defaults(project_parser=parser_project)

    parser_project_registry = project_subparsers.add_parser(
        "registry",
        help="Inspect the global project registry.",
        description=(
            "Inspect globally registered projects without mutating config or "
            "project-local files."
        ),
    )
    registry_subparsers = parser_project_registry.add_subparsers(
        dest="registry_command",
        required=True,
    )
    parser_project_registry_list = registry_subparsers.add_parser(
        "list",
        help="List registered projects with path/config existence and collisions.",
        description=(
            "List [projects.NAME] entries from global config, including root "
            "paths, existence flags, project-local config flags, and visible "
            "workspace child name collisions."
        ),
    )
    parser_project_registry_list.set_defaults(project_parser=parser_project)

    parser_project_refresh = project_subparsers.add_parser(
        "refresh",
        help=(
            "Safely create missing Taurworks project scaffolding "
            "without overwriting existing files."
        ),
        description=(
            "Repair/initialize minimal Taurworks-owned metadata in a safe, "
            "idempotent way."
        ),
    )
    parser_project_refresh.add_argument(
        "path_or_name",
        nargs="?",
        help=(
            "Optional project path or name. Defaults to current working "
            "directory when omitted."
        ),
    )
    parser_project_refresh.set_defaults(project_parser=parser_project)

    parser_project_init = project_subparsers.add_parser(
        "init",
        help=("Initialize an existing/current directory as a Taurworks project root."),
        description=(
            "Initialize an existing/current directory with safe, idempotent "
            "Taurworks metadata. Missing project roots are not created; use "
            "project create for new roots."
        ),
    )
    parser_project_init.add_argument(
        "path_or_name",
        nargs="?",
        help=(
            "Optional existing project root path. Defaults to current working "
            "directory when omitted."
        ),
    )
    parser_project_init.add_argument(
        "--working-dir",
        help=(
            "Optional project-root-relative default working directory to record. "
            "The directory must already exist unless --create-working-dir is supplied."
        ),
    )
    parser_project_init.add_argument(
        "--create-working-dir",
        action="store_true",
        help=(
            "Create a missing --working-dir directory after validating that it "
            "stays inside the project root."
        ),
    )
    parser_project_init.set_defaults(project_parser=parser_project)

    parser_project_working_dir = project_subparsers.add_parser(
        "working-dir",
        help="Show or set the project default working directory metadata.",
        description=(
            "Read or update project-local paths.working_dir metadata. The "
            "working directory is stored relative to the project root."
        ),
    )
    working_dir_subparsers = parser_project_working_dir.add_subparsers(
        dest="working_dir_command",
        required=True,
    )

    parser_project_working_dir_show = working_dir_subparsers.add_parser(
        "show",
        help="Show the configured project working directory.",
        description=(
            "Resolve the current Taurworks project root and show configured "
            "paths.working_dir metadata when present."
        ),
    )
    parser_project_working_dir_show.add_argument(
        "path_or_name",
        nargs="?",
        help=(
            "Optional project path or name. Defaults to the current project "
            "when run inside Taurworks metadata."
        ),
    )
    parser_project_working_dir_show.set_defaults(project_parser=parser_project)

    parser_project_working_dir_set = working_dir_subparsers.add_parser(
        "set",
        help="Set the configured project working directory.",
        description=(
            "Set paths.working_dir to an existing directory inside the project "
            "root. DIR is resolved from the current directory and stored "
            "relative to the project root. When DIR is omitted, the current "
            "directory is used."
        ),
    )
    parser_project_working_dir_set.add_argument(
        "dir",
        nargs="?",
        help="Optional existing directory to store relative to the project root.",
    )
    parser_project_working_dir_set.set_defaults(project_parser=parser_project)

    parser_project_create = project_subparsers.add_parser(
        "create",
        help=(
            "Create a new project root, then safely initialize Taurworks "
            "metadata without overwriting files."
        ),
        description=(
            "Create a new project root directory when needed, then delegate "
            "to the same safe, idempotent Taurworks metadata initialization "
            "used by project init for existing/current roots. Bare NAME targets use "
            "the configured "
            "workspace root by default. Use --local for cwd-relative creation "
            "or --path PATH for explicit path creation."
        ),
    )
    parser_project_create.add_argument(
        "path_or_name",
        nargs="?",
        help=(
            "Optional project name or explicit path-like target. Bare NAME "
            "creates under the configured workspace root unless --local or "
            "--path is supplied. Omitting NAME remains a compatibility alias "
            "for current-directory initialization."
        ),
    )
    target_group = parser_project_create.add_mutually_exclusive_group()
    target_group.add_argument(
        "--local",
        action="store_true",
        help="Create bare NAME under the current working directory.",
    )
    target_group.add_argument(
        "--path",
        help=(
            "Explicit project root path to create. When NAME is also supplied, "
            "PATH's basename must match NAME so NAME is not ignored."
        ),
    )
    parser_project_create.add_argument(
        "--working-dir",
        help=(
            "Optional project-root-relative default working directory to record. "
            "Missing directories are recorded without being created unless "
            "--create-working-dir is supplied."
        ),
    )
    parser_project_create.add_argument(
        "--create-working-dir",
        action="store_true",
        help=(
            "Create a missing --working-dir directory after validating that it "
            "stays inside the new project root."
        ),
    )
    parser_project_create.add_argument(
        "--nested",
        action="store_true",
        help=(
            "Allow intentional nested same-name project creation when the current "
            "project or current directory already has NAME."
        ),
    )
    parser_project_create.set_defaults(project_parser=parser_project)

    parser_project_activate = project_subparsers.add_parser(
        "activate",
        help=(
            "Resolve a project and print read-only shell activation guidance "
            "without mutating the shell."
        ),
        description=(
            "Resolve a project and print activation instructions. This command "
            "is read-only and does not source scripts, activate environments, "
            "or change the current shell."
        ),
    )
    parser_project_activate.add_argument(
        "path_or_name",
        nargs="?",
        help=(
            "Optional project path or name. Defaults to the current project "
            "when run inside Taurworks metadata."
        ),
    )
    parser_project_activate.add_argument(
        "--print",
        dest="print_only",
        action="store_true",
        help="Print activation guidance (required in this non-mutating slice).",
    )
    parser_project_activate.set_defaults(project_parser=parser_project)

    parser_project.set_defaults(project_parser=parser_project)

    # `dev` namespace
    parser_dev = subparsers.add_parser(
        "dev",
        help="Repository/developer workflow commands and diagnostics.",
        description=(
            "Repository/developer workflow namespace. This scaffold is minimal: "
            "it currently provides read-only diagnostics and does not run "
            "workflow automation."
        ),
    )
    dev_subparsers = parser_dev.add_subparsers(
        dest="dev_command",
        required=False,
    )

    parser_dev_where = dev_subparsers.add_parser(
        "where",
        help="Show repository/workspace diagnostics (read-only).",
        description=(
            "Report current repository/developer workspace context without "
            "changing files, shell state, or environments."
        ),
    )
    parser_dev_where.set_defaults(dev_parser=parser_dev)

    parser_dev_status = dev_subparsers.add_parser(
        "status",
        help="Show a minimal repository/workspace status summary (read-only).",
        description=(
            "Report a small read-only developer workspace summary. Detailed "
            "VCS and workflow automation are future work and no git commands "
            "are run."
        ),
    )
    parser_dev_status.set_defaults(dev_parser=parser_dev)
    parser_dev.set_defaults(dev_parser=parser_dev)

    # `shell` namespace
    parser_shell = subparsers.add_parser(
        "shell",
        help="Print sourceable Taurworks shell helper integration.",
        description=(
            "Shell helper commands for explicit, user-sourced shell integration. "
            "These commands do not edit shell startup files."
        ),
    )
    shell_subparsers = parser_shell.add_subparsers(
        dest="shell_command",
        required=False,
    )

    parser_shell_print = shell_subparsers.add_parser(
        "print",
        help="Print the packaged sourceable Taurworks shell helper.",
        description=(
            "Print the packaged Taurworks shell helper to stdout so it can be "
            "reviewed, redirected, or sourced manually."
        ),
    )
    parser_shell_print.set_defaults(shell_parser=parser_shell)
    parser_shell.set_defaults(shell_parser=parser_shell)

    args = parser.parse_args()

    if args.command == "projects":
        manager.list_projects(show_details=args.details)
    elif args.command == "create":
        manager.create_project(
            args.project_name,
            python_version=args.python,
            packages=args.packages,
            env_file=args.file,
        )
    elif args.command == "refresh":
        manager.refresh_project(
            args.project_name,
            python_version=args.python,
            packages=args.packages,
            env_file=args.file,
        )
    elif args.command == "config":
        _handle_config_command(args)
    elif args.command == "workspace":
        _handle_workspace_command(args)
    elif args.command == "dev":
        _handle_dev_command(args)
    elif args.command == "activate":
        manager.activate_project(args.project_name)
    elif args.command == "root":
        _emit_project_path(args.path_or_name, "root", "taurworks root")
    elif args.command == "working":
        _emit_project_path(args.path_or_name, "working", "taurworks working")
    elif args.command == "shell":
        _handle_shell_command(args)
    elif args.command == "project":
        if (
            args.project_command == "init"
            and args.create_working_dir
            and args.working_dir is None
        ):
            parser_project_init.error("--create-working-dir requires --working-dir")
        if (
            args.project_command == "create"
            and args.create_working_dir
            and args.working_dir is None
        ):
            parser_project_create.error("--create-working-dir requires --working-dir")
        if args.project_command == "activate" and not args.print_only:
            parser_project.error(
                "project activate currently requires --print and is read-only."
            )
        _handle_project_command(args)


if __name__ == "__main__":
    main()
