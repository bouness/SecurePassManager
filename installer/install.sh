#!/bin/bash
# securepass installer for compiled release

set -e

APP_NAME="SecurePass"
INSTALL_DIR="/opt/$APP_NAME"
BIN_PATH="/usr/local/bin/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
ICON_PATH="$INSTALL_DIR/assets/icon.png"

# Check root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy application files from current directory
echo "Copying application files..."
cp -r ./* "$INSTALL_DIR" || true

# Remove installer directory from installation
rm -rf "$INSTALL_DIR/installer"

# Create executable symlink
echo "Creating executable symlink..."
ln -sf "$INSTALL_DIR/main.bin" "$BIN_PATH"

# Create desktop entry
echo "Creating desktop entry..."
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=SecurePass
Comment=Password Manager Application
Exec=$BIN_PATH
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;Security;
Keywords=password;security;manager;
StartupWMClass=SecurePass
EOL

# Fix icon path in the desktop file if needed
sed -i "s|/opt/securepass/assets/icon.png|$ICON_PATH|g" "$DESKTOP_FILE"

# Update desktop database
echo "Updating desktop database..."
update-desktop-database /usr/share/applications || true

echo "=============================================="
echo "$APP_NAME installed successfully!"
echo "Installation directory: $INSTALL_DIR"
echo "Run command: $APP_NAME"
echo "Find in your application menu: SecurePass"
echo "=============================================="
