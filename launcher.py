"""English implementation note."""

import os
import sys
from pathlib import Path


def _bundle_directory() -> Path:
    """English implementation note."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)).resolve()


def _application_directory() -> Path:
    """English implementation note."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main() -> int:
    bundle_dir = _bundle_directory()
    app_dir = _application_directory()
    ffmpeg_dir = bundle_dir / "ffmpeg"

    os.environ["MUSIC_CUTTER_APP_DIR"] = str(app_dir)
    os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    sys.path.insert(0, str(bundle_dir))

    script = bundle_dir / "MUSIC_CUTTER.py"
    headless = os.environ.get("MUSIC_CUTTER_HEADLESS", "0") == "1"
    original_options = sys.argv[1:]
    sys.argv = [
        "streamlit",
        "run",
        str(script),
        f"--server.headless={'true' if headless else 'false'}",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
        *original_options,
    ]

    from streamlit.web import cli as streamlit_cli

    return int(streamlit_cli.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
