@echo off
cd /d "%~dp0"
start "" /min cmd /k "python -m streamlit run MUSIC_CUTTER.py"
