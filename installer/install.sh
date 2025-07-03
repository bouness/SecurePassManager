#!/bin/bash
# securepass installer

APP_NAME="securepass"
VERSION="1.0.0"
INSTALL_DIR="/opt/$APP_NAME"
BIN_PATH="/usr/local/bin/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"

# Check root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Create installation directory
mkdir -p "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo "Failed to create installation directory"
    exit 1
fi

# Copy application files
cp -r dist/main.dist/* "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo "Failed to copy application files"
    exit 1
fi

# Create executable symlink
ln -sf "$INSTALL_DIR/main" "$BIN_PATH"
if [ $? -ne 0 ]; then
    echo "Failed to create binary symlink"
    exit 1
fi

# Install desktop entry
cp "installer/$APP_NAME.desktop" "$DESKTOP_FILE"
if [ $? -ne 0 ]; then
    echo "Failed to install desktop entry"
    exit 1
fi

# Create proper launcher script
cat > "$INSTALL_DIR/$APP_NAME" <<EOL
#!/bin/sh
exec "$INSTALL_DIR/main.bin" "\$@"
EOL

# Make launcher executable
chmod +x "$INSTALL_DIR/$APP_NAME"

# Create symlink to launcher
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_PATH"

# Update desktop database
update-desktop-database /usr/share/applications

echo "=============================================="
echo "$APP_NAME $VERSION installed successfully!"
echo "Run command: $APP_NAME"
echo "Find in your application menu: SecurePass"
echo "=============================================="