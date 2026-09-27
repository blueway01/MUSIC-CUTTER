"""English implementation note."""

import tempfile
import unittest
from pathlib import Path

from pydub import AudioSegment

from cut_storage import clean_title, delete_history_entry, read_history, save_cuts


class CutStorageTests(unittest.TestCase):
    def test_save_two_ranges_and_continue_numbering(self):
        audio = AudioSegment.silent(duration=1800)
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            first = save_cuts(
                audio,
                [
                    {"start": 0.0, "end": 0.5, "title": "Intro"},
                    {"start": 0.5, "end": 1.0, "title": "Chorus"},
                ],
                "source.wav",
                output_dir,
            )
            second = save_cuts(
                audio,
                [{"start": 1.0, "end": 1.5, "title": "Intro"}],
                "source.wav",
                output_dir,
            )
            self.assertEqual([item["number"] for item in first + second], [1, 2, 3])
            self.assertEqual([item["title"] for item in read_history(output_dir)], ["Intro", "Chorus", "Intro"])
            self.assertTrue((output_dir / "0001_Intro.mp3").is_file())
            self.assertTrue((output_dir / "0002_Chorus.mp3").is_file())
            self.assertTrue((output_dir / "0003_Intro.mp3").is_file())
            self.assertGreater((output_dir / "0001_Intro.mp3").stat().st_size, 0)

    def test_invalid_title_and_range_do_not_create_output(self):
        audio = AudioSegment.silent(duration=1000)
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            with self.assertRaises(ValueError):
                save_cuts(audio, [{"start": 0, "end": 2, "title": "Long"}], "a.wav", output_dir)
            self.assertFalse(output_dir.exists())
            self.assertEqual(clean_title("../Track_Name"), "_Track_Name")
            with self.assertRaises(ValueError):
                clean_title("  ")

    def test_delete_history_keeps_audio_and_numbering(self):
        audio = AudioSegment.silent(duration=1000)
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            save_cuts(audio, [{"start": 0, "end": 0.5, "title": "Check"}], "a.wav", output_dir)
            self.assertTrue(delete_history_entry(output_dir, 1))
            self.assertEqual(read_history(output_dir), [])
            self.assertTrue((output_dir / "0001_Check.mp3").is_file())
            self.assertFalse(delete_history_entry(output_dir, 1))
            saved = save_cuts(audio, [{"start": 0.5, "end": 1, "title": "Next"}], "a.wav", output_dir)
            self.assertEqual(saved[0]["number"], 2)

    def test_song_order_remains_after_deleting_earlier_history(self):
        audio = AudioSegment.silent(duration=1000)
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            saved = save_cuts(
                audio,
                [
                    {"start": 0, "end": 0.5, "title": "Before", "track_order": 1},
                    {"start": 0.5, "end": 1, "title": "After", "track_order": 2},
                ],
                "source.wav",
                output_dir,
            )
            self.assertEqual([item["track_order"] for item in saved], [1, 2])
            self.assertTrue(delete_history_entry(output_dir, 1))
            self.assertEqual(read_history(output_dir)[0]["track_order"], 2)


if __name__ == "__main__":
    unittest.main()
