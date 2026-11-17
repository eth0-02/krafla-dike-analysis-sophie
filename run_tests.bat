@echo off
setlocal EnableExtensions
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv\Scripts\python.exe" (
    echo Run run_krafla_workflow.bat once first to create the environment.
    pause
    exit /b 2
)

call ".venv\Scripts\activate.bat"
set "PYTHONPATH=%PROJECT_DIR%src"
REM A project-local temporary directory avoids Windows permission issues in locked-down environments.
python -m pytest -p no:cacheprovider --basetemp ".test-artifacts"
pause
