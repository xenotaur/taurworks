import pathlib
import tempfile
import unittest

from helpers import assert_same_path, normalize_path, parse_cli_fields


class TestHelpersTest(unittest.TestCase):
    def test_assert_same_path_accepts_equivalent_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            target = root / "target"
            target.mkdir()
            nested_reference = root / "target" / ".." / "target"

            self.assertEqual(normalize_path(target), normalize_path(nested_reference))
            assert_same_path(self, nested_reference, target)

    def test_parse_cli_fields_reads_bulleted_and_plain_diagnostics(self):
        output = "\n".join(
            [
                "Taurworks diagnostics",
                "- project_root: /tmp/example/project",
                "resolved_working_dir: /tmp/example/project/repo",
                "mutation_performed: False",
            ]
        )

        fields = parse_cli_fields(output)

        self.assertEqual("/tmp/example/project", fields["project_root"])
        self.assertEqual("/tmp/example/project/repo", fields["resolved_working_dir"])
        self.assertEqual("False", fields["mutation_performed"])
