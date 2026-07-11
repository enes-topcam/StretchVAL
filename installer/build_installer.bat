@echo off
REM StretchVAL kurulum (.exe) derleyici.
REM Once proje kokunde:  python build.py   (dist\StretchVAL.exe uretir)
REM Ayrica Inno Setup kurulu olmali: https://jrsoftware.org/isdl.php
cd /d "%~dp0"

if not exist "..\dist\StretchVAL.exe" (
  echo dist\StretchVAL.exe yok. Once proje kokunde: python build.py
  pause & exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Inno Setup bulunamadi. Kur: https://jrsoftware.org/isdl.php
  pause & exit /b 1
)

"%ISCC%" StretchVAL.iss
echo.
echo Tamamlandi -> dist\StretchVAL-Setup.exe
pause
