#!/bin/bash
# securepass uninstaller

APP_NAME="securepass"
INSTALL_DIR="/opt/$APP_NAME"
BIN_PATH="/usr/local/bin/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"

# Check root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Remove installed files
rm -rf "$INSTALL_DIR"
rm -f "$BIN_PATH"
rm -f "$DESKTOP_FILE"

# Update desktop database
update-desktop-database /usr/share/applications

echo "=============================================="
echo "$APP_NAME completely uninstalled!"
echo "=============================================="