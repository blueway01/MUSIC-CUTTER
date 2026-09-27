"""English implementation note."""

import tempfile
import unittest
from pathlib import Path

from save_location import output_directory


class SaveLocationTests(unittest.TestCase):
    def test_default_and_custom_base(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "app"
            other = Path(directory) / "other-location"
            self.assertEqual(output_directory(app, "Default"), app / "MUSIC CUTTER CONVERT FILE")
            self.assertEqual(output_directory(app, "Custom folder", str(other)), other / "MUSIC CUTTER CONVERT FILE")

    def test_selecting_completed_folder_does_not_nest_it(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            self.assertEqual(output_directory(directory, "Custom folder", str(completed)), completed)

    def test_missing_or_relative_custom_path_is_rejected(self):
        for path in ("", "relative/path"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                output_directory(Path.cwd(), "Custom folder", path)


if __name__ == "__main__":
    unittest.main()
