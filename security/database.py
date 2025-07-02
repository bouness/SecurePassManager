import json
import logging
import os
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken


class SecureDatabase:
    def __init__(self, crypto_manager, db_path=None):
        self.crypto = crypto_manager
        self.db_path = db_path
        self.salt = None
        self.data = {}
        self.locked = True
        self.cipher = None
        self.password_history = {}
        self.logger = logging.getLogger("SecurePass.database")

        # Initialize database if path is provided
        # if db_path and os.path.exists(db_path):
        #     self.initialize()

    def initialize(self, master_password):
        """Initialize a new database with master password"""
        try:
            if not self.db_path:
                raise ValueError("Database path not set")

            # Generate salt
            self.salt = os.urandom(16)
            key = self.crypto.derive_key(master_password, self.salt)
            self.cipher = Fernet(key)

            # Create empty database
            self.data = {}
            self._save_data()
            return True
        except Exception as e:
            self.logger.debug(f"Database initialization failed: {str(e)}")
            return False

    def unlock(self, master_password: str) -> bool:
        try:
            if not self.db_path or not os.path.exists(self.db_path):
                self.logger.debug(f"Database file not found: {self.db_path}")
                return False

            with open(self.db_path, "rb") as f:
                encrypted = f.read()

            # First 16 bytes are salt
            self.salt = encrypted[:16]
            encrypted_data = encrypted[16:]

            # Derive key and initialize cipher
            key = self.crypto.derive_key(master_password, self.salt)
            self.cipher = Fernet(key)

            # Decrypt data
            decrypted = self.cipher.decrypt(encrypted_data)
            self.data = json.loads(decrypted)
            return True
        except (InvalidToken, json.JSONDecodeError) as e:
            print(f"Decryption failed: {str(e)}")
            return False
        except Exception as e:
            logging.error("Decryption failed: %s", e)
            # print(f"Unlock error: {str(e)}")
            # raise Exception("Decryption failed")
            return False

    def _save_data(self):
        """Save data to database file"""
        if not self.db_path:
            raise ValueError("Database path not set")
        if not self.cipher:
            raise ValueError("Cipher not initialized")

        # Serialize data
        json_data = json.dumps(self.data).encode()

        # Encrypt data
        encrypted_data = self.cipher.encrypt(json_data)

        # Prepend salt to encrypted data
        with open(self.db_path, "wb") as f:
            f.write(self.salt)
            f.write(encrypted_data)

    def add_password(
        self, service, username, password, category="Other", url="", notes=""
    ):
        """Add a new password entry"""
        # Check if service already exists
        # if service in self.data:
        #     # Update existing entry instead of creating duplicate
        #     self.update_password(
        #         service, service, username, password,
        #         category, url, notes
        #     )
        #     return

        # Check for duplicates
        if service in self.data:
            # Append a number to create a unique service name
            counter = 1
            new_service = f"{service} ({counter})"
            while new_service in self.data:
                counter += 1
                new_service = f"{service} ({counter})"
            service = new_service

        # Handle duplicate names
        base_service = service
        counter = 1
        while service in self.data:
            service = f"{base_service} ({counter})"
            counter += 1

        # Add the entry
        self.data[service] = {
            "username": username,
            "password": password,
            "category": category,
            "url": url,
            "notes": notes,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
        self._save_data()

    def get_password(self, service):
        """Get password details by service name"""
        return self.data.get(service)

    def get_all_entries(self):
        """Get all password entries"""
        return self.data

    def update_password(
        self, old_service, new_service, username, password, category, url, notes
    ):
        """Update an existing password entry"""
        if old_service not in self.data:
            raise KeyError(f"Service '{old_service}' not found")

        if not self.cipher:
            raise ValueError("Database not unlocked")

        # Save old password to history
        if old_service in self.data:
            old_entry = self.data[old_service]
            if old_service not in self.password_history:
                self.password_history[old_service] = []
            self.password_history[old_service].append(
                {
                    "password": old_entry["password"],
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # If service name changed, remove old entry
        if old_service != new_service and old_service in self.data:
            del self.data[old_service]

        # Add/update the entry
        self.data[new_service] = {
            "username": username,
            "password": password,
            "category": category,
            "url": url,
            "notes": notes,
            "updated": datetime.now().isoformat(),
        }
        self._save_data()

    def delete_password(self, service):
        """Delete a password entry by service name"""
        if service in self.data:
            del self.data[service]
            self._save_data()
            return True
        return False
