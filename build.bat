@echo off
REM Build script for SecurePass on Windows

REM Clean previous builds
rmdir /s /q dist
rmdir /s /q build

REM Install dependencies
python -m pip install --upgrade nuitka pyside6

REM Compile icon into .res file
REM windres app.rc -O coff -o app.res

REM Build with Nuitka
python -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-qt-plugins=sqldrivers,qml ^
    --include-data-dir=assets=assets ^
    --include-data-file=version.py=version.py ^
    --windows-icon-from-ico=icon.ico ^
    --output-dir=dist ^
    main.py

IF %ERRORLEVEL% NEQ 0 (
    echo Nuitka build failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Nuitka build complete!

REM Call Inno Setup to create the installer
echo Building installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" securepass.iss

IF %ERRORLEVEL% NEQ 0 (
    echo Inno Setup failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Installer created successfully!
