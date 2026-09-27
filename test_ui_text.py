import unittest

from ui_text import translate


class UiTextTests(unittest.TestCase):
    def test_english_is_the_default_catalog(self) -> None:
        self.assertEqual("Language", translate("Language", "English"))

    def test_japanese_catalog_translates_and_formats_values(self) -> None:
        self.assertEqual("\u8868\u793a\u8a00\u8a9e", translate("Language", "Japanese"))
        self.assertEqual(
            "\u5207\u308a\u5206\u3051\u305f\u66f2\u6570\uff1a3\u66f2",
            translate("Split songs: {count}", "Japanese", count=3),
        )

    def test_missing_message_falls_back_to_english(self) -> None:
        self.assertEqual("Unknown message", translate("Unknown message", "Japanese"))


if __name__ == "__main__":
    unittest.main()
