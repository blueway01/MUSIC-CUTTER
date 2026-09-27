"""English implementation note."""

import unittest
from unittest.mock import patch

from pydub import AudioSegment

from waveform import waveform_levels


class WaveformTests(unittest.TestCase):
    def test_long_audio_does_not_expand_all_samples(self):
        audio = AudioSegment(
            data=bytes(16_000_000), sample_width=2, frame_rate=8000, channels=1
        )
        with patch.object(AudioSegment, "get_array_of_samples", side_effect=AssertionError):
            levels = waveform_levels(audio)
        self.assertEqual(len(levels), 350)
        self.assertEqual(set(levels), {0.1})

    def test_stereo_peaks_are_visible(self):
        audio = AudioSegment(
            data=b"\x00\x00\x00\x40" * 1000,
            sample_width=2,
            frame_rate=8000,
            channels=2,
        )
        levels = waveform_levels(audio)
        self.assertEqual(len(levels), 350)
        self.assertEqual(set(levels), {1.0})


if __name__ == "__main__":
    unittest.main()
