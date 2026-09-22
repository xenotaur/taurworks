import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from taurworks import dev
from taurworks import environments
from taurworks import project_internals

SHELL_HELPER = (
    pathlib.Path(__file__).parents[1]
    / "src"
    / "taurworks"
    / "resources"
    / "shell"
    / "taurworks-shell.sh"
)


def _context(
    root: pathlib.Path,
    *,
    environment: environments.EnvironmentSpec | None = None,
    working_dir: str = "backend",
) -> environments.EnvironmentContext:
    host_working_dir = root / working_dir
    host_working_dir.mkdir(parents=True, exist_ok=True)
    return environments.EnvironmentContext(
        project_name="Example",
        project_root=root,
        host_working_dir=host_working_dir,
        relative_working_dir=pathlib.Path(working_dir),
        environment=environment or environments.EnvironmentSpec("devcontainer"),
        exports={"PROJECT_FLAG": "value with spaces"},
    )


def _completed(
    argv,
    returncode=0,
    stdout="",
    stderr="",
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


class EnvironmentConfigurationTest(unittest.TestCase):
    def test_valid_conda_configuration_is_backward_compatible(self):
        config = {"activation": {"environment": {"type": "conda", "name": "A"}}}
        self.assertEqual(
            {"type": "conda", "name": "A"},
            project_internals.activation_environment_from_config(config),
        )

    def test_valid_devcontainer_default_and_explicit_configuration(self):
        default = {"activation": {"environment": {"type": "devcontainer"}}}
        explicit = {
            "activation": {
                "environment": {
                    "type": "devcontainer",
                    "config": ".devcontainer/custom.json",
                }
            }
        }
        self.assertEqual(
            {"type": "devcontainer"},
            project_internals.activation_environment_from_config(default),
        )
        self.assertEqual(
            {"type": "devcontainer", "config": ".devcontainer/custom.json"},
            project_internals.activation_environment_from_config(explicit),
        )

    def test_invalid_provider_fields_and_config_traversal_are_rejected(self):
        invalid_configs = (
            {"type": "conda", "name": "A", "config": "extra.json"},
            {"type": "devcontainer", "name": "not-allowed"},
            {"type": "devcontainer", "config": "../outside.json"},
            {"type": "unknown"},
        )
        for environment_config in invalid_configs:
            with self.subTest(environment_config=environment_config):
                with self.assertRaises(project_internals.ProjectConfigError):
                    project_internals.activation_environment_from_config(
                        {"activation": {"environment": environment_config}}
                    )

    def test_provider_dispatch_includes_host_conda_and_devcontainer(self):
        expected = {
            "host": environments.HostEnvironmentProvider,
            "conda": environments.CondaEnvironmentProvider,
            "devcontainer": environments.DevContainerEnvironmentProvider,
        }
        for type_name, provider_type in expected.items():
            with self.subTest(type_name=type_name):
                self.assertIsInstance(
                    environments.provider_for(environments.EnvironmentSpec(type_name)),
                    provider_type,
                )


class DevContainerProviderTest(unittest.TestCase):
    def _config(self, root: pathlib.Path, relative=".devcontainer/devcontainer.json"):
        config_path = root / relative
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text('{"image":"example"}\n', encoding="utf-8")
        return config_path

    def test_default_config_discovery_supports_both_standard_locations(self):
        for relative in (".devcontainer/devcontainer.json", ".devcontainer.json"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp)
                expected = self._config(root, relative)
                context = _context(root)
                provider = environments.DevContainerEnvironmentProvider(
                    which=lambda _: "/usr/bin/devcontainer"
                )
                self.assertEqual(provider._config_path(context), expected.resolve())

    def test_explicit_config_and_spaces_preserve_argument_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="project with spaces ") as temp:
            root = pathlib.Path(temp)
            config = self._config(root, ".devcontainer/custom file.json")
            context = _context(
                root,
                environment=environments.EnvironmentSpec(
                    "devcontainer", config=".devcontainer/custom file.json"
                ),
            )
            calls = []

            def run(argv, **kwargs):
                calls.append((argv, kwargs))
                if "up" in argv:
                    payload = {
                        "outcome": "success",
                        "remoteWorkspaceFolder": "/workspaces/example",
                    }
                    return _completed(argv, stdout=json.dumps(payload) + "\n")
                return _completed(argv)

            provider = environments.DevContainerEnvironmentProvider(
                run=run, which=lambda _: "/usr/bin/devcontainer"
            )
            prepared = provider.prepare(context)

        self.assertEqual(prepared.container_working_dir, "/workspaces/example/backend")
        up_argv = calls[0][0]
        self.assertIn(str(root.resolve()), up_argv)
        self.assertIn(str(config.resolve()), up_argv)
        self.assertNotIn(" ".join(up_argv), up_argv)

    def test_missing_tool_config_and_nested_transition_fail_clearly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            context = _context(root)
            with self.assertRaisesRegex(
                environments.EnvironmentError, "CLI is unavailable"
            ):
                environments.DevContainerEnvironmentProvider(
                    which=lambda _: None
                ).validate(context)

            provider = environments.DevContainerEnvironmentProvider(
                which=lambda _: "/usr/bin/devcontainer"
            )
            with self.assertRaisesRegex(environments.EnvironmentError, "was not found"):
                provider.validate(context)

            self._config(root)
            with mock.patch.dict(
                os.environ,
                {"TAURWORKS_EXECUTION_ENVIRONMENT": "devcontainer"},
            ):
                with self.assertRaisesRegex(
                    environments.EnvironmentError, "unsafe nested"
                ):
                    provider.validate(context)

    def test_startup_failure_and_unusable_workspace_are_actionable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._config(root)
            context = _context(root)
            failed = environments.DevContainerEnvironmentProvider(
                run=lambda argv, **kwargs: _completed(
                    argv, 1, stderr="docker daemon unavailable\n"
                ),
                which=lambda _: "/usr/bin/devcontainer",
            )
            with self.assertRaisesRegex(
                environments.EnvironmentError, "docker daemon unavailable"
            ):
                failed.prepare(context)

            calls = 0

            def missing_directory(argv, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return _completed(
                        argv,
                        stdout=json.dumps(
                            {
                                "outcome": "success",
                                "remoteWorkspaceFolder": "/workspace/project",
                            }
                        ),
                    )
                return _completed(argv, 1)

            invalid = environments.DevContainerEnvironmentProvider(
                run=missing_directory, which=lambda _: "/usr/bin/devcontainer"
            )
            with self.assertRaisesRegex(
                environments.EnvironmentError, "working directory is unavailable"
            ):
                invalid.prepare(context)

    def test_noninteractive_execution_maps_paths_exports_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._config(root)
            script = root / "backend" / "scripts" / "test"
            script.parent.mkdir(parents=True)
            script.write_text("#!/bin/sh\n", encoding="utf-8")
            context = _context(root)
            calls = []

            def run(argv, **kwargs):
                calls.append(argv)
                if "up" in argv:
                    return _completed(
                        argv,
                        stdout=json.dumps(
                            {
                                "outcome": "success",
                                "remoteWorkspaceFolder": "/workspaces/example",
                            }
                        ),
                    )
                if "test" in argv and "-d" in argv:
                    return _completed(argv)
                return _completed(argv, 7)

            provider = environments.DevContainerEnvironmentProvider(
                run=run, which=lambda _: "/usr/bin/devcontainer"
            )
            exit_code = provider.execute(context, [str(script), "arg;still-one-arg"])

        self.assertEqual(exit_code, 7)
        exec_argv = calls[-1]
        self.assertIn("PROJECT_FLAG=value with spaces", exec_argv)
        self.assertIn("TAURWORKS_EXECUTION_ENVIRONMENT=devcontainer", exec_argv)
        self.assertFalse(any(value.startswith("CONDA_") for value in exec_argv))
        self.assertIn("/workspaces/example/backend/scripts/test", exec_argv)
        self.assertIn("arg;still-one-arg", exec_argv)

    def test_interactive_entry_uses_container_working_dir_and_inherited_tty(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._config(root)
            context = _context(root)
            calls = []

            def run(argv, **kwargs):
                calls.append((argv, kwargs))
                if "up" in argv:
                    return _completed(
                        argv,
                        stdout=json.dumps(
                            {
                                "outcome": "success",
                                "remoteWorkspaceFolder": "/container/workspace",
                            }
                        ),
                    )
                return _completed(argv)

            provider = environments.DevContainerEnvironmentProvider(
                run=run, which=lambda _: "/usr/bin/devcontainer"
            )
            self.assertEqual(provider.enter(context), 0)

        argv, kwargs = calls[-1]
        self.assertIn("/container/workspace/backend", argv)
        self.assertNotIn("capture_output", kwargs)


class DevCommandProviderExecutionTest(unittest.TestCase):
    def test_all_supported_commands_dispatch_through_configured_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            metadata = root / ".taurworks"
            metadata.mkdir()
            command_lines = "\n".join(
                f'{name} = "tool {name}"' for name in dev.DEV_V1_COMMANDS
            )
            (metadata / "config.toml").write_text(
                "schema_version = 1\n\n"
                '[project]\nname = "Example"\n\n'
                '[paths]\nworking_dir = "."\n\n'
                '[activation.environment]\ntype = "devcontainer"\n\n'
                f"[dev.commands]\n{command_lines}\n",
                encoding="utf-8",
            )
            original_cwd = pathlib.Path.cwd()
            os.chdir(root)
            try:
                provider = mock.Mock()
                provider.execute.return_value = 0
                with mock.patch.object(
                    environments, "provider_for", return_value=provider
                ):
                    for name in dev.DEV_V1_COMMANDS:
                        resolution = dev.resolve_dev_command(name)
                        self.assertEqual(dev.execute_dev_command(resolution), 0)
            finally:
                os.chdir(original_cwd)

        self.assertEqual(provider.execute.call_count, len(dev.DEV_V1_COMMANDS))
        for call, name in zip(provider.execute.call_args_list, dev.DEV_V1_COMMANDS):
            self.assertEqual(call.args[1], ["tool", name])


class ShellTransitionMatrixTest(unittest.TestCase):
    def _fake_taurworks(self, bin_dir: pathlib.Path) -> None:
        script = bin_dir / "taurworks"
        script.write_text(
            """#!/usr/bin/env python3
import os
import pathlib
import shlex
import sys

args = sys.argv[1:]
root = pathlib.Path(os.environ["FAKE_PROJECTS_ROOT"])
log = pathlib.Path(os.environ["FAKE_PROVIDER_LOG"])
if args[:2] == ["project", "activate"]:
    target = next((arg for arg in args[2:] if not arg.startswith("--")), "Host")
    project_root = root / target
    work = project_root / "work"
    environment_type = "none"
    environment_name = "none"
    if target.startswith("Conda"):
        environment_type = "conda"
        environment_name = target + "Env"
    elif target.startswith("Dev"):
        environment_type = "devcontainer"
    export_name = "EXPORT_" + target.upper()
    fields = {
        "WORKING_DIR": str(work),
        "WORKING_DIR_EXISTS": "True",
        "WORKING_DIR_CONFIGURED": "True",
        "GUIDANCE": "ready",
        "MESSAGE": "",
        "MESSAGE_CONFIGURED": "False",
        "EXPORT_COUNT": "1",
        "EXPORT_NAMES": export_name,
        "EXPORT_COMMANDS": f"export {export_name}={shlex.quote(target)}",
        "ENVIRONMENT_CONFIGURED": str(environment_type != "none"),
        "ENVIRONMENT_TYPE": environment_type,
        "ENVIRONMENT_NAME": environment_name,
        "ENVIRONMENT_CONFIG": "none",
        "ENVIRONMENT_PROVIDER": environment_type if environment_type != "none" else "host",
        "PROJECT_NAME": target,
        "PROJECT_ROOT": str(project_root),
        "LEGACY_SETUP_EXISTS": "False",
        "LEGACY_SETUP_PATH": "none",
        "LEGACY_SOURCING_ENABLED": "False",
        "LEGACY_TRUSTED": "False",
        "LEGACY_TRUST_STALE": "False",
    }
    print("# fake activation")
    for name, value in fields.items():
        print(f"TAURWORKS_ACTIVATION_{name}={shlex.quote(value)}")
    raise SystemExit(0)
if args[:2] in (["environment", "prepare"], ["environment", "enter"]):
    operation = args[1]
    target = pathlib.Path(args[2]).name
    with log.open("a", encoding="utf-8") as stream:
        stream.write(f"{operation}:{target}\\n")
    failure = os.environ.get("FAKE_FAIL_OPERATION")
    failure_target = os.environ.get("FAKE_FAIL_TARGET")
    raise SystemExit(9 if operation == failure and target == failure_target else 0)
raise SystemExit(2)
""",
            encoding="utf-8",
        )
        script.chmod(0o755)

    def _run_shell(self, body: str, *, failure_operation=None, failure_target=None):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            bin_dir = root / "bin"
            projects = root / "projects"
            log = root / "provider.log"
            bin_dir.mkdir()
            for name in ("Host", "CondaA", "CondaB", "DevA", "DevB", "DevFail"):
                (projects / name / "work").mkdir(parents=True)
            self._fake_taurworks(bin_dir)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                    "FAKE_PROJECTS_ROOT": str(projects),
                    "FAKE_PROVIDER_LOG": str(log),
                }
            )
            if failure_operation:
                env["FAKE_FAIL_OPERATION"] = failure_operation
                env["FAKE_FAIL_TARGET"] = failure_target
            result = subprocess.run(
                ["bash", "-c", body, "bash", str(SHELL_HELPER)],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            log_text = log.read_text(encoding="utf-8") if log.exists() else ""
            return result, log_text, projects

    def test_transition_matrix_clears_provider_and_project_state(self):
        body = r"""
conda() {
  if [ "$1" = "activate" ]; then
    export CONDA_DEFAULT_ENV="$2"
    return 0
  fi
  if [ "$1" = "deactivate" ]; then
    unset CONDA_DEFAULT_ENV
    return 0
  fi
  return 1
}
source "$1"
tw activate Host >/dev/null
printf 'host:%s:%s:%s\n' "$TAURWORKS_ACTIVE_PROJECT" "$TAURWORKS_ENVIRONMENT_TYPE" "${CONDA_DEFAULT_ENV-}"
tw activate CondaA >/dev/null
tw activate CondaB >/dev/null
printf 'conda:%s:%s:%s:%s\n' "$TAURWORKS_ACTIVE_PROJECT" "$TAURWORKS_ENVIRONMENT_TYPE" "$CONDA_DEFAULT_ENV" "${EXPORT_CONDAA-unset}"
tw activate DevA >/dev/null 2>/dev/null
printf 'dev:%s:%s:%s:%s\n' "$TAURWORKS_ACTIVE_PROJECT" "$TAURWORKS_ENVIRONMENT_TYPE" "${CONDA_DEFAULT_ENV-unset}" "${EXPORT_CONDAB-unset}"
tw activate Host >/dev/null
printf 'after-dev-host:%s:%s:%s\n' "$TAURWORKS_ACTIVE_PROJECT" "$TAURWORKS_ENVIRONMENT_TYPE" "${EXPORT_DEVA-unset}"
tw activate DevA >/dev/null 2>/dev/null
tw activate DevB >/dev/null 2>/dev/null
printf 'dev-dev:%s:%s:%s\n' "$TAURWORKS_ACTIVE_PROJECT" "$TAURWORKS_ENVIRONMENT_TYPE" "${EXPORT_DEVA-unset}"
"""
        result, log, _ = self._run_shell(body)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("host:Host:host:", result.stdout)
        self.assertIn("conda:CondaB:conda:CondaBEnv:unset", result.stdout)
        self.assertIn("dev:DevA:devcontainer:unset:unset", result.stdout)
        self.assertIn("after-dev-host:Host:host:unset", result.stdout)
        self.assertIn("dev-dev:DevB:devcontainer:unset", result.stdout)
        self.assertEqual(log.count("prepare:Dev"), 3)
        self.assertEqual(log.count("enter:Dev"), 3)

    def test_failed_prepare_or_entry_leaves_host_state_atomic(self):
        for operation in ("prepare", "enter"):
            with self.subTest(operation=operation):
                body = r"""
conda() {
  if [ "$1" = "activate" ]; then export CONDA_DEFAULT_ENV="$2"; return 0; fi
  if [ "$1" = "deactivate" ]; then unset CONDA_DEFAULT_ENV; return 0; fi
  return 1
}
source "$1"
tw activate CondaA >/dev/null
before_pwd=$(pwd)
if tw activate DevFail >/dev/null 2>/dev/null; then exit 88; fi
printf '%s:%s:%s:%s\n' "$TAURWORKS_ACTIVE_PROJECT" "$TAURWORKS_ENVIRONMENT_TYPE" "$CONDA_DEFAULT_ENV" "$before_pwd"
pwd
"""
                result, _, projects = self._run_shell(
                    body,
                    failure_operation=operation,
                    failure_target="DevFail",
                )

                self.assertEqual(result.returncode, 0, msg=result.stderr)
                lines = result.stdout.splitlines()
                self.assertEqual(
                    lines[-2],
                    f"CondaA:conda:CondaAEnv:{projects / 'CondaA' / 'work'}",
                )
                self.assertEqual(lines[-1], str(projects / "CondaA" / "work"))

    def test_nested_activation_is_rejected_before_resolution(self):
        result, log, _ = self._run_shell(
            'source "$1"; export TAURWORKS_EXECUTION_ENVIRONMENT=devcontainer; tw activate CondaA',
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("unsafe nested environment transition", result.stderr)
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
