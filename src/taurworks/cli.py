import argparse
import sys

from taurworks import manager
from taurworks import project_resolution


PROJECT_NOT_IMPLEMENTED_MESSAGE = (
    "The 'taurworks project {command}' command is a scaffold placeholder and is "
    "not implemented yet."
)


def _handle_project_command(args):
    """Handle scaffolded `taurworks project ...` commands."""
    if args.project_command == "where":
        diagnostics = project_resolution.gather_project_where_diagnostics()
        print(project_resolution.format_project_where_output(diagnostics))
        return

    if args.project_command == "list":
        print(
            PROJECT_NOT_IMPLEMENTED_MESSAGE.format(command=args.project_command),
            file=sys.stderr,
        )
        print(
            "Use `taurworks project --help` to view planned read-only commands.",
            file=sys.stderr,
        )
        return

    args.project_parser.print_help()


def main():
    parser = argparse.ArgumentParser(
        prog="taurworks", description="Manage taurworks projects.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # List projects
    parser_list = subparsers.add_parser(
        "projects", help="List available project environments.")
    parser_list.add_argument(
        "-l", "--details", action="store_true", help="Show detailed project information.")

    # Create a project
    parser_create = subparsers.add_parser(
        "create", help="Create a new project.")
    parser_create.add_argument(
        "project_name", type=str, help="Name of the project to create.")
    parser_create.add_argument(
        "--python", type=str, default="3.11", help="Specify Python version (default: 3.11).")
    parser_create.add_argument(
        "--packages", type=str, help="Comma-separated list of additional packages.")
    parser_create.add_argument(
        "--file", type=str, help="Path to a Conda environment YAML file.")

    # Refresh a project
    parser_refresh = subparsers.add_parser(
        "refresh", help="Ensure a project is correctly set up.")
    parser_refresh.add_argument(
        "project_name", type=str, help="Name of the project to refresh.")
    parser_refresh.add_argument(
        "--python", type=str, default="3.11", help="Specify Python version (default: 3.11).")
    parser_refresh.add_argument(
        "--packages", type=str, help="Comma-separated list of additional packages.")
    parser_refresh.add_argument(
        "--file", type=str, help="Path to a Conda environment YAML file.")

    # Activate a project
    parser_activate = subparsers.add_parser(
        "activate", help="Activate an existing project.")
    parser_activate.add_argument(
        "project_name", type=str, help="Name of the project to activate.")

    # Scaffolded `project` namespace
    parser_project = subparsers.add_parser(
        "project",
        help="Project command namespace scaffold (read-only planning stage).",
        description=(
            "Scaffolded namespace for planned project lifecycle commands. "
            "This stage exposes help and command shape only."
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
        help="(Planned) List registered projects (placeholder).",
        description=(
            "Placeholder command. Planned to list registered projects in a "
            "read-only way."
        ),
    )
    parser_project_list.set_defaults(project_parser=parser_project)

    parser_project.set_defaults(project_parser=parser_project)

    args = parser.parse_args()

    if args.command == "projects":
        manager.list_projects(show_details=args.details)
    elif args.command == "create":
        manager.create_project(args.project_name, python_version=args.python,
                               packages=args.packages, env_file=args.file)
    elif args.command == "refresh":
        manager.refresh_project(args.project_name, python_version=args.python,
                                packages=args.packages, env_file=args.file)
    elif args.command == "activate":
        manager.activate_project(args.project_name)
    elif args.command == "project":
        _handle_project_command(args)


if __name__ == "__main__":
    main()
