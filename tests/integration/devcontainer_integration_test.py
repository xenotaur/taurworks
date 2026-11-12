import os
import pathlib
import shutil
import stat
import subprocess
import unittest

from taurworks import environments


@unittest.skipUnless(
    os.environ.get("TAURWORKS_RUN_DEVCONTAINER_INTEGRATION") == "1",
    "set TAURWORKS_RUN_DEVCONTAINER_INTEGRATION=1 with Docker and devcontainer installed",
)
class DevContainerIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for executable in ("docker", "devcontainer"):
            if shutil.which(executable) is None:
                raise unittest.SkipTest(f"{executable} executable is unavailable")

        docker_socket = pathlib.Path("/var/run/docker.sock")
        try:
            socket_mode = docker_socket.stat().st_mode
        except OSError as error:
            raise unittest.SkipTest(
                f"Docker socket is unavailable: {docker_socket} ({error})"
            ) from error
        if not stat.S_ISSOCK(socket_mode):
            raise unittest.SkipTest(f"Docker endpoint is not a socket: {docker_socket}")
        if not os.access(docker_socket, os.R_OK | os.W_OK):
            raise unittest.SkipTest(
                f"Docker socket is not readable and writable: {docker_socket}"
            )

        for command, label in (
            (("docker", "version", "--format", "{{.Server.Version}}"), "Docker daemon"),
            (("docker", "buildx", "version"), "Docker Buildx"),
        ):
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=15,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise unittest.SkipTest(f"{label} is unavailable: {error}") from error
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "command failed").strip()
                raise unittest.SkipTest(f"{label} is unavailable: {detail}")

    def test_executes_inside_reference_cli_environment(self):
        root = pathlib.Path(__file__).parent / "fixture"
        context = environments.EnvironmentContext(
            project_name="taurworks-integration",
            project_root=root,
            host_working_dir=root,
            relative_working_dir=pathlib.Path("."),
            environment=environments.EnvironmentSpec("devcontainer"),
            exports={"TAURWORKS_INTEGRATION": "ready"},
        )
        provider = environments.DevContainerEnvironmentProvider()
        self.assertEqual(
            provider.execute(
                context,
                ["/bin/sh", "-c", 'test "$TAURWORKS_INTEGRATION" = ready'],
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
