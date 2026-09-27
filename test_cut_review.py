"""English implementation note."""

import unittest

from pydub import AudioSegment
from pydub.generators import Sine

from cut_review import check_edges


class CutReviewTests(unittest.TestCase):
    def test_silence_has_no_loud_edge(self):
        report = check_edges(AudioSegment.silent(duration=1000), 0.2, 0.8)
        self.assertFalse(report["start"]["needs_review"])
        self.assertFalse(report["end"]["needs_review"])

    def test_tone_at_edges_needs_listening(self):
        report = check_edges(Sine(440).to_audio_segment(duration=1000), 0.2, 0.8)
        self.assertTrue(report["start"]["needs_review"])
        self.assertTrue(report["end"]["needs_review"])

    def test_invalid_range_is_rejected(self):
        with self.assertRaises(ValueError):
            check_edges(AudioSegment.silent(duration=1000), 0.8, 0.2)


if __name__ == "__main__":
    unittest.main()
