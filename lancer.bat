@echo off
setlocal
cd /d "%~dp0"

rem --- find Python (launcher "py" first, then "python") ---
set "PY="
set "PYW="
where py >nul 2>nul && (set "PY=py -3" & set "PYW=pyw -3")
if not defined PY where python >nul 2>nul && (set "PY=python" & set "PYW=pythonw")
if not defined PY goto :nopython

rem --- install missing requirements ---
%PY% -c "import PIL, tkinter" >nul 2>nul
if errorlevel 1 (
  echo Installation des dependances necessaires...
  %PY% -m pip install --disable-pip-version-check -r requirements.txt
  %PY% -c "import PIL, tkinter" >nul 2>nul
  if errorlevel 1 (
    echo.
    echo Il manque encore un composant : si "tkinter" est en cause, reinstallez Python
    echo en cochant l'option "tcl/tk and IDLE".
    pause
    exit /b 1
  )
)

start "" %PYW% app.py
exit /b 0

:nopython
echo Python est introuvable.
choice /m "Installer Python 3.12 avec winget"
if errorlevel 2 (
  echo Installez Python depuis https://www.python.org/downloads/ puis relancez lancer.bat.
  pause
  exit /b 1
)
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
echo.
echo Python est installe. Fermez cette fenetre et relancez lancer.bat.
pause
exit /b 0
