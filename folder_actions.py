"""English implementation note."""

import os
import subprocess
from pathlib import Path


def open_folder(path: str | Path) -> Path:
    """English implementation note."""
    folder = Path(path).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    os.startfile(str(folder))
    return folder


def select_folder(initial_directory: str | Path) -> str:
    """English implementation note."""
    initial = str(Path(initial_directory).resolve()).replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$OutputEncoding=[Text.UTF8Encoding]::new();"
        "$dialog=New-Object System.Windows.Forms.FolderBrowserDialog;"
        f"$dialog.SelectedPath='{initial}';"
        "if($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){"
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
        "[Console]::Write($dialog.SelectedPath)}"
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-STA", "-Command", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        creationflags=flags,
    )
    return result.stdout.strip()
