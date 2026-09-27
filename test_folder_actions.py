"""English implementation note."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from folder_actions import open_folder, select_folder


class FolderActionsTests(unittest.TestCase):
    def test_missing_folder_is_created_and_opened(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "MUSIC CUTTER CONVERT FILE"
            with patch("folder_actions.os.startfile") as startfile:
                opened = open_folder(target)
            self.assertEqual(opened, target.resolve())
            self.assertTrue(target.is_dir())
            startfile.assert_called_once_with(str(target.resolve()))

    @patch("folder_actions.subprocess.run")
    def test_returns_selected_folder(self, run) -> None:
        run.return_value.stdout = "C:/Music/destination\n"

        self.assertEqual(select_folder("C:/Music"), "C:/Music/destination")
        args = run.call_args.args[0]
        self.assertEqual(args[:4], ["powershell.exe", "-NoProfile", "-STA", "-Command"])


if __name__ == "__main__":
    unittest.main()
