import argparse
from taurworks.manager import create_project, activate_project, list_projects

def main():
    parser = argparse.ArgumentParser(prog="taurworks", description="Manage taurworks projects.")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List projects
    parser_list = subparsers.add_parser("projects", help="List available project environments.")

    # Create a project
    parser_create = subparsers.add_parser("create", help="Create a new project.")
    parser_create.add_argument("project_name", type=str, help="Name of the project to create.")

    # Activate a project
    parser_activate = subparsers.add_parser("activate", help="Activate an existing project.")
    parser_activate.add_argument("project_name", type=str, help="Name of the project to activate.")

    args = parser.parse_args()

    if args.command == "projects":
        list_projects()
    elif args.command == "create":
        create_project(args.project_name)
    elif args.command == "activate":
        activate_project(args.project_name)

if __name__ == "__main__":
    main()

