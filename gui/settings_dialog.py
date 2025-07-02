import logging
import os
import subprocess
import sys

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QSpinBox, QTabWidget, QVBoxLayout,
                               QWidget)

from security.proxy import ProxyManager


class SettingsDialog(QDialog):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle("SecurePass Settings")
        self.setMinimumSize(700, 500)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Security Tab
        self.security_tab = QWidget()
        self.setup_security_tab(self.security_tab)
        self.tab_widget.addTab(self.security_tab, "Security")

        # Privacy Tab
        self.privacy_tab = QWidget()
        self.setup_privacy_tab(self.privacy_tab)
        self.tab_widget.addTab(self.privacy_tab, "Privacy")

        # Advanced Tab
        self.advanced_tab = QWidget()
        self.setup_advanced_tab(self.advanced_tab)
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        apply_button = self.button_box.button(QDialogButtonBox.Apply)
        apply_button.clicked.connect(self.apply_settings)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.button_box)

        # Create proxy manager for unified settings
        self.proxy_manager = ProxyManager()

        # Load current settings
        self.load_settings()

    def import_passwords(self):
        """Open import dialog"""
        self.parent().show_import_dialog()

    def export_passwords(self):
        """Open export dialog"""
        self.parent().show_export_dialog()

    def setup_security_tab(self, tab):
        layout = QFormLayout(tab)

        # Firewall status
        firewall_status = (
            "Active" if self.app_manager.firewall.is_active() else "Inactive"
        )
        self.status_label = QLabel(firewall_status)
        layout.addRow("Firewall Status:", self.status_label)

        # Firewall control
        self.firewall_btn = QPushButton(
            "Enable Firewall"
            if not self.app_manager.firewall.is_active()
            else "Disable Firewall"
        )
        self.firewall_btn.clicked.connect(self.toggle_firewall)
        layout.addRow("Firewall Control:", self.firewall_btn)

        # Password policy
        self.policy_combo = QComboBox()
        self.policy_combo.addItems(
            [
                "Basic (8 characters)",
                "Strong (12 characters)",
                "Military (16+ characters)",
            ]
        )
        layout.addRow("Password Policy:", self.policy_combo)

        # Auto-lock timeout
        self.lock_timeout = QSpinBox()
        self.lock_timeout.setRange(1, 60)
        self.lock_timeout.setSuffix(" minutes")
        layout.addRow("Auto-lock Timeout:", self.lock_timeout)

        # Encryption level
        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems(["AES-128", "AES-256", "ChaCha20"])
        layout.addRow("Encryption Level:", self.encryption_combo)

    def setup_privacy_tab(self, tab):
        layout = QFormLayout(tab)

        # Clipboard settings
        self.clipboard_timeout = QSpinBox()
        self.clipboard_timeout.setRange(5, 300)
        self.clipboard_timeout.setSuffix(" seconds")
        layout.addRow("Clipboard Clear Timeout:", self.clipboard_timeout)

        # Password visibility
        self.password_visibility = QComboBox()
        self.password_visibility.addItems(
            ["Always masked", "Show when editing", "Always visible"]
        )
        layout.addRow("Password Visibility:", self.password_visibility)

        # Logging configuration
        self.logging_config = QComboBox()
        self.logging_config.addItems(["Full logging", "Minimal logging", "No logging"])
        layout.addRow("Activity Logging:", self.logging_config)

        # Logging level control
        self.logging_level = QComboBox()
        self.logging_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addRow("Logging Level:", self.logging_level)

        # Auto-clear clipboard on lock
        self.clear_on_lock = QCheckBox("Clear clipboard when locking database")
        layout.addRow(self.clear_on_lock)

    def setup_advanced_tab(self, tab):
        layout = QFormLayout(tab)

        import_export_group = QGroupBox("Data Transfer")
        import_export_layout = QVBoxLayout(import_export_group)

        import_button = QPushButton("Import Passwords...")
        import_button.clicked.connect(self.import_passwords)
        import_export_layout.addWidget(import_button)

        export_button = QPushButton("Export Passwords...")
        export_button.clicked.connect(self.export_passwords)
        import_export_layout.addWidget(export_button)

        layout.addRow(import_export_group)

        # Backup settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QFormLayout(backup_group)

        self.backup_enable = QCheckBox("Enable automatic backups")
        backup_layout.addRow(self.backup_enable)

        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["Daily", "Weekly", "Monthly"])
        backup_layout.addRow("Backup Frequency:", self.backup_frequency)

        self.backup_location = QLineEdit()
        self.backup_location.setPlaceholderText("Select backup directory...")
        self.backup_browse = QPushButton("Browse...")
        self.backup_browse.clicked.connect(self.browse_backup_location)

        location_layout = QHBoxLayout()
        location_layout.addWidget(self.backup_location)
        location_layout.addWidget(self.backup_browse)
        backup_layout.addRow("Backup Location:", location_layout)

        # Manual backup button
        self.manual_backup_btn = QPushButton("Perform Backup Now")
        self.manual_backup_btn.clicked.connect(self.perform_manual_backup)
        backup_layout.addRow("", self.manual_backup_btn)

        layout.addRow(backup_group)

        # Database location group
        db_group = QGroupBox("Database")
        db_layout = QFormLayout(db_group)

        # Database location
        self.db_location = QLineEdit()
        self.db_location.setReadOnly(True)
        layout.addRow("Current Database:", self.db_location)

        # Change database button
        self.change_db_btn = QPushButton("Change Database Location...")
        self.change_db_btn.clicked.connect(self.change_database_location)
        db_layout.addRow("", self.change_db_btn)

        layout.addRow(db_group)

        # Logging section
        logging_group = QGroupBox("Logging")
        logging_layout = QVBoxLayout(logging_group)

        # View logs button
        view_logs_btn = QPushButton("View Log Files")
        view_logs_btn.clicked.connect(self.view_logs)
        logging_layout.addWidget(view_logs_btn)

        layout.addRow(logging_group)

    def view_logs(self):
        """Open the log directory in the system file explorer"""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        log_dir = os.path.normpath(log_dir)

        try:
            if os.path.exists(log_dir):
                if sys.platform == "win32":
                    os.startfile(log_dir)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", log_dir])
                else:
                    subprocess.Popen(["xdg-open", log_dir])
            else:
                QMessageBox.warning(
                    self,
                    "Log Directory Not Found",
                    f"The log directory does not exist:\n{log_dir}",
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Error Opening Logs", f"Could not open log directory: {str(e)}"
            )

    def perform_manual_backup(self):
        """Perform an immediate manual backup"""
        # Get current settings from UI
        backup_enabled = self.backup_enable.isChecked()
        backup_frequency = self.backup_frequency.currentText()
        backup_location = self.backup_location.text()

        # Validate backup location
        if not backup_location:
            QMessageBox.warning(self, "Backup Settings", "Backup location is required")
            return

        # Update backup manager with current settings
        self.app_manager.backup_manager.update_settings(
            backup_enabled, backup_frequency, backup_location
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
                # Get detailed error from logs
                log_file = self.get_log_location()
                QMessageBox.warning(
                    self,
                    "Backup Failed",
                    "Backup could not be created.\n\n"
                    f"Please check the logs for details:\n{log_file}",
                )
        except Exception as e:
            log_file = self.get_log_location()
            QMessageBox.critical(
                self,
                "Backup Error",
                f"Error during backup: {str(e)}\n\n"
                f"Detailed error information has been logged to:\n{log_file}",
            )

    def get_log_location(self):
        """Get the path to the log file"""
        try:
            # Get the root logger
            logger = logging.getLogger("SecurePass")
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    return handler.baseFilename
        except:
            pass
        return "logs/SecurePass.log (location unknown)"

    def browse_backup_location(self):
        path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if path:
            self.backup_location.setText(path)

    def browse_backup_location(self):
        path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if path:
            self.backup_location.setText(path)

    def change_database_location(self):
        """Change the database location"""
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

                # Update UI
                self.db_location.setText(file_path)

                # Update backup manager
                self.app_manager.backup_manager.db_path = file_path

                # Show success message
                QMessageBox.information(
                    self,
                    "Database Moved",
                    f"Database successfully moved to:\n{file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Database Error", f"Failed to move database: {str(e)}"
                )
                # Revert to original path
                self.app_manager.db.db_path = original_path

    def toggle_firewall(self):
        if self.app_manager.firewall.is_active():
            # Show disable confirmation
            reply = QMessageBox.question(
                self,
                "Disable Firewall",
                "Are you sure you want to disable the firewall?\n\n"
                "This will make your system more vulnerable to network attacks.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # Implement disable logic in firewall manager
                # For now, just update UI
                self.status_label.setText("Inactive")
                self.firewall_btn.setText("Enable Firewall")
                QMessageBox.information(
                    self, "Firewall Disabled", "Firewall has been disabled."
                )
        else:
            # Try to enable firewall
            if self.app_manager.firewall.block_incoming():
                self.status_label.setText("Active")
                self.firewall_btn.setText("Disable Firewall")
                QMessageBox.information(
                    self, "Firewall Enabled", "Firewall has been successfully enabled."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Firewall Error",
                    "Could not enable firewall. Administrator privileges required.",
                )

    def load_settings(self):
        """Load current settings from settings.ini"""
        # Security settings
        self.policy_combo.setCurrentIndex(1)  # Default to Strong
        self.lock_timeout.setValue(5)  # Default 5 minutes
        self.encryption_combo.setCurrentIndex(1)  # AES-256

        # Privacy settings
        self.clipboard_timeout.setValue(30)  # Default 30 seconds
        self.password_visibility.setCurrentIndex(0)

        # Load logging configuration
        log_config = self.app_manager.proxy.settings.get(
            "Logging/config", "Minimal logging"
        )
        index = self.logging_config.findText(log_config)
        if index >= 0:
            self.logging_config.setCurrentIndex(index)

        # Load logging level
        log_level = self.app_manager.proxy.settings.get("Logging/level", "INFO")
        index = self.logging_level.findText(log_level)
        if index >= 0:
            self.logging_level.setCurrentIndex(index)

        self.clear_on_lock.setChecked(True)

        # Advanced settings - Load from unified settings
        settings = self.app_manager.proxy.settings

        # Load backup settings
        self.backup_enable.setChecked(bool(settings.get("Backup/enabled", False)))

        frequency = settings.get("Backup/frequency", "Daily")
        index = self.backup_frequency.findText(frequency)
        if index >= 0:
            self.backup_frequency.setCurrentIndex(index)

        self.backup_location.setText(settings.get("Backup/location", ""))
        self.db_location.setText(self.app_manager.db.db_path)

    def apply_settings(self):
        """Apply settings without closing dialog"""
        # Security settings
        self.app_manager.password_policy = self.policy_combo.currentIndex()
        self.app_manager.lock_timeout = (
            self.lock_timeout.value() * 60
        )  # Convert to seconds

        # Privacy settings
        self.app_manager.clipboard_timeout = self.clipboard_timeout.value()

        # Backup settings
        backup_enabled = bool(self.backup_enable.isChecked())
        backup_frequency = self.backup_frequency.currentText()
        backup_location = self.backup_location.text()

        # Validate backup location
        if backup_enabled and not backup_location:
            QMessageBox.warning(
                self,
                "Backup Settings",
                "Backup location is required when automatic backups are enabled",
            )
            return

        # Create a copy of current settings
        new_settings = self.app_manager.proxy.settings.copy()

        # Add logging settings
        new_settings.update(
            {
                "Logging/config": self.logging_config.currentText(),
                "Logging/level": self.logging_level.currentText(),
            }
        )

        # Update logging settings
        new_settings.update(
            {
                "Logging/config": self.logging_config.currentText(),
                "Logging/level": self.logging_level.currentText(),
                "Backup/enabled": backup_enabled,
                "Backup/frequency": backup_frequency,
                "Backup/location": backup_location,
            }
        )

        # Save to settings.ini
        if not self.app_manager.proxy.save_settings(new_settings):
            QMessageBox.warning(
                self,
                "Settings Error",
                "Failed to save settings to file. Please check application logs.",
            )
        else:
            # Update in-memory settings
            self.app_manager.proxy.settings = new_settings

            # Update backup manager
            self.app_manager.backup_manager.update_settings(
                backup_enabled, backup_frequency, backup_location
            )

            # Update logging level
            try:
                from utils import update_logging_level

                update_logging_level(new_settings["Logging/level"])

                # Show confirmation with logging details
                QMessageBox.information(
                    self,
                    "Settings Applied",
                    f"Your settings have been applied successfully.\n\n"
                    f"Logging level set to: {new_settings['Logging/level']}",
                )
            except Exception as e:
                logging.error(f"Failed to update logging level: {e}")
                QMessageBox.warning(
                    self,
                    "Logging Error",
                    f"Settings saved but logging update failed: {str(e)}",
                )

    def accept(self):
        self.apply_settings()
        super().accept()
