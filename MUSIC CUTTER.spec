import os
import shutil
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


project = Path(SPECPATH)
configured_ffmpeg = os.environ.get("FFMPEG_BIN_DIR")
ffmpeg_executable = shutil.which("ffmpeg")
ffprobe_executable = shutil.which("ffprobe")
if configured_ffmpeg:
    ffmpeg_bin = Path(configured_ffmpeg)
elif ffmpeg_executable and ffprobe_executable:
    ffmpeg_bin = Path(ffmpeg_executable).resolve().parent
else:
    raise RuntimeError("FFmpeg was not found. Set FFMPEG_BIN_DIR to its bin directory.")

streamlit_datas = collect_data_files("streamlit")
streamlit_hiddenimports = collect_submodules("streamlit")
app_files = [
    "MUSIC_CUTTER.py",
    "auto_split.py",
    "clip_editor.py",
    "cut_storage.py",
    "folder_actions.py",
    "save_location.py",
    "ui_text.py",
    "ui_theme.py",
    "waveform.py",
]
datas = (
    streamlit_datas
    + copy_metadata("streamlit")
    + [(str(project / name), ".") for name in app_files]
    + [(str(project / "assets"), "assets")]
    + [(str(project / "locales"), "locales")]
)
binaries = [
    (str(path), "ffmpeg")
    for path in ffmpeg_bin.iterdir()
    if path.suffix.lower() == ".dll" or path.name.lower() in {"ffmpeg.exe", "ffprobe.exe"}
]
hiddenimports = streamlit_hiddenimports + [
    "numpy",
    "pydub",
    "pydub.audio_segment",
    "streamlit.web.cli",
]

a = Analysis(
    [str(project / "launcher.py")],
    pathex=[str(project)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "playwright",
        "scipy",
        "sklearn",
        "sympy",
        "tensorflow",
        "tkinter",
        "torch",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MUSIC CUTTER",
    icon=str(project / "assets" / "music-cutter.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    hide_console="minimize-early",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
