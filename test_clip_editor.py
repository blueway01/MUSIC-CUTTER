"""English implementation note."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from pydub.generators import Sine

from clip_editor import clip_duration, list_saved_clips, preview_segment, save_revised_clip
from cut_storage import read_history


class ClipEditorTests(unittest.TestCase):
    def test_nested_clip_is_revised_without_changing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            nested = root / "001"
            nested.mkdir(parents=True)
            original = nested / "001_Source Track.mp3"
            Sine(440).to_audio_segment(duration=2200).export(original, format="mp3").close()
            before = hashlib.sha256(original.read_bytes()).digest()

            self.assertEqual(list_saved_clips(root), [original])
            self.assertGreater(len(preview_segment(original, 0.2, 0.6)), 1000)
            record = save_revised_clip(root, original, 0.2, 1.2, "Revised Track")

            revised = root / record["filename"]
            self.assertEqual(record["number"], 1)
            self.assertEqual(record["operation"], "clip_revision")
            self.assertEqual(record["revision_source"], str(original.relative_to(root)))
            self.assertTrue(revised.is_file())
            self.assertAlmostEqual(clip_duration(revised), 1.0, delta=0.15)
            self.assertEqual(hashlib.sha256(original.read_bytes()).digest(), before)
            self.assertEqual(read_history(root), [record])

    def test_rejects_source_outside_save_folder_and_invalid_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "MUSIC CUTTER CONVERT FILE"
            root.mkdir()
            outside = Path(directory) / "outside.mp3"
            Sine(440).to_audio_segment(duration=1000).export(outside, format="mp3").close()
            with self.assertRaises(ValueError):
                save_revised_clip(root, outside, 0, 0.5, "Rejected")
            with self.assertRaises(ValueError):
                save_revised_clip(root, root / "missing.mp3", 0, 0.5, "Rejected")
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
