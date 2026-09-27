"""English implementation note."""

import math


def _dbfs(amplitude, maximum):
    if amplitude <= 0:
        return -120.0
    return round(20 * math.log10(amplitude / maximum), 1)


def check_edges(audio, start, end):
    """English implementation note."""
    start_ms = round(start * 1000)
    end_ms = round(end * 1000)
    if not 0 <= start_ms < end_ms <= len(audio):
        raise ValueError("Set the start and end positions within the audio duration.")
    cut = audio[start_ms:end_ms]
    channels = cut.channels
    samples = cut.get_array_of_samples()
    if not samples:
        raise ValueError("The selected range contains no audio samples.")
    window_ms = min(50, len(cut))
    maximum = cut.max_possible_amplitude
    result = {}
    for label, edge_samples, near in (
        ("start", samples[:channels], cut[:window_ms]),
        ("end", samples[-channels:], cut[-window_ms:]),
    ):
        instant = _dbfs(max(abs(value) for value in edge_samples), maximum)
        average = _dbfs(near.rms, maximum)
        result[label] = {
            "endpoint_dbfs": instant,
            "nearby_dbfs": average,
            "needs_review": instant > -30 or average > -35,
        }
    return result
