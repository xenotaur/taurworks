import argparse

from taurworks import manager
from taurworks import project_resolution


def _handle_project_command(args):
    """Handle scaffolded `taurworks project ...` commands."""
    if args.project_command == "where":
        diagnostics = project_resolution.gather_project_where_diagnostics()
        print(project_resolution.format_project_where_output(diagnostics))
        return

    if args.project_command == "list":
        diagnostics = project_resolution.gather_project_list_diagnostics()
        print(project_resolution.format_project_list_output(diagnostics))
        return

    if args.project_command == "refresh":
        diagnostics = project_resolution.gather_project_refresh_diagnostics(
            args.path_or_name
        )
        print(project_resolution.format_project_refresh_output(diagnostics))
        return
    if args.project_command == "create":
        diagnostics = project_resolution.gather_project_create_diagnostics(
            args.path_or_name
        )
        print(project_resolution.format_project_create_output(diagnostics))
        return
    if args.project_command == "activate":
        diagnostics = project_resolution.gather_project_activate_print_diagnostics(
            args.path_or_name
        )
        print(project_resolution.format_project_activate_print_output(diagnostics))
        return

    args.project_parser.print_help()


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

    parser_project_create = project_subparsers.add_parser(
        "create",
        help=(
            "Ensure target directory exists, then safely refresh Taurworks "
            "project scaffolding without overwriting files."
        ),
        description=(
            "Create a target directory when needed, then delegate to project "
            "refresh for safe, idempotent Taurworks metadata scaffolding."
        ),
    )
    parser_project_create.add_argument(
        "path_or_name",
        nargs="?",
        help=(
            "Optional project path or name. Defaults to current working "
            "directory when omitted."
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
            "Optional project path or name. Defaults to current working "
            "directory when omitted."
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
    elif args.command == "activate":
        manager.activate_project(args.project_name)
    elif args.command == "project":
        if args.project_command == "activate" and not args.print_only:
            parser_project.error(
                "project activate currently requires --print and is read-only."
            )
        _handle_project_command(args)


if __name__ == "__main__":
    main()
