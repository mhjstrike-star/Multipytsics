@echo off
setlocal DisableDelayedExpansion
set "NUMBA_CACHE_DIR=%~dp0_numba_cache"
set "OPENBLAS_NUM_THREADS=1"
set "OMP_NUM_THREADS=1"
set "PYTHONIOENCODING=utf-8"

set "TOOLBOX_DIR="
if not exist "%~dp0toolbox_path.txt" goto :invalid_toolbox
set /p "TOOLBOX_DIR="<"%~dp0toolbox_path.txt"
if not defined TOOLBOX_DIR goto :invalid_toolbox
set "TOOLBOX_DIR=%TOOLBOX_DIR:"=%"
if not defined TOOLBOX_DIR goto :invalid_toolbox

pushd "%~dp0" || goto :invalid_toolbox
for %%P in ("%TOOLBOX_DIR%\python.exe") do set "DEMO_PYTHON=%%~fP"
popd
if not exist "%DEMO_PYTHON%" goto :invalid_toolbox
"%DEMO_PYTHON%" -B -c "import importlib.util as u; import sys; sys.exit(not all(u.find_spec(name) for name in ('AMR', 'PySide6', 'IMM', 'aGO', 'numpy')))" >nul 2>&1
if errorlevel 1 goto :invalid_toolbox

if /I "%~1"=="--smoke" (
    "%DEMO_PYTHON%" -B -u "%~dp0amr_demo.py" --smoke
    exit /b
)
start "AMR Demo Console" /min "%DEMO_PYTHON%" -B -u "%~dp0amr_demo.py"
exit /b

:invalid_toolbox
echo Check "%~dp0toolbox_path.txt".
echo The first line must contain the PIAnO ToolBox folder with python.exe, AMR, and PySide6.
if /I not "%~1"=="--smoke" pause
exit /b 1
