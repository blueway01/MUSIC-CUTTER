"""English implementation note."""

import unittest

from pydub import AudioSegment
from pydub.generators import Sine

from auto_split import (
    _accept_compound_silence_reset,
    _accept_music_change,
    _accept_soft_valley,
    _merge_quiet_runs,
    find_song_boundaries,
    make_ranges,
)


def tone(frequency, seconds):
    return Sine(frequency).to_audio_segment(duration=int(seconds * 1000))


class AutoSplitTests(unittest.TestCase):
    def test_short_breath_does_not_split(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=500) + tone(1400, 6)
        self.assertEqual(find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=3), [])

    def test_long_pause_inside_same_tone_does_not_split(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=3500) + tone(440, 6)
        self.assertEqual(find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=3), [])

    def test_one_point_four_second_pause_with_same_tone_does_not_split(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=1400) + tone(440, 6)
        self.assertEqual(find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=1.2), [])

    def test_long_gap_and_distinct_music_creates_candidate(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=3500) + tone(1400, 6)
        boundaries = find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=3)
        self.assertEqual(len(boundaries), 1)
        self.assertTrue(6.0 < boundaries[0]["seconds"] < 9.5)
        ranges = make_ranges(len(audio) / 1000, [boundaries[0]["seconds"]], "Track", 4)
        self.assertEqual(ranges[0]["start"], 0.0)
        self.assertEqual(ranges[0]["end"], ranges[1]["start"])
        self.assertEqual(ranges[1]["end"], len(audio) / 1000)

    def test_one_point_four_second_gap_with_distinct_tone_creates_candidate(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=1400) + tone(1400, 6)
        boundaries = find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=1.2)
        self.assertEqual(len(boundaries), 1)

    def test_long_gap_with_same_pitch_class_and_changed_timbre_creates_candidate(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=2500) + tone(880, 6)
        boundaries = find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=0.1)
        self.assertEqual(len(boundaries), 1)

    def test_short_gap_with_only_one_feature_change_does_not_split(self):
        audio = tone(440, 6) + AudioSegment.silent(duration=500) + tone(880, 6)
        self.assertEqual(find_song_boundaries(audio, min_song_seconds=4, min_gap_seconds=0.1), [])

    def test_zero_point_seven_second_gap_with_pitch_and_timbre_change_is_accepted(self):
        self.assertTrue(_accept_music_change(0.7, (0.863, 0.674, 0.915)))

    def test_shorter_gap_with_same_features_is_rejected(self):
        self.assertFalse(_accept_music_change(0.4, (0.863, 0.674, 0.915)))

    def test_zero_point_seven_second_gap_without_timbre_support_is_rejected(self):
        self.assertFalse(_accept_music_change(0.7, (0.93, 0.674, 0.915)))

    def test_nearby_quiet_runs_are_merged(self):
        self.assertEqual(_merge_quiet_runs([100, 110], [104, 116]), [[100, 116, 10]])

    def test_compound_silence_with_music_change_is_accepted(self):
        self.assertTrue(
            _accept_compound_silence_reset(
                0.9, 0.55, 0.61, -48.38, -43.05, (0.811, 0.847, 0.887)
            )
        )

    def test_compound_silence_without_music_change_is_rejected(self):
        self.assertFalse(
            _accept_compound_silence_reset(
                0.9, 0.55, 0.61, -48.38, -43.05, (0.98, 0.98, 0.98)
            )
        )

    def test_shallow_compound_silence_is_rejected(self):
        self.assertFalse(
            _accept_compound_silence_reset(
                0.9, 0.55, 0.61, -45.0, -43.05, (0.811, 0.847, 0.887)
            )
        )

    def test_long_soft_valley_with_timbre_and_pitch_change_is_accepted(self):
        self.assertTrue(
            _accept_soft_valley(
                5.35, 3.25, 0.61, -39.0, -35.05, (0.785, 0.780, 0.909)
            )
        )

    def test_soft_valley_without_pitch_change_is_rejected(self):
        self.assertFalse(
            _accept_soft_valley(
                5.35, 3.25, 0.61, -39.0, -35.05, (0.785, 0.92, 0.80)
            )
        )

    def test_short_soft_valley_is_rejected(self):
        self.assertFalse(
            _accept_soft_valley(
                2.0, 1.5, 0.75, -39.0, -35.05, (0.70, 0.70, 0.70)
            )
        )

    def test_invalid_adjusted_boundary_is_rejected(self):
        with self.assertRaises(ValueError):
            make_ranges(20, [19], "Track", 4)


if __name__ == "__main__":
    unittest.main()
