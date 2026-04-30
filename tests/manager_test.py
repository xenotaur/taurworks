import pathlib
import tempfile
import unittest

from taurworks import manager


class ManagerModuleTest(unittest.TestCase):
    def test_camel_to_snake(self):
        self.assertEqual(manager.camel_to_snake("ProjectName"), "project_name")

    def test_get_directory_info_counts_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "a.txt").write_text("a", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.txt").write_text("bc", encoding="utf-8")
            size, count = manager.get_directory_info(str(root))
        self.assertEqual(count, 2)
        self.assertGreaterEqual(size, 3)


if __name__ == "__main__":
    unittest.main()
