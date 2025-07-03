@echo off
REM Build script for SecurePass on Windows

REM Clean previous builds
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
rmdir /s /q installer_output 2>nul

REM Install application dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 exit /b %errorlevel%

REM Install build tool (Nuitka)
pip install nuitka
if %errorlevel% neq 0 exit /b %errorlevel%

REM Build with Nuitka
python -m nuitka ^
    --standalone ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-qt-plugins=sqldrivers,qml ^
    --include-data-dir=assets=assets ^
    --include-data-file=version.py=version.py ^
    --include-package=cryptography ^
    --include-module=cffi ^
    --include-module=pycparser ^
    --nofollow-import-to=*.tests ^
    --windows-icon-from-ico=icon.ico ^
    --output-dir=dist ^
    main.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo Nuitka build complete!

REM Verify cryptography was included
echo Verifying cryptography inclusion...
if not exist "dist\main.dist\cryptography" (
    echo Cryptography not bundled! Manually copying...
    for /f "delims=" %%i in ('python -c "import cryptography; print(cryptography.__path__[0])"') do (
        xcopy /E /I /Y "%%i" "dist\main.dist\cryptography"
    )
)

REM Call Inno Setup to create the installer
echo Building installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" securepass.iss
if %errorlevel% neq 0 exit /b %errorlevel%

echo Installer created successfully!

REM Create portable ZIP
echo Creating portable ZIP...
if not exist "dist\main.dist\" (
    echo Error: main.dist directory not found!
    exit /b 1
)
powershell -Command "Compress-Archive -Path 'dist\main.dist\*' -DestinationPath 'dist\SecurePass-Windows-Portable.zip' -Force"
if %errorlevel% neq 0 exit /b %errorlevel%

echo Build completed successfully!