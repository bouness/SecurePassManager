import ctypes
import os
import platform
import subprocess
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from gui.login import LoginWindow
from security.backup_manager import BackupManager
from security.crypto import CryptoManager
from security.database import SecureDatabase
from security.firewall import FirewallManager
from security.proxy import ProxyManager
from utils import resource_path, setup_logging, update_logging_level


class PasswordManagerApp:
    def __init__(self):
        # Initialize proxy manager first to get logging settings
        self.proxy = ProxyManager()

        # Log settings for verification
        # print("Proxy Manager Settings:", self.proxy.settings)

        # Setup logging with level from settings
        log_level = self.proxy.settings.get("Logging/level", "INFO")
        self.logger = setup_logging("SecurePass", log_level=log_level)
        self.logger.info("Application starting")
        self.logger.debug(f"Initial settings: {self.proxy.settings}")

        # Setup logging with level from settings
        log_level = self.proxy.settings.get("Logging/level", "INFO")
        self.logger = setup_logging("SecurePass", log_level=log_level)
        self.logger.info("Application starting")

        self.qt_app = QApplication(sys.argv)
        self.qt_app.aboutToQuit.connect(self.on_exit)

        # Initialize components
        self.crypto = CryptoManager()
        self.firewall = FirewallManager()

        # Initialize database without path - will be set later
        self.db = SecureDatabase(self.crypto, db_path=None)

        # Initialize backup manager (only once)
        self.backup_manager = BackupManager(self)
        self.logger.info("Backup manager initialized")

        # Set clipboard timeout default
        self.clipboard_timeout = 30

        # Privilege state
        self.has_admin_privileges = self.check_admin_privileges()
        self.firewall_active = self.firewall.is_active()
        self.privilege_checked = False

    def update_logging_level(self, level):
        update_logging_level(level)

    def apply_settings(self, new_settings):
        """Apply new settings throughout the app"""
        # Update logging level
        new_log_level = new_settings.get("Logging/level", "INFO")
        self.update_logging_level(new_log_level)

        # Update proxy settings
        self.proxy.settings = new_settings

        # Update backup settings
        self.backup_manager.update_settings(
            new_settings.get("Backup/enabled", False),
            new_settings.get("Backup/frequency", "Daily"),
            new_settings.get("Backup/location", ""),
        )

    def check_admin_privileges(self):
        """Check if we have admin privileges"""
        try:
            if os.name == "nt":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Check if we can run sudo without password
                result = subprocess.run(
                    ["sudo", "-n", "true"],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )
                return result.returncode == 0
        except:
            return False

    def run(self):
        # Set application icon
        app_icon = QIcon(resource_path("assets/icon.png"))
        self.qt_app.setWindowIcon(app_icon)

        # Try to enable firewall first
        firewall_success = self.firewall.block_incoming()

        # If firewall failed and we haven't checked privileges yet
        if not firewall_success and not self.privilege_checked:
            # Check if we have admin privileges now
            self.has_admin_privileges = self.check_admin_privileges()
            self.privilege_checked = True

            # If we still don't have privileges, show warning
            if not self.has_admin_privileges:
                result = QMessageBox.warning(
                    None,
                    "Admin Privileges Required",
                    "SecurePass Manager requires administrator privileges for full security features.\n\n"
                    "Some security features like firewall protection will be limited.\n\n"
                    "Do you want to grant administrator privileges now?",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if result == QMessageBox.Yes:
                    # Try to grant privileges
                    grant_success = self.grant_admin_privileges()

                    if grant_success:
                        # Update privilege status and try firewall again
                        self.has_admin_privileges = True
                        self.firewall.block_incoming(use_sudo=True)
                    else:
                        # Continue with limited functionality
                        self.logger.warning("Continuing without admin privileges")
                else:
                    # User declined privileges - continue normally
                    self.logger.info("User declined admin privileges")

        # Apply proxy settings
        self.proxy.set_application_proxy()

        if self.proxy.settings["enabled"] and self.proxy.settings["system_wide"]:
            self.proxy.set_system_proxy()

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
        self.proxy.load_settings()

        # Start backup scheduler with current settings
        self.start_backup_manager()

    def start_backup_manager(self):
        """Start backup scheduler with current settings"""
        backup_settings = {
            "enabled": self.proxy.settings.get("Backup/enabled", False),
            "frequency": self.proxy.settings.get("Backup/frequency", "Daily"),
            "location": self.proxy.settings.get("Backup/location", ""),
        }

        # Update backup manager
        self.backup_manager.update_settings(
            backup_settings["enabled"],
            backup_settings["frequency"],
            backup_settings["location"],
        )

    def grant_admin_privileges(self):
        """Run specific commands with admin privileges using a GUI password prompt"""
        try:
            if os.name == "nt":
                # Windows - re-run with admin privileges
                self.logger.info("Requesting Windows admin privileges")
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)
                return True  # Never reached, but included for completeness

            else:
                # Unix-like systems - use GUI password prompt
                self.logger.info("Requesting Unix admin privileges")
                command = " && ".join(
                    [
                        "ufw enable",
                        "ufw default deny incoming",
                        "ufw default allow outgoing",
                    ]
                )

                # Use system-specific GUI sudo prompts
                if platform.system() == "Darwin":
                    applescript = f"""
                    do shell script "{command}" 
                    with administrator privileges
                    """
                    subprocess.run(["osascript", "-e", applescript], check=True)
                else:  # Linux
                    subprocess.run(["pkexec", "sh", "-c", command], check=True)

                # Update privilege status
                self.has_admin_privileges = True
                self.firewall.active = True

                QMessageBox.information(
                    None, "Privileges Granted", "Security features have been enabled."
                )
                return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Privilege escalation failed: {e}")
            QMessageBox.critical(
                None,
                "Privilege Error",
                f"Failed to grant admin privileges: {str(e)}\n\n"
                "Please try again or run the application as administrator.",
            )
            return False
        except Exception as e:
            self.logger.error(f"Unexpected privilege error: {e}")
            QMessageBox.critical(
                None, "Error", f"An unexpected error occurred: {str(e)}"
            )
            return False

    def restart_app(self):
        """Restart the application"""
        if os.name == "nt":
            # Windows
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        else:
            # Unix-like systems
            os.execv(sys.executable, ["python"] + sys.argv)
        sys.exit()

    def on_exit(self):
        """Clean up on application exit"""
        clipboard = QApplication.clipboard()
        clipboard.clear()


def main():
    app = PasswordManagerApp()
    app.run()


if __name__ == "__main__":
    main()
