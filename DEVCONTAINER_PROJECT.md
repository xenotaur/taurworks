# Dev Container projects with Taurworks

This guide explains how to configure a project so Taurworks can enter it and
run development commands inside a Dev Container.

Taurworks is the host-side control plane. The project owns its
`devcontainer.json`, image, Dockerfile, Features, mounts, ports, users, and
lifecycle commands. Taurworks stores only the provider selection and delegates
container operations to the reference `devcontainer` CLI.

## Prerequisites

Install and verify these tools on the host:

```bash
docker version
docker buildx version
docker ps
devcontainer --version
```

The Docker daemon must be running, the current user must be able to access the
Docker socket, and the `devcontainer` command must be on `PATH`.

Install the reference CLI with npm when needed:

```bash
npm install --global @devcontainers/cli
```

On WSL, check that `/var/run/docker.sock` is a socket owned by a group your
user belongs to. A Docker configuration that references an unavailable helper
such as `docker-credential-desktop.exe` can prevent image pulls; remove or
replace that helper, or pull images using a working Docker configuration.

## Initialize a project

Set a workspace once, then initialize an existing project directory:

```bash
taurworks workspace set ~/Workspace
taurworks project init ~/Workspace/my-container-project --working-dir .
```

Initialize the shell helper if `tw` is not already available:

```bash
mkdir -p ~/.config/taurworks
taurworks shell print > ~/.config/taurworks/taurworks-shell.sh
source ~/.config/taurworks/taurworks-shell.sh
```

Create the Dev Container configuration directory:

```bash
mkdir -p ~/Workspace/my-container-project/.devcontainer
```

Add this provider metadata to the project’s
`.taurworks/config.toml`:

```toml
[paths]
working_dir = "."

[activation.environment]
type = "devcontainer"
# Optional when using a non-default configuration path:
# config = ".devcontainer/devcontainer.json"

[dev.commands]
test = "python -m pytest -q"
lint = "ruff check ."
```

Taurworks discovers these paths automatically:

1. `.devcontainer/devcontainer.json`
2. `.devcontainer.json`

Use `activation.environment.config` only when the configuration is elsewhere
under the project root. Absolute paths and paths escaping the project root are
rejected.

## Create `devcontainer.json`

The smallest valid configuration selects an image:

```json
{
  "name": "my-container-project",
  "image": "python:3.12-slim"
}
```

The Dev Container CLI automatically mounts the project workspace. Add a
`postCreateCommand` when the image needs project dependencies installed:

```json
{
  "name": "my-container-project",
  "image": "python:3.12-slim",
  "postCreateCommand": "python -m pip install --no-cache-dir -r requirements.txt"
}
```

Use a Dockerfile when the project needs system packages, a compiled toolchain,
or a custom base image:

```json
{
  "name": "my-container-project",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "remoteUser": "vscode"
}
```

Keep paths in `devcontainer.json` relative to the `.devcontainer` directory
unless the Dev Container specification says otherwise. Keep Taurworks paths in
`.taurworks/config.toml` relative to the project root.

## Language examples

Each example belongs in `.devcontainer/devcontainer.json`. Choose the example
that matches the project and adjust the `postCreateCommand` to its dependency
files.

### Python

```json
{
  "name": "Python project",
  "image": "python:3.12-slim",
  "postCreateCommand": "python -m pip install --no-cache-dir -r requirements.txt"
}
```

For a project with no requirements file, install the test tool directly:

```json
{
  "name": "Python project",
  "image": "python:3.12-slim",
  "postCreateCommand": "python -m pip install --no-cache-dir pytest"
}
```

### C and C++

Start with a basic Ubuntu image and install the compiler, build systems,
debugger, source-control client, and common Autotools dependencies:

```json
{
  "name": "C or C++ project",
  "image": "ubuntu:24.04",
  "postCreateCommand": "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential clang cmake ninja-build autoconf automake libtool pkg-config gdb git && rm -rf /var/lib/apt/lists/*"
}
```

This installs GCC/G++, Clang, Make, CMake, Ninja, Autoconf, Automake, Libtool,
pkg-config, GDB, and Git. Add project-specific development headers (for
example, `libssl-dev` or `libboost-dev`) to the same package list.

A typical Taurworks command section is:

```toml
[dev.commands]
build = "cmake --build build"
test = "ctest --test-dir build --output-on-failure"
```

### C# / .NET

Use the basic .NET SDK image for the language runtime, then add the repository
and native build tools that are commonly useful in a developer container:

```json
{
  "name": "C# project",
  "image": "mcr.microsoft.com/dotnet/sdk:8.0",
  "postCreateCommand": "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates make cmake ninja-build autoconf automake && rm -rf /var/lib/apt/lists/* && dotnet restore"
}
```

The image supplies the .NET SDK; the post-create command adds Git, curl,
Make, CMake, Ninja, Autoconf, and Automake. Add tools such as `protobuf-compiler`
or native library headers when the project requires them.

Example Taurworks commands:

```toml
[dev.commands]
build = "dotnet build --no-restore"
test = "dotnet test --no-restore"
```

### Java

Start with a basic Temurin JDK image and install source-control, archive,
native-build, and Java build tools. This example uses Maven:

```json
{
  "name": "Java project",
  "image": "eclipse-temurin:21-jdk-jammy",
  "postCreateCommand": "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git curl unzip zip maven ant make cmake autoconf automake && rm -rf /var/lib/apt/lists/* && ./mvnw -q -DskipTests package"
}
```

This installs Git, curl, archive utilities, Maven, Ant, Make, CMake,
Autoconf, and Automake. For a Gradle project, install Gradle instead of Maven
and use `./gradlew` when the repository includes the Gradle wrapper:

```json
{
  "name": "Java project",
  "image": "eclipse-temurin:21-jdk-jammy",
  "postCreateCommand": "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git curl unzip zip gradle ant make cmake autoconf automake && rm -rf /var/lib/apt/lists/* && ./gradlew assemble"
}
```

Example Maven commands:

```toml
[dev.commands]
build = "./mvnw -q package"
test = "./mvnw -q test"
```

## Activate and work in the project

List projects and confirm activation eligibility:

```bash
tw projects --details
```

Activate the project from the host shell:

```bash
tw activate my-container-project
```

Taurworks then:

1. validates the provider and configuration;
2. runs `devcontainer up`;
3. reuses or creates the container;
4. determines the container workspace from `remoteWorkspaceFolder`; and
5. enters an interactive shell through `devcontainer exec`.

Inside the container, run the configured commands normally:

```bash
tw dev test
tw dev lint
```

`tw dev ...` resolves commands from `[dev.commands]` first, then from a
project-local `scripts/<command>` file. For a Dev Container project, the
resolved command is executed through `devcontainer exec`.

Check the active context inside the container:

```bash
echo "$TAURWORKS_ACTIVE_PROJECT"
echo "$TAURWORKS_ENVIRONMENT_TYPE"
echo "$TAURWORKS_EXECUTION_ENVIRONMENT"
```

The environment values should identify the project and report
`devcontainer`.

Exit the container to return to the host control shell:

```bash
exit
```

To switch projects, always switch from the host shell. Exit the current
container first, then run for example:

```bash
tw activate python-project
tw dev test
```

Nested activation from inside a Taurworks-managed Dev Container is rejected.

## Prepare without entering

To validate and start the container without opening an interactive shell:

```bash
taurworks environment prepare my-container-project
```

To enter it explicitly from the host:

```bash
taurworks environment enter my-container-project
```

The normal user-facing workflow remains `tw activate`.

## Verify the runtime directly

When activation fails, run the project’s Dev Container command directly with
trace logging:

```bash
devcontainer up \
  --workspace-folder ~/Workspace/my-container-project \
  --config ~/Workspace/my-container-project/.devcontainer/devcontainer.json \
  --log-level trace
```

This distinguishes Docker daemon, image-pull, mount, build, and lifecycle
errors from Taurworks configuration errors.

Run the repository’s opt-in integration test when Docker and the Dev Container
CLI are available:

```bash
TAURWORKS_RUN_DEVCONTAINER_INTEGRATION=1 \
PYTHONPATH=src \
python -m unittest tests.integration.devcontainer_integration_test
```

The test preflights Docker, Buildx, socket access, and daemon availability,
then starts the fixture container and verifies a command executes inside it.

## Common problems

### `Activation Eligible: ✘`

Inspect the project configuration:

```bash
cat .taurworks/config.toml
tw projects --details
```

Ensure `[paths].working_dir` exists and that the activation type is exactly
`devcontainer`.

### Invalid TOML

Only TOML belongs in `.taurworks/config.toml`. Do not paste explanatory prose,
Markdown headings, or JSON into that file.

### Docker socket permission denied

Check:

```bash
groups
stat -c '%a %U %G' /var/run/docker.sock
docker ps
```

The current user needs read/write access to the socket. Start a fresh shell
after adding the user to the Docker group.

### Credential-helper failure

Errors such as `docker-credential-desktop.exe: executable file not found` mean
the Docker config references a helper unavailable in the current environment.
Remove or replace that helper in `~/.docker/config.json`, then retry the image
pull.

### Image or build failure

Run `devcontainer up --log-level trace` directly. Confirm that the image name,
Dockerfile path, registry credentials, and build context are valid.

### Switching does not work

Exit the current Dev Container shell before running `tw activate` for another
project. Taurworks intentionally prevents nested environment transitions.

## Safety and lifecycle notes

`tw activate` may start or reuse a container, but exiting the interactive shell
does not stop, remove, or rebuild it. The project’s Dev Container configuration
remains authoritative for all container lifecycle behavior. Taurworks does not
edit shell startup files, install Docker, install the `devcontainer` CLI, or
silently create a missing project working directory.
