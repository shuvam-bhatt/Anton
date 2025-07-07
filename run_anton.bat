@echo off
echo Starting Anton AI Assistant...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python app.py
pause