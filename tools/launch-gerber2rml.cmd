@echo off
REM ---------------------------------------------------------------------------
REM  Launch the gerber2rml GUI (Roland SRM-20 CAM tool).
REM  Double-click this file, or run  tools\launch-gerber2rml.cmd  from a shell.
REM  First run bootstraps a local venv in tools\srm-cam\.venv; later runs just
REM  open the app. The venv is gitignored, so each PC builds its own once.
REM ---------------------------------------------------------------------------
setlocal
set "ROOT=%~dp0srm-cam"
set "PY=%ROOT%\.venv\Scripts\python.exe"
set "PYW=%ROOT%\.venv\Scripts\pythonw.exe"

if not exist "%PY%" (
    echo [gerber2rml] First run - creating venv and installing dependencies...
    pushd "%ROOT%"
    py -m venv .venv || ( echo [gerber2rml] Could not create venv - is Python installed? & pause & exit /b 1 )
    ".venv\Scripts\python.exe" -m pip install -e ".[gui]" || ( echo [gerber2rml] Install failed. & pause & exit /b 1 )
    popd
)

REM pythonw.exe = no lingering console window. Run from the submodule so the
REM bundled examples\ (calibration coupon) resolve in File -> Open.
start "gerber2rml" /D "%ROOT%" "%PYW%" -m gerber2rml
endlocal
