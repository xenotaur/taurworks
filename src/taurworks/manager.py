import os
import pathlib
import re
import sys
import subprocess
import tomllib

from taurworks import project_internals

TAURWORKS_WORKSPACE = os.getenv(
    "TAURWORKS_WORKSPACE", os.path.expanduser("~/Workspace")
)

PROJECT_STATUS_INITIALIZED = "initialized"
PROJECT_STATUS_WORKSPACE_ONLY = "workspace-only"
PROJECT_STATUS_LEGACY_ADMIN = "legacy-admin"
CONDA_ENV_LIST_TIMEOUT_SECONDS = 2


def workspace_path():
    """Return the configured workspace path using the current environment."""
    return pathlib.Path(
        os.getenv("TAURWORKS_WORKSPACE", os.path.expanduser("~/Workspace"))
    ).expanduser()


def get_conda_environments():
    """Returns a set of existing Conda environment names."""
    try:
        result = subprocess.run(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=CONDA_ENV_LIST_TIMEOUT_SECONDS,
        )
        envs = set()
        for line in result.stdout.split("\n"):
            if line and not line.startswith("#") and " " in line:
                env_name = line.split()[0]  # Extract the environment name
                # Conda paths might appear
                envs.add(os.path.basename(env_name))
        return envs
    except subprocess.TimeoutExpired:
        print(
            "Warning: Could not fetch Conda environments: "
            f"`conda env list` timed out after {CONDA_ENV_LIST_TIMEOUT_SECONDS} seconds"
        )
        return set()
    except Exception as e:
        print(f"Warning: Could not fetch Conda environments: {e}")
        return set()


def create_conda_environment(
    env_name, python_version="3.11", packages=None, env_file=None
):
    """Creates a Conda environment if it does not exist."""
    if env_name in get_conda_environments():
        print(f"✔ Conda environment {env_name} already exists.")
        return

    print(f"Creating Conda environment: {env_name} ...")
    if env_file:
        print(f"Using environment file: {env_file}")
        subprocess.run(
            ["conda", "env", "create", "--name", env_name, "--file", env_file],
            check=True,
        )
    else:
        conda_cmd = [
            "conda",
            "create",
            "--name",
            env_name,
            f"python={python_version}",
            "-y",
        ]
        if packages:
            package_list = packages.split(",")
            conda_cmd.extend(package_list)
            print(f"Installing additional packages: {package_list}")

        subprocess.run(conda_cmd, check=True)


def camel_to_snake(name):
    """Convert CamelCase to snake_case."""
    return re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()


def refresh_project(project_name, python_version="3.11", packages=None, env_file=None):
    """Ensures a project is correctly set up."""
    project_dir = os.path.join(TAURWORKS_WORKSPACE, project_name)
    admin_dir = os.path.join(project_dir, ".taurworks")
    repo_name = camel_to_snake(project_name)
    repo_dir = os.path.join(project_dir, repo_name)
    env_name = f"{project_name}"

    # Ensure workspace exists
    os.makedirs(TAURWORKS_WORKSPACE, exist_ok=True)

    # Ensure project directory exists
    if not os.path.exists(project_dir):
        print(f"Creating project directory: {project_dir}")
        os.makedirs(project_dir)

    # Ensure .taurworks directory exists
    if not os.path.exists(admin_dir):
        print(f"Creating .taurworks directory: {admin_dir}")
        os.makedirs(admin_dir)

    # Ensure Conda environment exists
    create_conda_environment(env_name, python_version, packages, env_file)

    # Ensure repository directory exists
    if not os.path.exists(repo_dir):
        print(f"Creating repository directory: {repo_dir}")
        os.makedirs(repo_dir)

    # Ensure project-setup.source script exists
    setup_script = os.path.join(admin_dir, "project-setup.source")
    if not os.path.exists(setup_script):
        print(f"Creating setup script: {setup_script}")
        with open(setup_script, "w") as f:
            f.write(f"""#!/bin/bash
# Activate Conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate {env_name}
# Change to repository directory
cd "{repo_dir}"
""")
        os.chmod(setup_script, 0o755)  # Make executable
    else:
        print("✔ Setup script already exists.")

    print(f"✔ Project {project_name} is fully set up.")
    print(f"To activate, run: source {setup_script}")


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


def classify_project_entry(project_dir):
    """Classify a workspace directory for listing and activation guidance."""
    project_path = pathlib.Path(project_dir)
    config_path = project_internals.project_config_path(project_path)
    legacy_setup_path = project_path / "Admin" / "project-setup.source"
    metadata_dir_exists = (project_path / ".taurworks").is_dir()
    status = PROJECT_STATUS_WORKSPACE_ONLY
    if config_path.is_file():
        status = PROJECT_STATUS_INITIALIZED
    elif legacy_setup_path.is_file():
        status = PROJECT_STATUS_LEGACY_ADMIN

    working_dir = "none"
    resolved_working_dir = "none"
    working_dir_configured = False
    working_dir_exists = False
    activation_eligible = False
    if metadata_dir_exists:
        status_message = (
            "workspace metadata directory exists but config.toml is missing; "
            "not initialized for `tw activate`"
        )
    else:
        status_message = "not initialized for `tw activate`"

    if status == PROJECT_STATUS_INITIALIZED:
        status_message = "initialized but no working_dir is configured"
        try:
            config = project_internals.read_project_config(project_path)
            configured_working_dir = project_internals.working_dir_from_config(config)
            if configured_working_dir is not None:
                (
                    relative_working_dir,
                    absolute_working_dir,
                    working_dir_exists,
                ) = project_internals.resolve_configured_working_dir(
                    project_path, configured_working_dir
                )
                working_dir = relative_working_dir.as_posix()
                resolved_working_dir = str(absolute_working_dir)
                working_dir_configured = True
                activation_eligible = working_dir_exists
                if working_dir_exists:
                    status_message = "eligible for `tw activate`"
                else:
                    status_message = (
                        "working_dir is configured but missing on disk; "
                        "not eligible for `tw activate`"
                    )
        except (
            project_internals.ProjectConfigError,
            OSError,
            tomllib.TOMLDecodeError,
        ) as error:
            status_message = f"initialized but activation metadata is invalid: {error}"
    elif status == PROJECT_STATUS_LEGACY_ADMIN:
        status_message = (
            "legacy Admin/project-setup.source recognized; not sourced by `tw activate`"
        )

    return {
        "name": project_path.name,
        "path": str(project_path),
        "status": status,
        "config_path": str(config_path),
        "metadata_dir_exists": metadata_dir_exists,
        "config_exists": config_path.is_file(),
        "legacy_setup_path": str(legacy_setup_path),
        "legacy_setup_exists": legacy_setup_path.is_file(),
        "working_dir_configured": working_dir_configured,
        "working_dir": working_dir,
        "resolved_working_dir": resolved_working_dir,
        "working_dir_exists": working_dir_exists,
        "activation_eligible": activation_eligible,
        "status_message": status_message,
    }


def discover_workspace_projects(workspace):
    """Return classified direct child directories from an existing workspace."""
    return [
        classify_project_entry(child)
        for child in sorted(workspace.iterdir(), key=lambda path: path.name)
        if child.is_dir()
    ]


def list_projects(show_details=False):
    """Lists available projects in the workspace, with status classification."""
    workspace = workspace_path()
    if not workspace.exists():
        print(f"No workspace found at {workspace}.")
        return

    projects = discover_workspace_projects(workspace)
    if not projects:
        print("No projects found.")
        return

    conda_envs = get_conda_environments() if show_details else set()
    name_width = max(len(project["name"]) for project in projects)

    print("Available projects:\n")
    for project in projects:
        if show_details:
            project_dir = project["path"]
            has_env = project["name"] in conda_envs
            dir_size, file_count = get_directory_info(project_dir)
            size_str = f"{dir_size / (1024*1024):.2f} MB"
            print(f"- {project['name']}")
            print(f"  ├── Status: {project['status']}")
            print(f"  ├── Path: {project['path']}")
            print(f"  ├── Metadata Dir Exists: {project['metadata_dir_exists']}")
            print(f"  ├── Config: {project['config_path']}")
            print(f"  ├── Config Exists: {'✔' if project['config_exists'] else '✘'}")
            print(
                "  ├── Legacy Admin Setup: "
                f"{'✔' if project['legacy_setup_exists'] else '✘'} "
                f"({project['legacy_setup_path']})"
            )
            print(
                "  ├── Activation Eligible: "
                f"{'✔' if project['activation_eligible'] else '✘'}"
            )
            print(f"  ├── Working Dir: {project['working_dir']}")
            print(f"  ├── Resolved Working Dir: {project['resolved_working_dir']}")
            print(f"  ├── Working Dir Exists: {project['working_dir_exists']}")
            print(f"  ├── Status Message: {project['status_message']}")
            print(
                f"  ├── Conda Env Exists: {'✔' if has_env else '✘'} "
                f"({'active' if has_env else 'missing'})"
            )
            print(f"  ├── Files: {file_count}, Size: {size_str}\n")
        else:
            print(f"- {project['name'].ljust(name_width)}    {project['status']}")


def create_project(project_name, python_version="3.11", packages=None, env_file=None):
    """Creates a new project with the predefined structure."""
    project_dir = os.path.join(TAURWORKS_WORKSPACE, project_name)

    # Check if the project already exists
    if os.path.exists(project_dir):
        print(
            f"❌ Error: Project '{project_name}' already exists at {project_dir}.",
            file=sys.stderr,
        )
        sys.exit(1)

    admin_dir = os.path.join(project_dir, ".taurworks")
    repo_dir = os.path.join(project_dir, project_name)
    env_name = f"{project_name}"

    # Ensure workspace exists
    os.makedirs(TAURWORKS_WORKSPACE, exist_ok=True)
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(admin_dir, exist_ok=True)

    # Create Conda environment
    print(f"Creating Conda environment: {env_name} ...")

    if env_file:
        print(f"Using environment file: {env_file}")
        subprocess.run(
            ["conda", "env", "create", "--name", env_name, "--file", env_file],
            check=True,
        )
    else:
        conda_cmd = [
            "conda",
            "create",
            "--name",
            env_name,
            f"python={python_version}",
            "-y",
        ]
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

    print(f"✔ Project '{project_name}' created successfully.")
    print(f"To activate, run: source {setup_script}")


def activate_project(project_name):
    """Print compatibility activation guidance for a workspace project."""
    project_dir = workspace_path() / project_name
    project = classify_project_entry(project_dir)

    if project["status"] == PROJECT_STATUS_INITIALIZED:
        if project["activation_eligible"]:
            print("Run the following command to activate with the shell helper:\n")
            print(f"tw activate {project_name}")
            return
        print(
            f"Project {project_name} is initialized but is not eligible for `tw activate`."
        )
        print("Run `taurworks project working-dir set [DIR]` to configure it.")
        sys.exit(1)

    if project["status"] == PROJECT_STATUS_LEGACY_ADMIN:
        print(
            f"Project {project_name} is listed as legacy-admin but is not initialized for `tw activate`."
        )
        print("Run `taurworks project init ...` or migrate the legacy setup.")
        sys.exit(1)

    print(
        f"Project {project_name} is listed as workspace-only but is not initialized for `tw activate`."
    )
    print("Run `taurworks project init ...` to initialize it.")
    sys.exit(1)
