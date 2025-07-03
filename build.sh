#!/bin/bash
# Build script for SecurePass (./build.sh)
set -e  # Exit immediately on error

# Clean build environment
rm -rf dist build || true

# Install dependencies
python -m pip install --upgrade nuitka pyside6

# Build with Nuitka
python -m nuitka \
    --standalone \
    --enable-plugin=pyside6 \
    --follow-imports \
    --assume-yes-for-downloads \
    --include-qt-plugins=sqldrivers,qml \
    --include-data-dir=src/assets=assets \
    --include-data-file=version.py=version.py \
    --output-dir=dist \
    src/main.py

# Set executable permissions
chmod +x dist/main.dist/main

echo "Build complete! Install with: sudo ./installer/install.sh"