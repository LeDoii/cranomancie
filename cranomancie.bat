@echo off
setlocal
cd /d "%~dp0"
set "TRIED_INSTALL="

:detect
set "PY="
set "PYW="
rem Each candidate must really run: on a fresh Windows, "python" is often a Microsoft Store stub that does nothing.
call :try "py -3" "pyw -3"
if not defined PY call :try "python" "pythonw"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
  set "PYW="%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe""
)
if not defined PY goto :nopython

rem --- the only requirement is tkinter, which ships with Python (no pip install needed) ---
%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
  echo.
  echo Il manque un composant de Python : "tkinter".
  echo Reinstallez Python en cochant l'option "tcl/tk and IDLE", puis relancez cranomancie.bat.
  pause
  exit /b 1
)

start "" %PYW% app.py
exit /b 0

:try
%~1 -c "import sys" >nul 2>nul
if not errorlevel 1 (
  set "PY=%~1"
  set "PYW=%~2"
)
exit /b 0

:nopython
if defined TRIED_INSTALL (
  echo.
  echo Python a ete installe mais n'est pas encore detecte.
  echo Fermez cette fenetre puis relancez cranomancie.bat.
  pause
  exit /b 1
)
echo Python est introuvable.
winget --version >nul 2>nul
if errorlevel 1 (
  echo winget n'est pas disponible sur ce Windows.
  echo Installez Python 3.12 depuis https://www.python.org/downloads/ puis relancez cranomancie.bat.
  start "" https://www.python.org/downloads/
  pause
  exit /b 1
)
choice /m "Installer Python 3.12 avec winget"
if errorlevel 2 (
  echo Installez Python depuis https://www.python.org/downloads/ puis relancez cranomancie.bat.
  pause
  exit /b 1
)
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
set "TRIED_INSTALL=1"
goto :detect
