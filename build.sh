#!/bin/bash
set -e

# === Clean previous builds ===
rm -rf dist build package
rm -f SecurePass-*-linux.tar.gz
mkdir -p dist

# === Install application dependencies ===
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# === Install build tool (Nuitka) ===
pip install nuitka

# === Build with Nuitka ===
python3 -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --follow-imports \
  --enable-plugin=pyside6 \
  --include-qt-plugins=sqldrivers,qml \
  --include-data-dir=assets=assets \
  --include-data-file=version.py=version.py \
  --include-package=cryptography \
  --include-module=cffi \
  --include-module=pycparser \
  --nofollow-import-to=*.tests \
  --output-dir=dist \
  main.py

# === Check and copy cryptography dependencies ===
echo "Verifying cryptography inclusion..."
if [ ! -d "dist/main.dist/cryptography" ]; then
  echo "Cryptography not bundled! Manually copying..."
  CRYPTO_PATH=$(python3 -c "import cryptography; print(cryptography.__path__[0])")
  cp -r "$CRYPTO_PATH" dist/main.dist/cryptography
fi

# === Make executable permissions ===
chmod +x dist/main.dist/main.bin

# === Get version ===
VERSION=$(python3 -c "from version import __version__; print(__version__)")

# === Prepare package directory ===
echo "Preparing package..."
mkdir -p package/SecurePass-$VERSION
cp -r dist/main.dist/* package/SecurePass-$VERSION/
cp -r assets package/SecurePass-$VERSION/ || true
cp version.py package/SecurePass-$VERSION/ || true
cp -r installer package/SecurePass-$VERSION/

# === Create tarball ===
echo "Creating distribution tarball..."
tar -czf SecurePass-$VERSION-linux.tar.gz -C package SecurePass-$VERSION

echo
echo "✅ Linux build complete!"
echo "Created: SecurePass-$VERSION-linux.tar.gz"
echo "To install:"
echo "  1. tar -xzf SecurePass-$VERSION-linux.tar.gz"
echo "  2. sudo ./SecurePass-$VERSION/installer/install.sh"
