"""English implementation note."""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from cut_storage import HISTORY_FILE, clean_title, next_number, read_history


def list_saved_clips(output_dir: str | Path) -> list[Path]:
    """English implementation note."""
    root = Path(output_dir).resolve()
    if not root.is_dir():
        return []
    return sorted(
        (path for path in root.rglob("*.mp3") if path.is_file()),
        key=lambda path: str(path.relative_to(root)).casefold(),
    )


def clip_duration(path: str | Path) -> float:
    """English implementation note."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def preview_segment(path: str | Path, start: float, end: float) -> bytes:
    """English implementation note."""
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
            "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout


def save_revised_clip(
    output_dir: str | Path,
    source: str | Path,
    start: float,
    end: float,
    title: str,
) -> dict:
    """English implementation note."""
    root = Path(output_dir).resolve()
    original = Path(source).resolve()
    if not original.is_relative_to(root) or original.suffix.lower() != ".mp3" or not original.is_file():
        raise ValueError("Select an MP3 inside the save folder.")
    duration = clip_duration(original)
    start = round(float(start), 3)
    end = round(float(end), 3)
    if not 0 <= start < end <= duration:
        raise ValueError("Set the start and end positions within the file duration.")
    title = clean_title(title)
    number = next_number(root, read_history(root))
    while (root / f"{number:04d}_{title}.mp3").exists():
        number += 1
    destination = root / f"{number:04d}_{title}.mp3"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, suffix=".mp3", delete=False) as stream:
            temporary = Path(stream.name)
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(original), "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
                "-map", "0:a:0", "-vn", "-codec:a", "libmp3lame", "-b:a", "320k",
                str(temporary),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if temporary.stat().st_size == 0:
            raise ValueError("The revised audio is empty.")
        os.replace(temporary, destination)
        temporary = None
        record = {
            "number": number,
            "title": title,
            "source_file": original.name,
            "start_seconds": start,
            "end_seconds": end,
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "filename": destination.name,
            "operation": "clip_revision",
            "revision_source": str(original.relative_to(root)),
        }
        with (root / HISTORY_FILE).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return record
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
