#!/bin/bash
set -e

# === Clean previous builds ===
rm -rf dist build package
mkdir -p dist

# === Install dependencies ===
python3 -m pip install --upgrade nuitka pyside6

# === Build with Nuitka ===
python3 -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --follow-imports \
  --enable-plugin=pyside6 \
  --include-qt-plugins=sqldrivers,qml \
  --include-data-dir=assets=assets \
  --include-data-file=version.py=version.py \
  --output-dir=dist \
  main.py

# === Make executable permissions ===
chmod +x dist/main.dist/main.bin

echo
echo "✅ Linux build complete!"
echo "Run with: ./dist/main.dist/main.bin"
echo "Install with: sudo ./installer/install.sh"
