@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python scripts\scripts\fetch_meteo_openmeteo.py
