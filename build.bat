@echo off
REM Build script for Motion Capture Analysis GUI

echo Building Motion Capture Analysis GUI...

REM Check if required files exist
if not exist "mocap_gui.py" (
    echo ERROR: mocap_gui.py not found!
    pause
    exit /b 1
)

if not exist "MocapApi.dll" (
    echo ERROR: MocapApi.dll not found!
    pause
    exit /b 1
)

if not exist "take003_chr01.bvh" (
    echo ERROR: take003_chr01.bvh not found!
    pause
    exit /b 1
)

REM Create dist and build directories if they don't exist
if not exist "dist" mkdir dist
if not exist "build" mkdir build

REM Build with PyInstaller
echo Building executable...
pyinstaller --onefile --windowed ^
    --add-binary "MocapApi.dll;." ^
    --add-data "take003_chr01.bvh;." ^
    --name "MocapAnalysis" ^
    --distpath "dist" ^
    --workpath "build" ^
    mocap_gui.py

if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo Build completed successfully!
echo Executable location: dist\MocapAnalysis.exe

REM Test the executable
echo.
set /p test="Do you want to test the executable now? (y/n): "
if /i "%test%"=="y" (
    echo Testing executable...
    start "" "dist\MocapAnalysis.exe"
)

pause

