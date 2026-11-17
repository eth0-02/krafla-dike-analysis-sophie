@echo off
setlocal EnableExtensions

REM Krafla data workflow launcher for Windows.
REM Use it by dragging an .xlsx file onto this script, or run:
REM run_krafla_workflow.bat "C:\path\to\workbook.xlsx"

set "INPUT_FILE=%~1"
set "PROJECT_DIR=%~dp0"

if "%INPUT_FILE%"=="" (
    echo.
    echo No Excel workbook was supplied.
    echo Drag a workbook onto this file, or run:
    echo   run_krafla_workflow.bat "C:\path\to\Krafla_1975_1984_dike_data.xlsx"
    echo.
    pause
    exit /b 2
)

if not exist "%INPUT_FILE%" (
    echo.
    echo Input file was not found:
    echo   "%INPUT_FILE%"
    echo.
    pause
    exit /b 2
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul
    if not %ERRORLEVEL% EQU 0 (
        echo.
        echo Python 3 was not found. Install Python 3.10 or newer from python.org,
        echo and select "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 3
    )
    set "PYTHON=python"
)

cd /d "%PROJECT_DIR%"

REM Create an isolated environment only once. This avoids changing system Python.
if not exist ".venv\Scripts\python.exe" (
    echo Creating an isolated Python environment...
    %PYTHON% -m venv .venv
    if not %ERRORLEVEL% EQU 0 goto :failed
)

call ".venv\Scripts\activate.bat"
echo Installing/checking required libraries...
python -m pip install --disable-pip-version-check -r requirements.txt
if not %ERRORLEVEL% EQU 0 goto :failed

REM PYTHONPATH lets Python find the source code without requiring a package install.
set "PYTHONPATH=%PROJECT_DIR%src"
echo.
echo Running the Krafla workflow...
python -m krafla_workflow --input "%INPUT_FILE%" --output "%PROJECT_DIR%outputs"
if not %ERRORLEVEL% EQU 0 goto :failed

echo.
echo Finished successfully. Open the newest folder under:
echo   %PROJECT_DIR%outputs
echo.
pause
exit /b 0

:failed
echo.
echo The workflow stopped because of the error shown above.
echo Check the input workbook and try again. If installation failed, check your
echo internet connection and confirm that Python 3.10 or newer is installed.
echo.
pause
exit /b 1
