# MUSIC CUTTER

MUSIC CUTTER is a local browser application for splitting audio into numbered MP3 files.

<img src="assets/music-cutter-icon.png" alt="MUSIC CUTTER icon" width="180">

## Workflow

1. Choose an MP3, WAV, or M4A source file.
2. Select manual or automatic splitting.
3. Review every range and title.
4. Choose the output location and save the tracks.
5. Reset the screen before starting another source file.

## Features

- English and Japanese interface switching, with English and Dark mode enabled by default.
- Manual time fields and a synchronized millisecond range slider.
- Automatic boundary detection based on silence, timbre, pitch, and rhythm changes.
- Consecutive track ranges and numbered filenames.
- Saved clip revision with start and end preview controls.
- Local work history and history-entry removal.
- Default or custom output location.
- Original source files remain unchanged.

## Run the Windows EXE

Double-click `MUSIC CUTTER.exe`. The required runtime and FFmpeg files are bundled into the EXE. Its command prompt starts minimized on the taskbar. Open that command prompt and press `Ctrl+C` to stop the application.

The default output directory is `MUSIC CUTTER CONVERT FILE` next to the EXE.

## Run from source

Install Python 3.10 and FFmpeg, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run MUSIC_CUTTER.py
```

You can also double-click `MUSIC CUTTER Starter Batch.bat` after installing the dependencies.

## Build the Windows EXE

```powershell
pip install -r requirements-dev.txt
.\build_windows.ps1
```

The completed files are written to `dist\MUSIC CUTTER.exe` and `dist\MUSIC CUTTER SHA256.txt`.

The included GitHub Actions workflow runs the unit tests, builds the Windows EXE, and uploads both completed files as a workflow artifact. The EXE is excluded from normal Git commits because it exceeds GitHub's regular single-file commit limit.

## Public hosting note

Local folder selection and Explorer integration operate on the computer running the application. A public server deployment would require browser downloads and isolated per-user processing instead of local path selection.
