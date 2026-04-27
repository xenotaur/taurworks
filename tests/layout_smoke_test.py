import importlib
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class SrcLayoutSmokeTest(unittest.TestCase):
    def test_import_taurworks(self):
        module = importlib.import_module("taurworks")
        self.assertIsNotNone(module)


if __name__ == "__main__":
    unittest.main()
