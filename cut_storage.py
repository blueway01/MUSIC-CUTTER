"""English implementation note."""

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path


COMPLETE_FOLDER = "MUSIC CUTTER CONVERT FILE"
HISTORY_FILE = "work_history.jsonl"
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
NUMBER_PREFIX = re.compile(r"^(\d{4,})_")


def clean_title(value):
    """English implementation note."""
    title = INVALID_CHARS.sub("_", value).strip(" .")[:80].rstrip(" .")
    if not title:
        raise ValueError("Enter a title.")
    if title.upper() in {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
    }:
        title += "_"
    return title


def read_history(output_dir):
    """English implementation note."""
    history_path = Path(output_dir) / HISTORY_FILE
    if not history_path.exists():
        return []
    with history_path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def delete_history_entry(output_dir, number):
    """English implementation note."""
    output_dir = Path(output_dir)
    history = read_history(output_dir)
    remaining = [item for item in history if int(item["number"]) != int(number)]
    if len(remaining) == len(history):
        return False
    history_path = output_dir / HISTORY_FILE
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output_dir, suffix=".jsonl", delete=False
        ) as stream:
            temporary = Path(stream.name)
            for item in remaining:
                stream.write(json.dumps(item, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, history_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def next_number(output_dir, history):
    """English implementation note."""
    used = [int(item["number"]) for item in history]
    for path in Path(output_dir).glob("*.mp3"):
        match = NUMBER_PREFIX.match(path.name)
        if match:
            used.append(int(match.group(1)))
    return max(used, default=0) + 1


def save_cuts(audio, ranges, source_name, output_dir):
    """English implementation note."""
    if not ranges:
        raise ValueError("Add at least one split range.")
    prepared = []
    for item in ranges:
        start = float(item["start"])
        end = float(item["end"])
        if not 0 <= start < end <= len(audio) / 1000:
            raise ValueError("A split range exceeds the audio duration.")
        song_order = item.get("track_order")
        if song_order is not None and (not isinstance(song_order, int) or song_order < 1):
            raise ValueError("Track order must be a positive integer.")
        prepared.append((start, end, clean_title(item["title"]), song_order))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    number = next_number(output_dir, read_history(output_dir))
    saved = []
    for start, end, title, song_order in prepared:
        while (output_dir / f"{number:04d}_{title}.mp3").exists():
            number += 1
        filename = f"{number:04d}_{title}.mp3"
        destination = output_dir / filename
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=output_dir, suffix=".mp3", delete=False) as stream:
                temporary = Path(stream.name)
            exported = audio[int(start * 1000):int(end * 1000)].export(
                str(temporary), format="mp3", bitrate="320k"
            )
            exported.close()
            os.replace(temporary, destination)
            temporary = None
            record = {
                "number": number,
                "title": title,
                "source_file": Path(source_name).name,
                "start_seconds": start,
                "end_seconds": end,
                "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "filename": filename,
            }
            if song_order is not None:
                record["track_order"] = song_order
            with (output_dir / HISTORY_FILE).open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            saved.append(record)
            number += 1
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return saved
