import importlib
import pathlib
import subprocess
import sys
import unittest


class SrcLayoutSmokeTest(unittest.TestCase):
    def test_import_taurworks(self):
        module = importlib.import_module("taurworks")
        self.assertIsNotNone(module)
        self.assertIsNotNone(module.__file__)

        module_path = pathlib.Path(module.__file__).resolve()
        expected_package_dir = (
            pathlib.Path(__file__).resolve().parents[1] / "src" / "taurworks"
        ).resolve()

        self.assertTrue(
            expected_package_dir == module_path.parent
            or expected_package_dir in module_path.parents,
            f"Expected taurworks to be imported from {expected_package_dir}, got {module_path}",
        )

    def test_module_cli_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "taurworks.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Manage taurworks projects.", result.stdout)


if __name__ == "__main__":
    unittest.main()
