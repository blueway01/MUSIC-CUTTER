"""公開版の一時ファイル分離を確認する。"""

import unittest

from public_storage import reset_session_directory, session_directory


class PublicStorageTests(unittest.TestCase):
    def test_sessions_use_distinct_directories(self) -> None:
        first: dict = {}
        second: dict = {}
        try:
            first_path = session_directory(first)
            second_path = session_directory(second)
            self.assertNotEqual(first_path, second_path)
            self.assertEqual(session_directory(first), first_path)
            (first_path / "track.mp3").write_bytes(b"audio")
            self.assertFalse((second_path / "track.mp3").exists())
        finally:
            reset_session_directory(first)
            reset_session_directory(second)
        self.assertFalse(first_path.exists())
        self.assertFalse(second_path.exists())


if __name__ == "__main__":
    unittest.main()
