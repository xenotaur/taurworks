import os
import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src"


def subprocess_env() -> dict[str, str]:
    """Build subprocess environment with src-layout import path."""
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH")
    source_value = str(SOURCE_ROOT)
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{source_value}{os.pathsep}{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = source_value
    return env
