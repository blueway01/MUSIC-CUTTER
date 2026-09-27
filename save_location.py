"""English implementation note."""

from pathlib import Path

from cut_storage import COMPLETE_FOLDER


def output_directory(app_directory: str | Path, mode: str, chosen_path: str = "") -> Path:
    """English implementation note."""
    if mode == "Default":
        return Path(app_directory).resolve() / COMPLETE_FOLDER
    if mode != "Custom folder":
        raise ValueError("Check the save location selection.")
    if not chosen_path.strip():
        raise ValueError("Choose a custom parent folder.")
    selected = Path(chosen_path).expanduser()
    if not selected.is_absolute():
        raise ValueError("Use an absolute path for the save location.")
    selected = selected.resolve()
    return selected if selected.name == COMPLETE_FOLDER else selected / COMPLETE_FOLDER
