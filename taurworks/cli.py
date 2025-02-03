import argparse
from taurworks.manager import create_project, activate_project, list_projects

def main():
    parser = argparse.ArgumentParser(prog="taurworks", description="Manage taurworks projects.")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List projects with optional details
    parser_list = subparsers.add_parser("projects", help="List available project environments.")
    parser_list.add_argument("-l", "--details", action="store_true", help="Show detailed project information.")

    # Create a project with optional Conda settings
    parser_create = subparsers.add_parser("create", help="Create a new project.")
    parser_create.add_argument("project_name", type=str, help="Name of the project to create.")
    parser_create.add_argument("--python", type=str, default="3.11", help="Specify Python version (default: 3.11).")
    parser_create.add_argument("--packages", type=str, help="Comma-separated list of additional packages.")
    parser_create.add_argument("--file", type=str, help="Path to a Conda environment YAML file.")

    # Activate a project
    parser_activate = subparsers.add_parser("activate", help="Activate an existing project.")
    parser_activate.add_argument("project_name", type=str, help="Name of the project to activate.")

    args = parser.parse_args()

    if args.command == "projects":
        list_projects(show_details=args.details)
    elif args.command == "create":
        create_project(args.project_name, python_version=args.python, packages=args.packages, env_file=args.file)
    elif args.command == "activate":
        activate_project(args.project_name)

if __name__ == "__main__":
    main()
