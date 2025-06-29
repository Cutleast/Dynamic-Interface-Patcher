@echo off
call compile_qrc.bat
uv run scripts\build.py
