@echo off
REM Uygulamayi kaynaktan calistirir (gelistirme icin).
cd /d "%~dp0"
python -m pip install -r requirements.txt >nul 2>&1
python main.py
