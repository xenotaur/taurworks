import importlib
import unittest


class SrcLayoutSmokeTest(unittest.TestCase):
    def test_import_taurworks(self):
        module = importlib.import_module("taurworks")
        self.assertIsNotNone(module)


if __name__ == "__main__":
    unittest.main()
