import os
import subprocess

TAURWORKS_WORKSPACE = os.getenv("TAURWORKS_WORKSPACE", os.path.expanduser("~/Workspace"))

def get_conda_environments():
    """Returns a set of existing Conda environment names."""
    try:
        result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True, check=True)
        envs = set()
        for line in result.stdout.split("\n"):
            if line and not line.startswith("#") and " " in line:
                env_name = line.split()[0]  # Extract the environment name
                envs.add(os.path.basename(env_name))  # Conda paths might appear
        return envs
    except Exception as e:
        print(f"Warning: Could not fetch Conda environments: {e}")
        return set()

def get_directory_info(path):
    """Returns the total size and number of files in a directory."""
    total_size = 0
    file_count = 0
    for root, _, files in os.walk(path):
        file_count += len(files)
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size, file_count

def list_projects(show_details=False):
    """Lists available projects in the workspace, with optional details."""
    if not os.path.exists(TAURWORKS_WORKSPACE):
        print(f"No workspace found at {TAURWORKS_WORKSPACE}.")
        return
    
    projects = [p for p in os.listdir(TAURWORKS_WORKSPACE) if os.path.isdir(os.path.join(TAURWORKS_WORKSPACE, p))]
    if not projects:
        print("No projects found.")
        return

    conda_envs = get_conda_environments()

    print("Available projects:\n")
    for project in projects:
        project_dir = os.path.join(TAURWORKS_WORKSPACE, project)
        admin_dir = os.path.join(project_dir, ".taurworks")
        has_admin = os.path.exists(admin_dir)
        has_env = project in conda_envs

        if show_details:
            dir_size, file_count = get_directory_info(project_dir)
            size_str = f"{dir_size / (1024*1024):.2f} MB"  # Convert to MB
            print(f"- {project}")
            print(f"  ├── .taurworks Exists: {'✔' if has_admin else '✘'}")
            print(f"  ├── Conda Env Exists: {'✔' if has_env else '✘'} ({'active' if has_env else 'missing'})")
            print(f"  ├── Files: {file_count}, Size: {size_str}\n")
        else:
            print(f"- {project}")


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
