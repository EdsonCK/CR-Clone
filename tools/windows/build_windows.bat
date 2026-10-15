@echo off
rem ==========================================================================
rem  Build the Windows version yourself (only needed if you change the code -
rem  the ready-made zip already contains ClashClone.exe).
rem
rem  Needs Python 3.11 64-bit from python.org (tick "Add python.exe to PATH").
rem  Double-click this file, or run it from a Command Prompt.
rem  Result: dist\ClashClone\ClashClone.exe  (zip the whole dist\ClashClone
rem  folder to share it).
rem ==========================================================================
cd /d "%~dp0..\.."
python -m pip install --upgrade "pygame==2.6.1" "pyinstaller==6.10.0" || goto :fail
python -m PyInstaller --noconfirm --clean --distpath dist --workpath build tools\windows\ClashClone.spec || goto :fail
echo.
echo Done: dist\ClashClone\ClashClone.exe
pause
exit /b 0
:fail
echo.
echo Build FAILED - see the messages above.
pause
exit /b 1
