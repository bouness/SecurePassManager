import logging
import os
import shutil
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal


class BackupManager(QObject):
    backup_performed = Signal(str)
    backup_failed = Signal(str)

    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.enabled = False
        self.frequency = "Daily"
        self.location = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_backup)
        self.last_backup = None
        self.logger = logging.getLogger("SecurePass.backup")

    def update_settings(self, enabled, frequency, location):
        self.enabled = enabled
        self.frequency = frequency
        self.location = location

        # Stop existing timer if running
        self.timer.stop()

        # Log new settings
        self.logger.debug(
            f"Backup settings updated: "
            f"enabled={enabled}, frequency={frequency}, location={location}"
        )

        if enabled and location:
            # Start timer with appropriate interval
            interval = self._get_interval()
            self.timer.start(interval * 1000)  # Convert to milliseconds
            self.logger.info(f"Backup scheduled: {frequency} at {location}")
        elif enabled and not location:
            self.logger.warning("Backup enabled but no location specified")

    def _get_interval(self):
        """Return interval in seconds based on frequency"""
        if self.frequency == "Daily":
            return 24 * 60 * 60  # 1 day
        elif self.frequency == "Weekly":
            return 7 * 24 * 60 * 60  # 1 week
        elif self.frequency == "Monthly":
            return 30 * 24 * 60 * 60  # Approx 1 month
        return 0

    def check_backup(self):
        if not self.enabled or not self.location or not self.db_path:
            return

        now = datetime.now()
        needs_backup = False

        # If we've never done a backup, do one now
        if not self.last_backup:
            needs_backup = True
        else:
            # Calculate time since last backup
            time_since_last = now - self.last_backup

            if self.frequency == "Daily":
                needs_backup = time_since_last >= timedelta(days=1)
            elif self.frequency == "Weekly":
                needs_backup = time_since_last >= timedelta(weeks=1)
            elif self.frequency == "Monthly":
                # Approximate month as 30 days
                needs_backup = time_since_last >= timedelta(days=30)

        if needs_backup:
            self.logger.info("Performing scheduled backup")
            backup_path = self.perform_backup()
            if backup_path:
                self.logger.info(f"Scheduled backup completed: {backup_path}")

    def perform_backup(self):
        try:
            # Log critical information for debugging
            self.logger.debug(
                f"Attempting backup with settings: "
                f"enabled={self.enabled}, "
                f"location={self.location}, "
                f"db_path={self.db_path}"
            )

            # Check if we have a valid database path
            if not self.db_path:
                error_msg = "Database path not set in backup manager"
                self.logger.error(error_msg)
                self.backup_failed.emit(error_msg)
                return None

            self.logger.debug(f"Database path: {self.db_path}")

            if not os.path.exists(self.db_path):
                error_msg = f"Database file not found: {self.db_path}"
                self.logger.error(error_msg)
                self.backup_failed.emit(error_msg)
                return None

            # Create backup directory if needed
            os.makedirs(self.location, exist_ok=True)

            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"SecurePass_Backup_{timestamp}.spdb"
            backup_path = os.path.join(self.location, backup_name)

            # Copy database file
            self.logger.info(f"Starting backup to: {backup_path}")
            shutil.copy2(self.db_path, backup_path)
            self.last_backup = datetime.now()

            # Verify backup was created
            if not os.path.exists(backup_path):
                error_msg = f"Backup file not created: {backup_path}"
                self.logger.error(error_msg)
                self.backup_failed.emit(error_msg)
                return None

            # Verify backup size
            original_size = os.path.getsize(self.db_path)
            backup_size = os.path.getsize(backup_path)

            if backup_size == 0:
                error_msg = f"Backup file is empty: {backup_path}"
                self.logger.error(error_msg)
                self.backup_failed.emit(error_msg)
                return None

            if backup_size < original_size * 0.5:  # At least 50% of original size
                error_msg = f"Backup file suspiciously small: {backup_size} bytes (original: {original_size})"
                self.logger.warning(error_msg)

            self.logger.info(f"Backup successful: {backup_path} ({backup_size} bytes)")
            self.backup_performed.emit(backup_path)
            return backup_path

        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            self.logger.exception(error_msg)  # Log exception with traceback
            self.backup_failed.emit(error_msg)
            return None
