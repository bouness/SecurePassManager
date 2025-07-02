import os
from datetime import datetime, timedelta

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QIntValidator, QKeySequence
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                               QDialogButtonBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QProgressBar, QPushButton,
                               QSplitter, QStatusBar, QToolBar, QVBoxLayout,
                               QWidget)

from gui.about_dialog import AboutDialog
from gui.help_dialog import HelpDialog
from security.exporter import PasswordExporter
from security.importer import PasswordImporter
from utils import resource_path


class ImportDialog(QDialog):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle("Import Passwords")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # Format selection
        layout.addWidget(QLabel("Select import format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(
            [
                "LastPass (CSV)",
                "Bitwarden (JSON)",
                "1Password (1PUX)",
                "Chrome (CSV)",
                "Firefox (CSV)",
                "Generic JSON",
                "Generic CSV",
            ]
        )
        layout.addWidget(self.format_combo)

        # File selection
        layout.addWidget(QLabel("Select file to import:"))
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        layout.addWidget(self.file_path)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        layout.addWidget(browse_button)

        # Import button
        import_button = QPushButton("Import Passwords")
        import_button.clicked.connect(self.import_passwords)
        layout.addWidget(import_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select import file"""
        format_map = {
            "LastPass (CSV)": "CSV Files (*.csv)",
            "Bitwarden (JSON)": "JSON Files (*.json)",
            "1Password (1PUX)": "1PUX Files (*.1pux)",
            "Chrome (CSV)": "CSV Files (*.csv)",
            "Firefox (CSV)": "CSV Files (*.csv)",
            "Generic JSON": "JSON Files (*.json)",
            "Generic CSV": "CSV Files (*.csv)",
        }

        current_format = self.format_combo.currentText()
        file_filter = format_map.get(current_format, "All Files (*.*)")

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Import File", "", file_filter
        )

        if file_path:
            self.file_path.setText(file_path)

    def import_passwords(self):
        """Perform the import operation"""
        file_path = self.file_path.text()
        if not file_path:
            QMessageBox.warning(self, "Import Error", "Please select a file to import")
            return

        format_map = {
            "LastPass (CSV)": "lastpass",
            "Bitwarden (JSON)": "bitwarden",
            "1Password (1PUX)": "1password",
            "Chrome (CSV)": "chrome",
            "Firefox (CSV)": "firefox",
            "Generic JSON": "json",
            "Generic CSV": "csv",
        }

        format_type = format_map.get(self.format_combo.currentText())
        if not format_type:
            QMessageBox.critical(self, "Import Error", "Invalid import format selected")
            return

        importer = PasswordImporter(self.app_manager.crypto, self.app_manager.db)
        count = importer.import_passwords(file_path, format_type, self)

        if count is not False:
            self.status_label.setText(f"Successfully imported {count} passwords!")
            # Refresh UI
            self.parent().load_passwords()

            # Auto-close after success
            QTimer.singleShot(3000, self.accept)


class ExportDialog(QDialog):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle("Export Passwords")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        # Format selection
        layout.addWidget(QLabel("Select export format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "JSON"])
        layout.addWidget(self.format_combo)

        # File selection
        layout.addWidget(QLabel("Select export location:"))
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        layout.addWidget(self.file_path)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        layout.addWidget(browse_button)

        # Export button
        export_button = QPushButton("Export Passwords")
        export_button.clicked.connect(self.export_passwords)
        layout.addWidget(export_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select export location"""
        format_map = {"CSV": "CSV Files (*.csv)", "JSON": "JSON Files (*.json)"}

        current_format = self.format_combo.currentText()
        if current_format in format_map:
            file_filter, default_ext = format_map[current_format]
        else:
            file_filter = "All Files (*.*)"
            default_ext = ""

        # Suggest a default file name with extension
        default_name = (
            f"SecurePass_Export_{datetime.now().strftime('%Y%m%d')}{default_ext}"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Passwords", default_name, file_filter
        )

        if file_path:
            # Ensure the correct extension is added
            root, ext = os.path.splitext(file_path)
            if not ext or ext.lower() != default_ext.lower():
                file_path += default_ext
            self.file_path.setText(file_path)

    def export_passwords(self):
        """Perform the export operation"""
        file_path = self.file_path.text()
        if not file_path:
            QMessageBox.warning(
                self, "Export Error", "Please select an export location"
            )
            return

        format_type = self.format_combo.currentText().lower()

        exporter = PasswordExporter(self.app_manager.db)
        success = exporter.export_passwords(file_path, format_type, self)

        if success:
            self.status_label.setText("Passwords exported successfully!")
            # Auto-close after success
            QTimer.singleShot(3000, self.accept)


class ProxySettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proxy Settings")
        self.setFixedSize(400, 350)  # Increased height for new checkbox

        layout = QFormLayout(self)

        # Enable proxy checkbox
        self.enable_proxy = QCheckBox("Enable Proxy")
        layout.addRow(self.enable_proxy)

        # Proxy type
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["HTTP", "HTTPS", "SOCKS5"])
        layout.addRow("Proxy Type:", self.proxy_type)

        # Host and Port
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("proxy.example.com")
        layout.addRow("Host:", self.host_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("8080")
        self.port_input.setValidator(QIntValidator(1, 65535, self))
        layout.addRow("Port:", self.port_input)

        # Authentication
        self.auth_checkbox = QCheckBox("Requires Authentication")
        layout.addRow(self.auth_checkbox)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_input)

        # System-wide proxy checkbox
        self.system_wide_checkbox = QCheckBox(
            "Apply System-wide (Admin may be required)"
        )
        layout.addRow(self.system_wide_checkbox)

        # Info label
        self.info_label = QLabel(
            "Note: System-wide proxy requires admin privileges on some systems"
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addRow(self.info_label)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        # Load current settings
        self.load_settings()

        # Connect auth checkbox to enable/disable auth fields
        self.auth_checkbox.toggled.connect(self.toggle_auth_fields)
        self.toggle_auth_fields(self.auth_checkbox.isChecked())

        # Connect enable proxy to enable/disable all fields
        self.enable_proxy.toggled.connect(self.toggle_proxy_fields)
        self.toggle_proxy_fields(self.enable_proxy.isChecked())

    def toggle_auth_fields(self, checked):
        self.username_input.setEnabled(checked)
        self.password_input.setEnabled(checked)

    def toggle_proxy_fields(self, checked):
        self.proxy_type.setEnabled(checked)
        self.host_input.setEnabled(checked)
        self.port_input.setEnabled(checked)
        self.auth_checkbox.setEnabled(checked)
        self.system_wide_checkbox.setEnabled(checked)
        self.toggle_auth_fields(checked and self.auth_checkbox.isChecked())

    def load_settings(self):
        """Load settings from ProxyManager"""
        proxy_manager = self.parent().app_manager.proxy
        settings = proxy_manager.settings

        # Ensure boolean values are properly handled
        self.enable_proxy.setChecked(bool(settings["enabled"]))
        self.proxy_type.setCurrentText(settings["type"])
        self.host_input.setText(settings["host"])
        self.port_input.setText(settings["port"])
        self.auth_checkbox.setChecked(bool(settings["auth_enabled"]))
        self.username_input.setText(settings["username"])
        self.password_input.setText(settings["password"])
        self.system_wide_checkbox.setChecked(bool(settings["system_wide"]))

    def get_proxy_settings(self):
        """Return proxy settings as a dictionary"""
        return {
            "enabled": self.enable_proxy.isChecked(),
            "type": self.proxy_type.currentText(),
            "host": self.host_input.text().strip(),
            "port": self.port_input.text().strip(),
            "auth_enabled": self.auth_checkbox.isChecked(),
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
            "system_wide": self.system_wide_checkbox.isChecked(),
        }

    def accept(self):
        # Validate input
        if self.enable_proxy.isChecked():
            host = self.host_input.text().strip()
            port = self.port_input.text().strip()

            if not host:
                QMessageBox.warning(
                    self, "Invalid Input", "Host is required when proxy is enabled."
                )
                return

            if not port:
                QMessageBox.warning(self, "Invalid Input", "Port is required.")
                return

            if self.auth_checkbox.isChecked():
                username = self.username_input.text().strip()
                if not username:
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        "Username is required for authentication.",
                    )
                    return

        super().accept()

    def save_settings(self):
        settings = QSettings("SecurePass", "SecurePass Manager")
        settings.beginGroup("Proxy")
        settings.setValue("enabled", self.enable_proxy.isChecked())
        settings.setValue("type", self.proxy_type.currentText())
        settings.setValue("host", self.host_input.text().strip())
        settings.setValue("port", self.port_input.text().strip())
        settings.setValue("auth_enabled", self.auth_checkbox.isChecked())
        settings.setValue("username", self.username_input.text().strip())
        settings.setValue("password", self.password_input.text())
        settings.endGroup()


class MainWindow(QMainWindow):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.setWindowTitle("SecurePass Manager")
        self.setGeometry(100, 100, 900, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Left panel: Password list with search
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search passwords...")
        self.search_bar.textChanged.connect(self.filter_passwords)
        left_layout.addWidget(self.search_bar)

        # Password list
        self.password_list = QListWidget()
        self.password_list.itemSelectionChanged.connect(self.load_selected_password)

        # Enable double-click to edit
        self.password_list.itemDoubleClicked.connect(self.load_selected_password)
        left_layout.addWidget(self.password_list)

        # List buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add New")
        self.btn_add.clicked.connect(self.add_password)
        btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.edit_password)
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_password)
        btn_layout.addWidget(self.btn_delete)
        left_layout.addLayout(btn_layout)

        # Add category filter
        category_layout = QHBoxLayout()
        left_layout.addLayout(category_layout)

        category_layout.addWidget(QLabel("Filter by Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(
            [
                "Social",
                "Email",
                "Work",
                "Finance",
                "Shopping",
                "Gaming",
                "Streaming",
                "Developer",
                "Travel",
                "Health",
                "Government",
                "Miscellaneous",
            ]
        )
        self.category_filter.currentIndexChanged.connect(self.filter_passwords)
        category_layout.addWidget(self.category_filter)

        # Right panel: Password details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Password details group
        self.details_group = QGroupBox("Password Details")
        details_layout = QFormLayout(self.details_group)

        # Add category combo box
        self.category_combo = QComboBox()
        self.category_combo.addItems(
            [
                "Social",
                "Email",
                "Work",
                "Finance",
                "Shopping",
                "Gaming",
                "Streaming",
                "Developer",
                "Travel",
                "Health",
                "Government",
                "Miscellaneous",
            ]
        )
        details_layout.addRow("Category:", self.category_combo)

        self.service_input = QLineEdit()
        details_layout.addRow("Service:", self.service_input)

        self.username_input = QLineEdit()
        details_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        details_layout.addRow("Password:", self.password_input)

        # Password visibility toggle
        self.show_password = QPushButton("Show")
        self.show_password.setCheckable(True)
        self.show_password.toggled.connect(self.toggle_password_visibility)
        details_layout.addRow("", self.show_password)

        # URL field
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://")
        details_layout.addRow("URL:", self.url_input)

        # Notes field
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Additional information")
        details_layout.addRow("Notes:", self.notes_input)

        # Save button
        # self.btn_save = QPushButton("Save Changes")
        # self.btn_save.clicked.connect(self.save_password)
        # details_layout.addRow(self.btn_save)

        # Save/Cancel buttons
        btn_save_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.save_password)
        btn_save_layout.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.clear_form)
        btn_save_layout.addWidget(self.btn_cancel)
        details_layout.addRow(btn_save_layout)

        # Copy buttons
        copy_layout = QHBoxLayout()
        self.btn_copy_user = QPushButton("Copy Username")
        self.btn_copy_user.clicked.connect(self.copy_username)
        copy_layout.addWidget(self.btn_copy_user)

        self.btn_copy_pass = QPushButton("Copy Password")
        self.btn_copy_pass.clicked.connect(self.copy_password)
        copy_layout.addWidget(self.btn_copy_pass)
        details_layout.addRow(copy_layout)

        right_layout.addWidget(self.details_group)

        # Password strength meter
        self.strength_label = QLabel("Password Strength: -")
        right_layout.addWidget(self.strength_label)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])

        # Create toolbar
        self.create_toolbar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add database info to status bar
        self.db_info = QLabel()
        self.status_bar.addPermanentWidget(self.db_info)
        self.update_db_info()

        # Initialize UI state
        self.current_password = None
        self.clear_clipboard_timer = None
        self.load_passwords()

        # Add clipboard progress bar to status bar
        self.clipboard_progress = QProgressBar()
        self.clipboard_progress.setFixedWidth(200)
        self.clipboard_progress.setMinimum(0)
        self.clipboard_progress.setMaximum(30)  # 30 seconds
        self.clipboard_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.clipboard_progress)

        # Clipboard timer and progress
        self.clipboard_timer = QTimer()
        self.clipboard_timer.setInterval(1000)  # 1 second
        self.clipboard_timer.timeout.connect(self.update_clipboard_progress)
        self.clipboard_seconds_left = 0

        # Clipboard progress bar
        self.clipboard_progress = QProgressBar()
        self.clipboard_progress.setFixedWidth(200)
        self.clipboard_progress.setMinimum(0)
        self.clipboard_progress.setMaximum(30)
        self.clipboard_progress.setFormat("Clearing in %vs")
        self.clipboard_progress.setAlignment(Qt.AlignCenter)
        self.clipboard_progress.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                text-align: center;
                background: #333;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                width: 1px;
            }
        """
        )
        self.clipboard_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.clipboard_progress)

        # Allow service name editing
        # self.service_input.setEnabled(True)

        # Add backup status to status bar
        self.backup_status = QLabel()
        self.backup_status.setToolTip("Last backup status")
        self.status_bar.addPermanentWidget(self.backup_status)
        self.update_backup_status()

        # Connect backup signals
        if hasattr(self.app_manager, "backup_manager"):
            self.app_manager.backup_manager.backup_performed.connect(
                self.on_backup_performed
            )
            self.app_manager.backup_manager.backup_failed.connect(self.on_backup_failed)

    def update_backup_status(self):
        """Update backup status in status bar"""
        if (
            not hasattr(self.app_manager, "backup_manager")
            or not self.app_manager.backup_manager
        ):
            self.backup_status.setText("Backup: Not initialized")
            return

        if not self.app_manager.backup_manager.enabled:
            self.backup_status.setText("Backup: Disabled")
            return

        if not self.app_manager.backup_manager.last_backup:
            self.backup_status.setText("Backup: Never")
            return

        # Format time since last backup
        time_since = datetime.now() - self.app_manager.backup_manager.last_backup

        if time_since < timedelta(minutes=1):
            status = "Just now"
        elif time_since < timedelta(hours=1):
            mins = int(time_since.total_seconds() / 60)
            status = f"{mins} min ago"
        elif time_since < timedelta(days=1):
            hours = int(time_since.total_seconds() / 3600)
            status = f"{hours} hours ago"
        else:
            days = time_since.days
            status = f"{days} days ago"

        self.backup_status.setText(f"Backup: {status}")

    def on_backup_performed(self, backup_path):
        """Handle successful backup signal"""
        self.update_backup_status()
        self.status_bar.showMessage(
            f"Backup created: {os.path.basename(backup_path)}", 5000
        )

    def on_backup_failed(self, error):
        """Handle backup failure signal"""
        self.update_backup_status()
        self.status_bar.showMessage(f"Backup failed: {error}", 5000)

    def edit_password(self):
        """Edit selected password"""
        selected_items = self.password_list.selectedItems()
        if selected_items:
            self.load_selected_password()

    def update_db_info(self):
        """Update database information in status bar"""
        try:
            if (
                not hasattr(self.app_manager.db, "db_path")
                or not self.app_manager.db.db_path
            ):
                self.db_info.setText("Database: Not loaded")
                return

            db_path = self.app_manager.db.db_path
            db_name = os.path.basename(db_path)
            folder = os.path.dirname(db_path)

            # Get password count
            count = (
                len(self.app_manager.db.data)
                if hasattr(self.app_manager.db, "data")
                else 0
            )

            # Truncate folder path if too long
            if len(folder) > 30:
                folder = "..." + folder[-27:]

            self.db_info.setText(
                f"Database: {db_name} | Location: {folder} | Passwords: {count}"
            )
            self.db_info.setToolTip(f"Full Path: {db_path}")  # Show full path on hover

            # Also update backup manager's knowledge of the path
            if hasattr(self.app_manager, "backup_manager"):
                self.app_manager.logger.debug(
                    f"Updating backup manager with database path: {db_path}"
                )
        except Exception as e:
            self.logger.error(f"Error updating db info: {str(e)}")
            self.db_info.setText("Database info error")

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(48, 48))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        backup_icon = resource_path("assets/icons/backup.png")
        export_icon = resource_path("assets/icons/export.png")
        firewall_icon = resource_path("assets/icons/firewall.png")
        key_icon = resource_path("assets/icons/key.png")
        import_icon = resource_path("assets/icons/import.png")
        lock_icon = resource_path("assets/icons/lock.png")
        proxy_icon = resource_path("assets/icons/proxy.png")
        settings_icon = resource_path("assets/icons/settings.png")
        about_icon = resource_path("assets/icons/about.png")
        help_icon = resource_path("assets/icons/help.png")

        # Security actions
        lock_action = QAction(QIcon(lock_icon), "Lock Database", self)
        lock_action.triggered.connect(self.lock_database)
        toolbar.addAction(lock_action)
        toolbar.addSeparator()

        firewall_action = QAction(QIcon(firewall_icon), "Firewall Status", self)
        firewall_action.triggered.connect(self.show_firewall_status)
        toolbar.addAction(firewall_action)
        toolbar.addSeparator()

        proxy_action = QAction(QIcon(proxy_icon), "Proxy Settings", self)
        proxy_action.triggered.connect(self.configure_proxy)
        toolbar.addAction(proxy_action)
        toolbar.addSeparator()

        # Backup action
        backup_action = QAction(QIcon(backup_icon), "Backup Now", self)
        backup_action.triggered.connect(self.perform_backup_now)
        toolbar.addAction(backup_action)
        toolbar.addSeparator()

        # Password actions
        generate_action = QAction(QIcon(key_icon), "Generate Password", self)
        generate_action.triggered.connect(self.generate_password)
        toolbar.addAction(generate_action)
        toolbar.addSeparator()

        # Add import/export actions to the toolbar
        import_action = QAction(QIcon(import_icon), "Import", self)
        import_action.triggered.connect(self.show_import_dialog)
        toolbar.addAction(import_action)
        toolbar.addSeparator()

        export_action = QAction(QIcon(export_icon), "Export", self)
        export_action.triggered.connect(self.show_export_dialog)
        toolbar.addAction(export_action)
        toolbar.addSeparator()

        # Settings
        settings_action = QAction(QIcon(settings_icon), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        toolbar.addSeparator()

        # About
        about_action = QAction(QIcon(about_icon), "About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

        # Help
        help_action = QAction(QIcon(help_icon), "Help", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)

        # Set keyboard shortcuts
        lock_action.setShortcut(QKeySequence("Ctrl+L"))
        generate_action.setShortcut(QKeySequence("Ctrl+G"))

    def perform_backup_now(self):
        """Perform an immediate manual backup"""
        if (
            not hasattr(self.app_manager, "backup_manager")
            or not self.app_manager.backup_manager
        ):
            QMessageBox.warning(self, "Backup Error", "Backup manager not initialized")
            return

        # Get current backup settings
        backup_settings = {
            "enabled": self.app_manager.proxy.settings.get("Backup/enabled", False),
            "frequency": self.app_manager.proxy.settings.get(
                "Backup/frequency", "Daily"
            ),
            "location": self.app_manager.proxy.settings.get("Backup/location", ""),
        }

        # Validate location
        if not backup_settings["location"]:
            QMessageBox.warning(
                self,
                "Backup Error",
                "Backup location is not set. Please configure backup settings first.",
            )
            return

        # Update backup manager with current settings
        self.app_manager.backup_manager.update_settings(
            backup_settings["enabled"],
            backup_settings["frequency"],
            backup_settings["location"],
        )

        # Perform backup immediately
        try:
            backup_path = self.app_manager.backup_manager.perform_backup()
            if backup_path:
                QMessageBox.information(
                    self,
                    "Backup Successful",
                    f"Backup created successfully at:\n{backup_path}",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Backup Failed",
                    "Backup could not be created. Please check the logs.",
                )
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Error during backup: {str(e)}")

    def show_import_dialog(self):
        """Show the import dialog"""
        dialog = ImportDialog(self.app_manager, self)
        dialog.exec()

    def show_export_dialog(self):
        """Show the export dialog"""
        dialog = ExportDialog(self.app_manager, self)
        dialog.exec()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def save_database_as(self):
        """Save database to a new location"""
        current_path = self.app_manager.db.db_path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database As",
            current_path,
            "SecurePass Database (*.spdb);;All Files (*)",
        )

        if file_path:
            try:
                # Save current database to new location
                original_path = self.app_manager.db.db_path
                self.app_manager.db.db_path = file_path
                self.app_manager.db._save_data()

                # Update status
                self.update_db_info()
                self.status_bar.showMessage(f"Database saved to: {file_path}", 5000)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save database: {str(e)}"
                )
                # Revert to original path
                self.app_manager.db.db_path = original_path
            finally:
                # Refresh UI
                self.update_db_info()

    def is_clipboard_clear(self):
        """Check if clipboard is empty"""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        return text == ""

    def clear_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText("")  # Use setText instead of clear
        if self.clipboard_timer.isActive():
            self.clipboard_timer.stop()
            self.clipboard_progress.setVisible(False)
        self.copied_password = ""
        self.status_bar.showMessage("Clipboard manually cleared", 3000)

    def load_passwords(self):
        """Load all passwords into the list widget"""
        self.password_list.clear()

        # Check if database is loaded and has data
        if not hasattr(self.app_manager.db, "data") or not self.app_manager.db.data:
            self.status_bar.showMessage("Database is empty")
            self.update_db_info()
            return

        # Get all services from database
        services = list(self.app_manager.db.data.keys())
        services.sort(key=str.lower)

        for service in services:
            entry = self.app_manager.db.data[service]
            # Create a custom item with service and category
            item = QListWidgetItem()

            # Create a widget for better display
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 2, 5, 2)

            service_label = QLabel(service)
            service_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(service_label)

            category_label = QLabel(entry.get("category", "Other"))
            category_label.setStyleSheet("color: #888;")
            layout.addWidget(category_label)

            # Add username as tooltip
            username = entry.get("username", "")
            widget.setToolTip(f"Username: {username}" if username else service)

            self.password_list.addItem(item)
            self.password_list.setItemWidget(item, widget)
            item.setData(Qt.UserRole, service)

        self.update_db_info()
        self.status_bar.showMessage(f"Loaded {len(services)} passwords")
        self.filter_passwords()

    def filter_passwords(self):
        """Filter password list based on search text and category"""
        search_text = self.search_bar.text().lower()
        category_filter = self.category_filter.currentText()

        for i in range(self.password_list.count()):
            item = self.password_list.item(i)
            service = item.data(Qt.UserRole)
            entry = self.app_manager.db.get_password(service) or {}

            # Get category from entry
            category = entry.get("category", "Other")

            # Check filters
            category_match = (
                category_filter == "All Categories" or category_filter == category
            )

            # Search in service, username, and category
            username = entry.get("username", "").lower()
            text_match = (
                search_text in service.lower()
                or search_text in category.lower()
                or search_text in username
            )

            item.setHidden(not (category_match and text_match))

    def load_selected_password(self):
        """Load selected password details into form"""
        selected_items = self.password_list.selectedItems()
        if not selected_items:
            return

        service = selected_items[0].data(Qt.UserRole)
        self.current_service = service  # Store for updates

        entry = self.app_manager.db.get_password(service)
        if not entry:
            return

        self.service_input.setText(service)
        self.username_input.setText(entry.get("username", ""))
        self.password_input.setText(entry.get("password", ""))

        # Set category
        category = entry.get("category", "Other")
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        self.url_input.setText(entry.get("url", ""))
        self.notes_input.setText(entry.get("notes", ""))
        self.update_strength_indicator(entry.get("password", ""))

    def add_password(self):
        """Clear form for new password entry"""
        self.current_password = None
        self.service_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.url_input.clear()
        self.notes_input.clear()
        self.service_input.setEnabled(True)
        self.service_input.setFocus()
        self.status_bar.showMessage("Ready to add new password")

    def save_password(self):
        """Save current password to database"""
        new_service = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        category = self.category_combo.currentText()
        url = self.url_input.text().strip()
        notes = self.notes_input.text().strip()

        if not new_service:
            QMessageBox.warning(self, "Error", "Service name is required!")
            return

        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty!")
            return

        try:
            # Check if we're updating an existing entry
            if hasattr(self, "current_service") and self.current_service:
                self.app_manager.db.update_password(
                    self.current_service,
                    new_service,
                    username,
                    password,
                    category,
                    url,
                    notes,
                )
                self.status_bar.showMessage(
                    f"Password for {new_service} updated successfully"
                )
            else:
                # Add new password
                self.app_manager.db.add_password(
                    new_service, username, password, category, url, notes
                )
                self.status_bar.showMessage(
                    f"Password for {new_service} added successfully"
                )

            # Refresh the list
            self.load_passwords()

            # Select the updated/added item
            for i in range(self.password_list.count()):
                item = self.password_list.item(i)
                if item.data(Qt.UserRole) == new_service:
                    self.password_list.setCurrentItem(item)
                    break

            # Clear current service reference
            self.current_service = None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save password: {str(e)}")

    def delete_password(self):
        """Delete selected password"""
        selected_items = self.password_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No password selected!")
            return

        service = selected_items[0].data(Qt.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the password for {service}?",
            QMessageBox.Yes | QMessageBox.No,
        )

        self.update_db_info()

        if reply == QMessageBox.Yes:
            # Remove from database
            if service in self.app_manager.db.data:
                del self.app_manager.db.data[service]
                self.app_manager.db._save_data()
                self.load_passwords()
                self.clear_form()
                self.status_bar.showMessage(f"Password for {service} deleted")

    def clear_form(self):
        """Clear the password details form"""
        self.service_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.url_input.clear()
        self.notes_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.strength_label.setText("Password Strength: -")
        self.current_service = None
        self.password_list.clearSelection()

        # Enable service editing
        self.service_input.setEnabled(True)

        # Reset password visibility
        if self.show_password.isChecked():
            self.show_password.setChecked(False)

    def toggle_password_visibility(self, checked):
        """Toggle password visibility"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password.setText("Show")

    def copy_username(self):
        """Copy username to clipboard"""
        username = self.username_input.text()
        if username:
            QApplication.clipboard().setText(username)
            self.status_bar.showMessage("Username copied to clipboard", 3000)

            # Clear any existing password timer
            if self.clipboard_timer.isActive():
                self.clipboard_timer.stop()
                self.clipboard_progress.setVisible(False)

    def copy_password(self):
        """Copy password to clipboard with security measures"""
        password = self.password_input.text()
        if password:
            # Store the password we're copying
            self.copied_password = password

            # Set clipboard content
            clipboard = QApplication.clipboard()
            clipboard.setText(password)

            # Visual feedback
            self.btn_copy_pass.setStyleSheet("background-color: #4CAF50;")
            QTimer.singleShot(1000, lambda: self.btn_copy_pass.setStyleSheet(""))

            # Start clipboard countdown
            self.clipboard_seconds_left = 30
            self.clipboard_progress.setValue(30)
            self.clipboard_progress.setVisible(True)
            self.clipboard_progress.setFormat(
                f"Clearing in {self.clipboard_seconds_left}s"
            )
            self.status_bar.showMessage(
                "Password copied to clipboard - will clear in 30 seconds", 3000
            )

            # Start the timer
            self.clipboard_timer.start()

    def update_clipboard_progress(self):
        self.clipboard_seconds_left -= 1
        self.clipboard_progress.setValue(self.clipboard_seconds_left)
        self.clipboard_progress.setFormat(f"Clearing in {self.clipboard_seconds_left}s")
        if self.clipboard_seconds_left <= 0:
            self.clipboard_timer.stop()
            QApplication.clipboard().setText("")  # Overwrite instead of clear
            # self.clear_clipboard_system()  # optional fallback
            if not self.is_clipboard_clear():
                self.status_bar.showMessage("Clipboard clear failed!", 5000)
                self.app_manager.logger.debug("Clipboard clear verification failed")
            else:
                self.status_bar.showMessage("Clipboard cleared", 3000)
                # print("Clipboard cleared successfully")
            self.clipboard_progress.setVisible(False)
            self.copied_password = ""

    def generate_password(self):
        """Generate a strong random password"""
        import secrets
        import string

        # Generate 16-character password with letters, digits, and symbols
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = "".join(secrets.choice(alphabet) for i in range(16))

        self.password_input.setText(password)
        self.update_strength_indicator(password)
        self.status_bar.showMessage("Generated strong password")

    def update_strength_indicator(self, password):
        """Update password strength indicator"""
        if not password:
            self.strength_label.setText("Password Strength: -")
            return

        # Simple strength calculation
        strength = 0
        if len(password) >= 8:
            strength += 1
        if len(password) >= 12:
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in "!@#$%^&*()" for c in password):
            strength += 1

        # Map to strength levels
        levels = ["Very Weak", "Weak", "Moderate", "Good", "Strong", "Very Strong"]
        level = levels[min(strength, len(levels) - 1)] if strength > 0 else "Very Weak"

        # Set color based on strength
        colors = ["red", "orange", "#CCCC00", "green", "darkgreen", "blue"]
        color = colors[min(strength, len(colors) - 1)]

        self.strength_label.setText(
            f'Password Strength: <span style="color:{color}; font-weight:bold">{level}</span>'
        )

    def lock_database(self):
        """Lock the database and return to login screen"""
        # Clear clipboard and any active timers
        if self.clipboard_timer.isActive():
            self.clipboard_timer.stop()

        clipboard = QApplication.clipboard()
        clipboard.clear()
        self.clipboard_progress.setVisible(False)

        # Clear our reference
        self.copied_password = ""

        # Clear sensitive data
        self.clear_form()
        self.password_list.clear()

        # Create a new login window
        from gui.login import LoginWindow

        self.login_window = LoginWindow(self.app_manager)
        self.login_window.show()
        self.close()

    def show_firewall_status(self):
        """Display firewall status information"""
        status = "Active" if self.app_manager.firewall.is_active() else "Inactive"
        protection = (
            "Full system protection" if status == "Active" else "Limited protection"
        )

        message = (
            f"Firewall Status: {status}\n"
            f"Protection Level: {protection}\n\n"
            "Incoming connections are blocked when firewall is active."
        )

        QMessageBox.information(self, "Firewall Status", message)

    def configure_proxy(self):
        """Open proxy configuration dialog"""
        dialog = ProxySettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            proxy_settings = dialog.get_proxy_settings()

            # Ensure correct types before saving
            proxy_settings["enabled"] = bool(proxy_settings["enabled"])
            proxy_settings["auth_enabled"] = bool(proxy_settings["auth_enabled"])
            proxy_settings["system_wide"] = bool(proxy_settings["system_wide"])

            # Save and apply the new settings
            if self.app_manager.proxy.save_settings(proxy_settings):
                self.app_manager.proxy.settings = proxy_settings

                # Apply application-level proxy
                self.app_manager.proxy.set_application_proxy()

                # Apply system-wide proxy if requested
                if proxy_settings["system_wide"] and proxy_settings["enabled"]:
                    success = self.app_manager.proxy.set_system_proxy()
                    if not success:
                        QMessageBox.warning(
                            self,
                            "Proxy Error",
                            "Failed to set system-wide proxy. You may need administrator privileges.",
                        )

                status = "Enabled" if proxy_settings["enabled"] else "Disabled"
                scope = "system-wide" if proxy_settings["system_wide"] else "app-only"

                self.status_bar.showMessage(
                    f"Proxy settings updated: {status} ({scope}, {proxy_settings['type']} {proxy_settings['host']}:{proxy_settings['port']})",
                    5000,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Proxy Error",
                    "Failed to save proxy settings. Please check application logs.",
                )

    def open_settings(self):
        """Open application settings"""
        from gui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.app_manager, self)
        dialog.exec()

    def show_help(self):
        """Show help information"""
        # QMessageBox.information(self, "Help",
        # "SecurePass Manager Help\n\n"
        # "1. Add new passwords using the 'Add New' button\n"
        # "2. Select a password to view or edit its details\n"
        # "3. Use the copy buttons to copy credentials to clipboard\n"
        # "4. Generate strong passwords with Ctrl+G\n"
        # "5. Lock the database with Ctrl+L when leaving your computer")
        dialog = HelpDialog(self)
        dialog.exec()
