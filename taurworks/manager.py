import os
import subprocess

TAURWORKS_WORKSPACE = os.getenv("TAURWORKS_WORKSPACE", os.path.expanduser("~/Workspace"))

def list_projects():
    """Lists available projects in the workspace."""
    if not os.path.exists(TAURWORKS_WORKSPACE):
        print(f"No workspace found at {TAURWORKS_WORKSPACE}.")
        return
    
    projects = [p for p in os.listdir(TAURWORKS_WORKSPACE) if os.path.isdir(os.path.join(TAURWORKS_WORKSPACE, p))]
    if projects:
        print("Available projects:")
        for project in projects:
            print(f"- {project}")
    else:
        print("No projects found.")

def create_project(project_name, python_version="3.11", packages=None, env_file=None):
    """Creates a new project with optional Conda customization."""
    project_dir = os.path.join(TAURWORKS_WORKSPACE, project_name)
    admin_dir = os.path.join(project_dir, ".taurworks")
    repo_dir = os.path.join(project_dir, project_name)
    env_name = f"{project_name}"  # Conda environment name

    # Ensure workspace exists
    os.makedirs(TAURWORKS_WORKSPACE, exist_ok=True)
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(admin_dir, exist_ok=True)

    # Create Conda environment
    print(f"Creating Conda environment: {env_name} ...")

    if env_file:
        print(f"Using environment file: {env_file}")
        subprocess.run(["conda", "env", "create", "--name", env_name, "--file", env_file], check=True)
    else:
        conda_cmd = ["conda", "create", "--name", env_name, f"python={python_version}", "-y"]
        if packages:
            package_list = packages.split(",")
            conda_cmd.extend(package_list)
            print(f"Installing additional packages: {package_list}")

        subprocess.run(conda_cmd, check=True)

    # Create the repository directory
    os.makedirs(repo_dir, exist_ok=True)

    # Generate the project-setup.source script
    setup_script = os.path.join(admin_dir, "project-setup.source")
    with open(setup_script, "w") as f:
        f.write(f"""#!/bin/bash
# Activate Conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate {env_name}
# Change to repository directory
cd "{repo_dir}"
""")
    os.chmod(setup_script, 0o755)  # Make executable

    print(f"Project {project_name} created successfully.")
    print(f"To activate, run: source {setup_script}")

def activate_project(project_name):
    """Activates a project by sourcing its setup script."""
    project_dir = os.path.join(TAURWORKS_WORKSPACE, project_name)
    admin_dir = os.path.join(project_dir, ".taurworks")
    setup_script = os.path.join(admin_dir, "project-setup.source")

    if not os.path.exists(setup_script):
        print(f"Error: No setup script found for project {project_name} at {setup_script}")
        return

    print(f"Run the following command to activate:\n")
    print(f"source {setup_script}")
