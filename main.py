import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

from gui.login import LoginWindow
from security.backup_manager import BackupManager
from security.crypto import CryptoManager
from security.database import SecureDatabase
from utils import resource_path, setup_logging, update_logging_level, get_config_path


class PasswordManagerApp:
    def __init__(self):
        # Setup logging first
        self.logger = setup_logging("SecurePass", log_level="INFO")
        self.logger.info("Application starting")

        self.config_path = get_config_path()
        self.settings = {}
        self.load_settings() # Now logger is available

        self.logger.debug(f"Initial settings: {self.settings}")

        self.qt_app = QApplication(sys.argv)
        self.qt_app.aboutToQuit.connect(self.on_exit)

        # Initialize components
        self.crypto = CryptoManager()

        # Initialize database without path - will be set later
        self.db = SecureDatabase(self.crypto, db_path=None)

        # Initialize backup manager (only once)
        self.backup_manager = BackupManager(self)
        self.logger.info("Backup manager initialized")

        # Set clipboard timeout default
        self.clipboard_timeout = 30

    def load_settings(self):
        """Load settings from config file using cross-platform location"""
        self.logger.debug(f"Loading settings from: {self.config_path}")
        settings = QSettings(str(self.config_path), QSettings.IniFormat)

        # Create settings dictionary with defaults and proper types
        self.settings = {
            "Backup/enabled": False,
            "Backup/frequency": "Daily",
            "Backup/location": "",
            "Logging/config": "Minimal logging",
            "Logging/level": "INFO",
        }

        try:
            # Load backup settings with type conversion
            settings.beginGroup("Backup")
            self.settings["Backup/enabled"] = settings.value(
                "enabled", False, type=bool
            )
            self.settings["Backup/frequency"] = settings.value(
                "frequency", "Daily", type=str
            )
            self.settings["Backup/location"] = settings.value("location", "", type=str)
            settings.endGroup()

            # Load logging settings
            settings.beginGroup("Logging")
            self.settings["Logging/config"] = settings.value(
                "config", "Minimal logging", type=str
            )
            log_level = settings.value("level", "INFO", type=str)
            if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                self.settings["Logging/level"] = log_level
            else:
                self.settings["Logging/level"] = "INFO"  # Enforce valid value
            settings.endGroup()

            self.logger.debug(f"Loaded settings: {self.settings}")

        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")

        return self.settings

    def save_settings(self, settings=None):
        """Save settings to config file using cross-platform location"""
        if settings is None:
            settings = self.settings

        self.logger.debug(f"Saving settings to: {self.config_path}")

        try:
            qsettings = QSettings(str(self.config_path), QSettings.IniFormat)

            # Save backup settings
            qsettings.beginGroup("Backup")
            qsettings.setValue("enabled", settings.get("Backup/enabled", False))
            qsettings.setValue("frequency", settings.get("Backup/frequency", "Daily"))
            qsettings.setValue("location", settings.get("Backup/location", ""))
            qsettings.endGroup()

            # Save logging settings
            qsettings.beginGroup("Logging")
            qsettings.setValue(
                "config", settings.get("Logging/config", "Minimal logging")
            )
            qsettings.setValue("level", settings.get("Logging/level", "INFO"))
            qsettings.endGroup()

            # Force immediate write to disk
            qsettings.sync()

            # Verify settings were saved
            if qsettings.status() != QSettings.NoError:
                self.logger.error(
                    f"Failed to save settings: QSettings error {qsettings.status()}"
                )
                return False

            self.logger.info("Settings saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}", exc_info=True)
            return False

    def update_logging_level(self, level):
        update_logging_level(level)

    def apply_settings(self, new_settings):
        """Apply new settings throughout the app"""
        # Update logging level
        new_log_level = new_settings.get("Logging/level", "INFO")
        self.update_logging_level(new_log_level)

        # Update in-memory settings
        self.settings.update(new_settings)

        # Update backup settings
        self.backup_manager.update_settings(
            new_settings.get("Backup/enabled", False),
            new_settings.get("Backup/frequency", "Daily"),
            new_settings.get("Backup/location", ""),
        )

    def run(self):
        # Set application icon
        app_icon = QIcon(resource_path("assets/icon.png"))
        self.qt_app.setWindowIcon(app_icon)

        # Create login window
        self.login_window = LoginWindow(self)
        self.login_window.show()

        sys.exit(self.qt_app.exec())

    def on_database_unlocked(self, db_path):
        """Called when database is successfully unlocked"""
        self.logger.info(f"Database unlocked at: {db_path}")

        # Update backup manager with the new path
        self.backup_manager.db_path = db_path
        self.logger.debug(f"Backup manager db_path updated to: {db_path}")

        # Load settings from INI file
        self.load_settings()

        # Start backup scheduler with current settings
        self.start_backup_manager()

    def start_backup_manager(self):
        """Start backup scheduler with current settings"""
        backup_settings = {
            "enabled": self.settings.get("Backup/enabled", False),
            "frequency": self.settings.get("Backup/frequency", "Daily"),
            "location": self.settings.get("Backup/location", ""),
        }

        # Update backup manager
        self.backup_manager.update_settings(
            backup_settings["enabled"],
            backup_settings["frequency"],
            backup_settings["location"],
        )

    def on_exit(self):
        """Clean up on application exit"""
        clipboard = QApplication.clipboard()
        clipboard.clear()


def main():
    app = PasswordManagerApp()
    app.run()


if __name__ == "__main__":
    main()