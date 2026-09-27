"""English implementation note."""

import numpy as np
from pydub import AudioSegment


SAMPLE_DTYPES = {1: np.int8, 2: np.int16, 4: np.int32}


def waveform_levels(audio: AudioSegment, points: int = 350) -> list[float]:
    """English implementation note."""
    if points < 1:
        raise ValueError("The waveform point count must be at least one.")
    dtype = SAMPLE_DTYPES.get(audio.sample_width)
    if dtype is None:
        raise ValueError("The audio sample width is not supported.")

    samples = np.frombuffer(audio.raw_data, dtype=dtype)
    frame_count = len(samples) // audio.channels
    if frame_count == 0:
        return [0.1] * points

    frames = samples[: frame_count * audio.channels].reshape(frame_count, audio.channels)
    positions = np.linspace(0, frame_count - 1, points * 32, dtype=np.int64)
    sampled = frames[positions].astype(np.float64)
    peaks = np.max(np.abs(sampled), axis=1).reshape(points, 32).max(axis=1)
    maximum = float(peaks.max())
    return (peaks / maximum).tolist() if maximum > 0 else [0.1] * points
