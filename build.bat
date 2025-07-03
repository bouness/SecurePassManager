@echo off
setlocal

REM === Clean previous build ===
rmdir /S /Q dist
rmdir /S /Q build

REM === Install dependencies ===
python -m pip install --upgrade nuitka pyside6

REM === Build with Nuitka ===
python -m nuitka ^
  --standalone ^
  --onefile ^
  --windows-disable-console ^
  --enable-plugin=pyside6 ^
  --include-qt-plugins=sqldrivers,qml ^
  --include-data-dir=assets=assets ^
  --include-data-file=version.py=version.py ^
  --output-dir=dist ^
  main.py

REM === Build installer with Inno Setup ===
if exist "installer_output" rmdir /S /Q installer_output
mkdir installer_output

"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\securepass.iss

echo.
echo Build complete! Outputs are in /dist and /installer_output
