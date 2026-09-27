$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDirectory

$ffmpegCommand = Get-Command ffmpeg -ErrorAction Stop
$ffprobeCommand = Get-Command ffprobe -ErrorAction Stop
if ((Split-Path -Parent $ffmpegCommand.Source) -ne (Split-Path -Parent $ffprobeCommand.Source)) {
    throw "Place ffmpeg.exe and ffprobe.exe in the same directory."
}

$env:FFMPEG_BIN_DIR = Split-Path -Parent $ffmpegCommand.Source
python -m unittest test_auto_split test_clip_editor test_cut_review test_cut_storage test_folder_actions test_save_location test_waveform
python -m PyInstaller --noconfirm "MUSIC CUTTER.spec"

$hash = (Get-FileHash -LiteralPath "dist\MUSIC CUTTER.exe" -Algorithm SHA256).Hash
Set-Content -LiteralPath "dist\MUSIC CUTTER SHA256.txt" -Value $hash -Encoding ascii
Write-Host "Completed: dist\MUSIC CUTTER.exe"
Write-Host "SHA256: $hash"
