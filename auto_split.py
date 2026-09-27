"""English implementation note."""

import numpy as np


RATE = 8000
FRAME_SECONDS = 0.05
FRAME_SIZE = int(RATE * FRAME_SECONDS)
BAND_EDGES = np.array([50, 90, 150, 250, 400, 650, 1000, 1600, 2400, 3500, 4001])


def _cosine(left, right):
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0 and right_norm == 0:
        return 1.0
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _frame_dbfs(samples):
    count = len(samples) // FRAME_SIZE
    if count == 0:
        return np.array([], dtype=float)
    frames = samples[:count * FRAME_SIZE].reshape(count, FRAME_SIZE)
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))


def _signature(samples):
    """English implementation note."""
    window_size = 4096
    frequencies = np.fft.rfftfreq(window_size, 1 / RATE)
    bands = np.zeros(len(BAND_EDGES) - 1)
    chroma = np.zeros(12)
    frequency_mask = (frequencies >= 50) & (frequencies < 4000)
    valid_frequencies = frequencies[frequency_mask]
    band_index = np.searchsorted(BAND_EDGES, valid_frequencies, side="right") - 1
    note_index = np.rint(69 + 12 * np.log2(valid_frequencies / 440)).astype(int) % 12
    for offset in range(0, len(samples) - window_size + 1, window_size):
        piece = samples[offset:offset + window_size] * np.hanning(window_size)
        power = np.abs(np.fft.rfft(piece)) ** 2
        np.add.at(bands, band_index, power[frequency_mask])
        np.add.at(chroma, note_index, power[frequency_mask])
    if bands.sum():
        bands /= bands.sum()
    if chroma.sum():
        chroma /= chroma.sum()

    frame_levels = _frame_dbfs(samples)
    rhythm = np.zeros(32)
    if len(frame_levels) >= 80:
        loudness = np.maximum(frame_levels, -90)
        variation = loudness - np.mean(loudness)
        frequencies = np.fft.rfftfreq(len(variation), FRAME_SECONDS)
        spectrum = np.abs(np.fft.rfft(variation))
        selected = (frequencies >= 0.8) & (frequencies <= 4.0)
        if np.any(selected):
            rhythm = np.interp(np.linspace(0.8, 4.0, 32), frequencies[selected], spectrum[selected])
            if rhythm.sum():
                rhythm /= rhythm.sum()
    return bands, chroma, rhythm


def _accept_music_change(gap_length, similarities):
    """English implementation note."""
    strict_changes = sum(
        score < threshold
        for score, threshold in zip(similarities, (0.72, 0.8, 0.65))
    )
    long_gap_change = gap_length >= 1.5 and (
        similarities[0] < 0.85 or similarities[1] < 0.9
    )
    # Application workflow.
    short_gap_pitch_change = (
        gap_length >= 0.6
        and similarities[1] < 0.72
        and similarities[0] < 0.9
    )
    return strict_changes >= 2 or long_gap_change or short_gap_pitch_change


def _merge_quiet_runs(starts, ends, max_interruption_seconds=0.5):
    """English implementation note."""
    merged = []
    for start, end in zip(starts, ends):
        quiet_frames = int(end - start)
        if merged and (start - merged[-1][1]) * FRAME_SECONDS <= max_interruption_seconds:
            merged[-1][1] = int(end)
            merged[-1][2] += quiet_frames
        else:
            merged.append([int(start), int(end), quiet_frames])
    return merged


def _accept_compound_silence_reset(
    span_length,
    quiet_length,
    quiet_ratio,
    minimum_level,
    silence_limit,
    similarities,
):
    """English implementation note."""
    moderate_music_change = (
        similarities[0] < 0.93
        or similarities[1] < 0.88
        or similarities[2] < 0.85
    )
    return (
        0.6 <= span_length <= 1.2
        and quiet_length >= 0.5
        and quiet_ratio >= 0.6
        and minimum_level <= silence_limit - 5.0
        and moderate_music_change
    )


def _accept_soft_valley(
    span_length,
    quiet_length,
    quiet_ratio,
    minimum_level,
    quiet_limit,
    similarities,
):
    """English implementation note."""
    return (
        3.0 <= span_length <= 12.0
        and quiet_length >= 2.0
        and quiet_ratio >= 0.55
        and minimum_level <= quiet_limit - 3.0
        and similarities[0] < 0.82
        and similarities[1] < 0.85
    )


def find_song_boundaries(audio, min_song_seconds=45, min_gap_seconds=1.2):
    """English implementation note."""
    if min_song_seconds <= 0 or min_gap_seconds <= 0:
        raise ValueError("Analysis parameters must be positive.")
    mono = audio.set_channels(1).set_frame_rate(RATE)
    sample_dtype = {1: np.int8, 2: np.int16, 4: np.int32}[mono.sample_width]
    samples = np.frombuffer(mono.raw_data, dtype=sample_dtype).astype(np.float32)
    samples /= mono.max_possible_amplitude
    levels = _frame_dbfs(samples)
    if not len(levels):
        return []
    active_level = float(np.percentile(levels, 75))
    silence_limit = min(-38.0, active_level - 28.0)
    quiet = levels <= silence_limit
    changes = np.diff(np.concatenate(([False], quiet, [False])).astype(np.int8))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    candidates = _merge_quiet_runs(starts, ends)
    duration = len(audio) / 1000.0
    boundaries = []
    previous_boundary = 0.0

    for start_frame, end_frame, quiet_frames in candidates:
        gap_start = start_frame * FRAME_SECONDS
        gap_end = end_frame * FRAME_SECONDS
        span_length = gap_end - gap_start
        gap_length = quiet_frames * FRAME_SECONDS
        quiet_ratio = gap_length / span_length
        boundary = round((gap_start + gap_end) / 2, 3)
        if gap_length < min_gap_seconds:
            continue
        if boundary - previous_boundary < min_song_seconds or duration - boundary < min_song_seconds:
            continue
        left_start = max(0.0, gap_start - 21.0)
        left_end = max(left_start, gap_start - 0.3)
        right_start = min(duration, gap_end + 0.3)
        right_end = min(duration, gap_end + 21.0)
        left = samples[round(left_start * RATE):round(left_end * RATE)]
        right = samples[round(right_start * RATE):round(right_end * RATE)]
        if min(len(left), len(right)) < 4 * RATE:
            continue
        if np.mean(_frame_dbfs(left) > silence_limit + 8) < 0.7:
            continue
        if np.mean(_frame_dbfs(right) > silence_limit + 8) < 0.7:
            continue
        left_features = _signature(left)
        right_features = _signature(right)
        similarities = [_cosine(a, b) for a, b in zip(left_features, right_features)]
        candidate_levels = levels[start_frame:end_frame]
        compound_silence_reset = _accept_compound_silence_reset(
            span_length,
            gap_length,
            quiet_ratio,
            float(np.min(candidate_levels)),
            silence_limit,
            similarities,
        )
        # Application workflow.
        # Application workflow.
        # Application workflow.
        if not (_accept_music_change(gap_length, similarities) or compound_silence_reset):
            continue
        boundaries.append({
            "seconds": boundary,
            "silence_start_seconds": round(gap_start, 3),
            "silence_end_seconds": round(gap_end, 3),
            "silence_seconds": round(gap_length, 2),
            "timbre_similarity": round(similarities[0], 2),
            "pitch_similarity": round(similarities[1], 2),
            "rhythm_similarity": round(similarities[2], 2),
        })
        previous_boundary = boundary

    # Application workflow.
    soft_limit = silence_limit + 8.0
    soft_quiet = levels <= soft_limit
    soft_changes = np.diff(np.concatenate(([False], soft_quiet, [False])).astype(np.int8))
    soft_starts = np.flatnonzero(soft_changes == 1)
    soft_ends = np.flatnonzero(soft_changes == -1)
    soft_candidates = _merge_quiet_runs(soft_starts, soft_ends, max_interruption_seconds=1.0)
    for start_frame, end_frame, quiet_frames in soft_candidates:
        gap_start = start_frame * FRAME_SECONDS
        gap_end = end_frame * FRAME_SECONDS
        span_length = gap_end - gap_start
        quiet_length = quiet_frames * FRAME_SECONDS
        quiet_ratio = quiet_length / span_length
        if quiet_length < max(2.0, min_gap_seconds):
            continue
        if gap_start < min_song_seconds or duration - gap_end < min_song_seconds:
            continue
        candidate_levels = levels[start_frame:end_frame]
        minimum_offset = int(np.argmin(candidate_levels))
        boundary = round((start_frame + minimum_offset + 0.5) * FRAME_SECONDS, 3)
        if any(abs(boundary - item["seconds"]) < min_song_seconds for item in boundaries):
            continue
        left_start = max(0.0, gap_start - 18.0)
        left_end = max(left_start, gap_start - 1.0)
        right_start = min(duration, gap_end + 1.0)
        right_end = min(duration, gap_end + 18.0)
        left = samples[round(left_start * RATE):round(left_end * RATE)]
        right = samples[round(right_start * RATE):round(right_end * RATE)]
        if min(len(left), len(right)) < 4 * RATE:
            continue
        if np.mean(_frame_dbfs(left) > soft_limit) < 0.7:
            continue
        if np.mean(_frame_dbfs(right) > soft_limit) < 0.7:
            continue
        similarities = [_cosine(a, b) for a, b in zip(_signature(left), _signature(right))]
        if not _accept_soft_valley(
            span_length,
            quiet_length,
            quiet_ratio,
            float(np.min(candidate_levels)),
            soft_limit,
            similarities,
        ):
            continue
        boundaries.append({
            "seconds": boundary,
            "silence_start_seconds": round(gap_start, 3),
            "silence_end_seconds": round(gap_end, 3),
            "silence_seconds": round(quiet_length, 2),
            "timbre_similarity": round(similarities[0], 2),
            "pitch_similarity": round(similarities[1], 2),
            "rhythm_similarity": round(similarities[2], 2),
        })
    boundaries.sort(key=lambda item: item["seconds"])
    return boundaries


def make_ranges(duration, boundaries, title, min_song_seconds=1.0):
    """English implementation note."""
    points = [0.0] + sorted(float(value) for value in boundaries) + [duration]
    if any(end - start < min_song_seconds for start, end in zip(points, points[1:])):
        raise ValueError("A boundary creates a track shorter than the configured minimum.")
    return [
        {"start": start, "end": end, "title": f"{title}_{index:02d}"}
        for index, (start, end) in enumerate(zip(points, points[1:]), 1)
    ]
