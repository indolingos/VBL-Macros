@echo off
REM ============================================================
REM  VBL Macro — Qt/QML Liquid Glass Windows build
REM  Output exe: dist\VBL-Macro.exe
REM ============================================================

setlocal

python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller keyboard pydirectinput pillow PySide6

if not exist "app_icon.ico" (
    echo.
    echo [!] app_icon.ico not found in this folder.
    echo     Put your icon file here first, named exactly app_icon.ico
    pause
    exit /b 1
)

if not exist "LiquidGlass.qml" (
    echo.
    echo [!] LiquidGlass.qml not found in this folder.
    pause
    exit /b 1
)

if not exist "RobloxOverlay.qml" (
    echo.
    echo [!] RobloxOverlay.qml not found in this folder.
    pause
    exit /b 1
)

pyinstaller --noconfirm --onefile --windowed ^
    --name "VBL-Macro" ^
    --icon "app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    --add-data "icon_512.png;." ^
    --add-data "LiquidGlass.qml;." ^
    --add-data "RobloxOverlay.qml;." ^
    --hidden-import "keyboard._winkeyboard" ^
    --hidden-import "keyboard._winmouse" ^
    --collect-all "PySide6" ^
    key_macro_gui.py

echo.
echo ============================================================
echo Build complete: dist\VBL-Macro.exe
echo ============================================================
echo.
pause
