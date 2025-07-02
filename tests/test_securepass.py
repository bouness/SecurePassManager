# tests/test_securepass.py
import csv
import io
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from security.crypto import CryptoManager
from security.database import SecureDatabase
from security.exporter import PasswordExporter
from security.firewall import FirewallManager
from security.importer import PasswordImporter


class TestCryptoManager(unittest.TestCase):
    def setUp(self):
        self.crypto = CryptoManager()
        self.test_data = b"Top secret password data!"
        # Derive key and initialize cipher
        self.salt = os.urandom(16)
        key = self.crypto.derive_key("test_password", self.salt)
        self.crypto.initialize_cipher(key)

    def test_encryption_decryption(self):
        # Test basic encryption/decryption
        encrypted = self.crypto.encrypt(self.test_data)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, self.test_data)

    def test_key_consistency(self):
        # Ensure same key gives same results
        salt1 = os.urandom(16)
        key1 = self.crypto.derive_key("password1", salt1)

        # Initialize both instances with the same key
        self.crypto.initialize_cipher(key1)

        # Create new crypto instance for key consistency
        crypto2 = CryptoManager()
        crypto2.initialize_cipher(key1)

        encrypted1 = self.crypto.encrypt(self.test_data)
        encrypted2 = crypto2.encrypt(self.test_data)

        # self.assertEqual(encrypted1, encrypted2)
        # Problem: Encrypted outputs differ even with same key
        # Solution: Fernet uses random IVs so ciphertexts will always differ. Test decryption instead.

        # Should decrypt to same value
        decrypted1 = self.crypto.decrypt(encrypted1)
        decrypted2 = crypto2.decrypt(encrypted2)
        self.assertEqual(decrypted1, self.test_data)
        self.assertEqual(decrypted2, self.test_data)

        # Should fail with wrong key
        salt2 = os.urandom(16)
        key2 = self.crypto.derive_key("password2", salt2)
        crypto3 = CryptoManager()
        crypto3.initialize_cipher(key2)

        with self.assertRaises(Exception):
            crypto3.decrypt(encrypted1)

    def test_large_data(self):
        # Test with large data
        large_data = os.urandom(10 * 1024 * 1024)  # 10MB
        encrypted = self.crypto.encrypt(large_data)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, large_data)

    def test_get_salt(self):
        # Verify salt generation
        salt = self.crypto.get_salt()
        self.assertEqual(len(salt), 16)
        self.assertIsInstance(salt, bytes)

    def test_get_salt_returns_bytes(self):
        # Ensure it returns bytes and length.
        salt = self.crypto.get_salt()
        self.assertIsInstance(salt, bytes)
        self.assertEqual(len(salt), 16)

    def test_secure_clear(self):
        # Test secure memory clearing
        sensitive_data = bytearray(b"sensitive")
        self.crypto.secure_clear(sensitive_data)
        self.assertEqual(sensitive_data, bytearray(len(sensitive_data)))

    def test_decrypt_invalid_data(self):
        # Test decryption failure with invalid data
        with self.assertRaises(Exception):
            self.crypto.decrypt(b"invalid_ciphertext")

    def test_encrypt_empty_data(self):
        # Test edge case with empty input
        encrypted = self.crypto.encrypt(b"")
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, b"")


class TestSecureDatabase(unittest.TestCase):
    def setUp(self):
        self.crypto = CryptoManager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db.spdb")

        # Create a new database
        self.db = SecureDatabase(self.crypto, self.db_path)
        self.db.initialize("test_password")

        # Capture logs
        self.log_capture = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        logging.getLogger("SecurePass.database").addHandler(self.log_handler)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        logging.getLogger("SecurePass.database").removeHandler(self.log_handler)

    @property
    def captured_log(self):
        return self.log_capture.getvalue()

    def test_create_and_load(self):
        # Test database creation and loading
        self.db.initialize("master_password")
        self.db.add_password("google", "user1", "pass1", "Email")
        self.db.add_password("github", "user2", "pass2", "Development")
        self.db._save_data()

        # Create a new instance to test loading
        new_db = SecureDatabase(self.crypto, self.db_path)
        self.assertTrue(new_db.unlock("master_password"))  # Unlock with password

        self.assertEqual(len(new_db.data), 2)
        self.assertEqual(new_db.get_password("google")["username"], "user1")
        self.assertEqual(new_db.get_password("github")["password"], "pass2")

    def test_add_password(self):
        self.db.add_password("service1", "user1", "pass1")
        self.assertEqual(len(self.db.data), 1)

        # Test duplicate handling
        self.db.add_password("service1", "user2", "pass2")
        self.assertEqual(len(self.db.data), 2)
        self.assertTrue("service1 (1)" in self.db.data)

    def test_update_password(self):
        self.db.add_password(
            "amazon", "user1", "pass1", "Shopping", "https://amazon.com", "Notes"
        )

        # Update without changing service name
        self.db.update_password(
            "amazon",
            "amazon",
            "newuser",
            "newpass",
            "Shopping",
            "https://amazon.com",
            "Updated notes",
        )

        entry = self.db.get_password("amazon")
        self.assertEqual(entry["username"], "newuser")
        self.assertEqual(entry["password"], "newpass")
        self.assertEqual(entry["category"], "Shopping")

        # Test service name change - provide all arguments
        self.db.update_password(
            "amazon",
            "amazon-web",
            "newuser",
            "newpass",
            "Shopping",
            "https://amazon.com",
            "Updated notes",
        )
        self.assertTrue("amazon-web" in self.db.data)
        self.assertFalse("amazon" in self.db.data)

    def test_delete_password(self):
        self.db.add_password("twitter", "user1", "pass1")
        self.assertEqual(len(self.db.data), 1)

        self.db.delete_password("twitter")
        self.assertEqual(len(self.db.data), 0)
        self.assertIsNone(self.db.get_password("twitter"))

    def test_unlock_failure(self):
        # Test wrong password
        self.db.add_password("test", "user", "pass")
        self.db._save_data()

        new_db = SecureDatabase(self.crypto, self.db_path)
        self.assertFalse(new_db.unlock("wrong_password"))
        self.assertEqual(len(new_db.data), 0)

    def test_unlock_corrupted_data(self):
        with open(self.db_path, "wb") as f:
            f.write(b"corrupted_data")

        new_db = SecureDatabase(self.crypto, self.db_path)

        with patch("builtins.print") as mock_print:
            self.assertFalse(new_db.unlock("test_password"))
            printed_texts = [call.args[0] for call in mock_print.call_args_list]
            self.assertTrue(
                any("Decryption failed" in text for text in printed_texts),
                "Expected 'Decryption failed' message in print output",
            )

    def test_update_nonexistent_entry(self):
        # Test updating non-existing service
        with self.assertRaises(KeyError):
            self.db.update_password(
                "nonexistent",
                "new_service",
                "user",
                "pass",
                "category",
                "https://example.com",
                "notes",
            )

    def test_duplicate_service_handling(self):
        # Test duplicate service name resolution
        self.db.add_password("service", "user1", "pass1")
        self.db.add_password("service", "user2", "pass2")
        self.db.add_password("service", "user3", "pass3")

        self.assertIn("service", self.db.data)
        self.assertIn("service (1)", self.db.data)
        self.assertIn("service (2)", self.db.data)


class TestFirewallManager(unittest.TestCase):
    @patch("subprocess.run")
    def test_windows_firewall(self, mock_run):
        manager = FirewallManager()
        manager.os_type = "Windows"

        # Test successful block
        mock_run.return_value.returncode = 0
        self.assertTrue(manager.block_incoming())

        # Test failed block
        # mock_run.side_effect = Exception("Firewall error")
        # self.assertFalse(manager.block_incoming())

        # Test failed block
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertFalse(manager.block_incoming())

    @patch("subprocess.run")
    def test_linux_firewall(self, mock_run):
        manager = FirewallManager()
        manager.os_type = "Linux"

        # Test successful block
        mock_run.return_value.returncode = 0
        self.assertTrue(manager.block_incoming())

        # Test failed block
        # mock_run.side_effect = Exception("Firewall error")
        # self.assertFalse(manager.block_incoming())

        # Test failed block - use CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertFalse(manager.block_incoming())

    @patch("subprocess.run")
    def test_macos_firewall(self, mock_run):
        manager = FirewallManager()
        manager.os_type = "Darwin"

        # Test successful block
        mock_run.return_value.returncode = 0
        self.assertTrue(manager.block_incoming())

        # Test failed block
        mock_run.side_effect = Exception("Firewall error")
        self.assertFalse(manager.block_incoming())

    @patch("subprocess.run")
    def test_windows_block_implementation(self, mock_run):
        # Test Windows-specific blocking logic
        manager = FirewallManager()
        manager.os_type = "Windows"
        manager._run_windows_block(kwargs={})
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_linux_block_implementation(self, mock_run):
        # Test Linux-specific blocking logic
        manager = FirewallManager()
        manager.os_type = "Linux"
        manager._run_linux_block(use_sudo=False)
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_macos_block_implementation(self, mock_run):
        # Test macOS-specific blocking logic
        manager = FirewallManager()
        manager.os_type = "Darwin"
        manager._run_macos_block(use_sudo=False)
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_firewall_status_check(self, mock_run):
        manager = FirewallManager()

        # Mock exact output that matches the detection logic
        if manager.os_type == "Linux":
            mock_run.return_value.stdout = (
                "Status: active\nDefault: deny (incoming), allow (outgoing)"
            )
        elif manager.os_type == "Windows":
            mock_run.return_value.stdout = """
            Domain Profile Settings:
            ----------------------------------------------------------------------
            State                                 ON
            Private Profile Settings:
            ----------------------------------------------------------------------
            State                                 ON
            Public Profile Settings:
            ----------------------------------------------------------------------
            State                                 ON
            """
        elif manager.os_type == "Darwin":
            mock_run.return_value.stdout = "Status: Enabled"

        # Skip test if not implemented for this OS
        if manager.os_type in ("Linux", "Windows", "Darwin"):
            self.assertTrue(manager.is_active())

    @patch("subprocess.run")
    def test_firewall_is_active_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        fw = FirewallManager()
        self.assertFalse(fw.is_active())


class TestProxyManager(unittest.TestCase):
    def setUp(self):
        from security.proxy import ProxyManager

        self.proxy = ProxyManager()
        self.proxy.settings = {
            "enabled": True,
            "type": "SOCKS5",
            "host": "127.0.0.1",
            "port": "8080",
            "auth_enabled": True,
            "username": "testuser",
            "password": "testpass",
            "system_wide": True,
        }

    @patch("PySide6.QtNetwork.QNetworkProxy.setApplicationProxy")
    def test_application_proxy(self, mock_set_proxy):
        self.proxy.set_application_proxy()
        mock_set_proxy.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_system_proxy(self):
        # Simulate Linux environment
        self.proxy.os_type = "Linux"

        # Test session-based proxy
        self.proxy.set_system_proxy()

        # Verify environment variables were set
        self.assertEqual(os.environ.get("http_proxy"), "http://127.0.0.1:8080")
        self.assertEqual(os.environ.get("https_proxy"), "http://127.0.0.1:8080")
        self.assertEqual(os.environ.get("HTTP_PROXY"), "http://127.0.0.1:8080")
        self.assertEqual(os.environ.get("HTTPS_PROXY"), "http://127.0.0.1:8080")

        # Test clear
        self.proxy.clear_system_proxy()
        self.assertIsNone(os.environ.get("http_proxy"))
        self.assertIsNone(os.environ.get("https_proxy"))
        self.assertIsNone(os.environ.get("HTTP_PROXY"))
        self.assertIsNone(os.environ.get("HTTPS_PROXY"))

    @patch("subprocess.run")
    def test_windows_system_proxy(self, mock_run):
        # Set OS type for test
        self.proxy.os_type = "Windows"
        self.proxy.settings["system_wide"] = True

        # Test successful proxy set
        mock_run.return_value.returncode = 0
        self.assertTrue(self.proxy.set_system_proxy())

        # Test clear
        self.assertTrue(self.proxy.clear_system_proxy())

    @patch("PySide6.QtNetwork.QNetworkProxy.setApplicationProxy")
    def test_application_proxy_auth(self, mock_set_proxy):
        # Test proxy with authentication
        self.proxy.settings["auth_enabled"] = True
        self.proxy.set_application_proxy()

        # Verify proxy configuration includes auth
        proxy_arg = mock_set_proxy.call_args[0][0]
        self.assertEqual(proxy_arg.user(), "testuser")
        self.assertEqual(proxy_arg.password(), "testpass")

    @patch("security.proxy.winreg", create=True)
    @patch("subprocess.run")
    def test_windows_proxy_registry(self, mock_run, mock_winreg):
        # Mock Windows registry functions
        mock_winreg.ConnectRegistry.return_value = MagicMock()
        mock_winreg.OpenKey.return_value = MagicMock()
        mock_winreg.SetValueEx = MagicMock()

        # Mock subprocess to succeed
        mock_run.return_value.returncode = 0

        # Set OS type for test
        self.proxy.os_type = "Windows"
        self.proxy.settings["system_wide"] = True

        # Test proxy set
        self.assertTrue(self.proxy.set_system_proxy())

        # Test clear operation
        self.assertTrue(self.proxy.clear_system_proxy())


class TestImportExport(unittest.TestCase):
    def setUp(self):
        self.crypto = CryptoManager()
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_db.spdb")
        self.db = SecureDatabase(self.crypto, self.db_path)
        self.db.initialize("master_password")  # Initialize database
        self.importer = PasswordImporter(self.crypto, self.db)
        self.exporter = PasswordExporter(self.db)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_lastpass_import(self):
        # Create a sample LastPass CSV
        csv_path = os.path.join(self.test_dir, "lastpass.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["url", "username", "password", "extra", "name", "grouping"]
            )
            writer.writerow(
                ["https://google.com", "user1", "pass1", "Note", "Google", "Web"]
            )
            writer.writerow(
                ["https://github.com", "user2", "pass2", "", "GitHub", "Development"]
            )

        count = self.importer.import_passwords(csv_path, "lastpass")
        self.assertEqual(count, 2)

        # Verify imported data
        google_entry = self.db.get_password("Google")
        self.assertEqual(google_entry["username"], "user1")
        self.assertEqual(google_entry["category"], "Web")

        github_entry = self.db.get_password("GitHub")
        self.assertEqual(github_entry["password"], "pass2")

    def test_bitwarden_import(self):
        # Create sample Bitwarden JSON
        json_path = os.path.join(self.test_dir, "bitwarden.json")
        data = {
            "items": [
                {
                    "type": 1,
                    "name": "Google",
                    "login": {
                        "username": "user1",
                        "password": "pass1",
                        "uris": [{"uri": "https://google.com"}],
                    },
                    "notes": "Work account",
                },
                {
                    "type": 2,  # Should be skipped
                    "name": "Credit Card",
                    "card": {"cardholderName": "John Doe"},
                },
            ]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        count = self.importer.import_passwords(json_path, "bitwarden")
        self.assertEqual(count, 1)
        self.assertEqual(self.db.get_password("Google")["notes"], "Work account")

    def test_csv_export(self):
        # Add some data
        self.db.add_password(
            "Service1", "user1", "pass1", "Category1", "https://service1.com", "Note1"
        )
        self.db.add_password(
            "Service2", "user2", "pass2", "Category2", "https://service2.com", "Note2"
        )

        # Export to CSV
        csv_path = os.path.join(self.test_dir, "export.csv")
        success = self.exporter.export_passwords(csv_path, "csv")
        self.assertTrue(success)

        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["Service"], "Service1")
            self.assertEqual(rows[0]["Password"], "pass1")
            self.assertEqual(rows[1]["URL"], "https://service2.com")

    def test_json_export(self):
        # Add some data
        self.db.add_password("JSONService", "jsonuser", "jsonpass")

        # Export to JSON
        json_path = os.path.join(self.test_dir, "export.json")
        success = self.exporter.export_passwords(json_path, "json")
        self.assertTrue(success)

        # Verify JSON content
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["service"], "JSONService")
            self.assertEqual(data[0]["username"], "jsonuser")

    def test_export_get_all_entries(self):
        # Test get_all_entries method
        self.db.add_password("export_test", "user", "pass")
        exporter = PasswordExporter(self.db)
        entries = exporter.get_all_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries["export_test"]["username"], "user")

    def test_export_unsupported_format(self):
        # Test handling of unsupported export formats
        with self.assertRaises(ValueError):
            self.exporter.export_passwords("dummy.xyz", "unsupported_format")

    @patch("PySide6.QtWidgets.QProgressDialog")
    @patch("PySide6.QtWidgets.QMessageBox")
    def test_generic_csv_import(self, mock_msgbox, mock_progress):
        # Test generic CSV import
        csv_path = os.path.join(self.test_dir, "generic.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Service", "Username", "Password", "Category"])
            writer.writerow(
                ["Netflix", "user@netflix.com", "password123", "Entertainment"]
            )

        # Mock progress dialog
        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.wasCanceled.return_value = False

        # Mock the database add_password method
        with patch.object(self.db, "add_password") as mock_add:
            # Call the actual import method
            count = self.importer.import_passwords(csv_path, "generic_csv")

            # Verify add_password was called with correct arguments
            mock_add.assert_called_once()
            call_args = mock_add.call_args[0]
            self.assertEqual(call_args[0], "Netflix")  # Service
            self.assertEqual(call_args[1], "user@netflix.com")  # Username
            self.assertEqual(call_args[2], "password123")  # Password
            self.assertEqual(call_args[3], "Imported")  # Category
            self.assertEqual(call_args[4], "")  # URL
            self.assertEqual(call_args[5], "")  # Notes

            # Verify the count
            self.assertEqual(count, 1)

    @patch("PySide6.QtWidgets.QProgressDialog")
    @patch("PySide6.QtWidgets.QMessageBox")
    def test_import_chrome_csv(self, mock_msgbox, mock_progress):
        csv_path = os.path.join(self.test_dir, "chrome.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "url", "username", "password"])
            writer.writerow(["YouTube", "https://youtube.com", "user", "pass"])

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.wasCanceled.return_value = False

        with patch.object(self.db, "add_password") as mock_add:
            count = self.importer.import_passwords(csv_path, "chrome")
            mock_add.assert_called_once()
            self.assertEqual(count, 1)

    def test_1password_import(self):
        # Test 1Password import
        json_path = os.path.join(self.test_dir, "1password.json")
        data = {
            "items": [
                {
                    "category": "LOGIN",
                    "title": "Amazon",
                    "fields": [
                        {"designation": "username", "value": "user"},
                        {"designation": "password", "value": "pass"},
                    ],
                    "urls": [{"href": "https://amazon.com"}],
                }
            ]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        count = self.importer.import_passwords(json_path, "1password")
        self.assertEqual(count, 1)

    @patch("PySide6.QtWidgets.QProgressDialog")
    @patch("PySide6.QtWidgets.QMessageBox")
    def test_field_detection(self, mock_msgbox, mock_progress):
        # Test automatic field detection
        csv_path = os.path.join(self.test_dir, "detection.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "login", "pwd", "group", "comments"])
            writer.writerow(["Google", "user@gmail.com", "secret", "Web", "Personal"])

        # Mock progress dialog
        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.wasCanceled.return_value = False

        # Mock the database add_password method
        with patch.object(self.db, "add_password") as mock_add:
            # Call the actual import method
            count = self.importer.import_passwords(csv_path, "generic_csv")

            # Verify add_password was called with correct arguments
            mock_add.assert_called_once()
            call_args = mock_add.call_args[0]
            self.assertEqual(call_args[0], "Google")  # Service
            self.assertEqual(call_args[1], "user@gmail.com")  # Username
            self.assertEqual(call_args[2], "secret")  # Password
            self.assertEqual(call_args[3], "Imported")  # Category
            self.assertEqual(call_args[4], "")  # URL
            self.assertEqual(call_args[5], "Personal")  # Notes

            # Verify the count
            self.assertEqual(count, 1)


class TestIntegration(unittest.TestCase):
    def test_full_workflow(self):
        # Create a temporary workspace
        test_dir = tempfile.mkdtemp()
        db_path = os.path.join(test_dir, "integration_test.spdb")

        try:
            # Initialize components
            crypto = CryptoManager()
            db = SecureDatabase(crypto, db_path)
            db.initialize("master_password")
            firewall = FirewallManager()

            from security.proxy import ProxyManager

            proxy = ProxyManager()

            # Mock firewall and proxy
            firewall.block_incoming = MagicMock(return_value=True)
            proxy.set_application_proxy = MagicMock()

            # Add passwords
            db.add_password("integration1", "user1", "pass1")
            db.add_password("integration2", "user2", "pass2", "Work")

            # Verify additions
            self.assertEqual(len(db.data), 2)
            self.assertEqual(db.get_password("integration1")["username"], "user1")

            # Update password
            db.update_password(
                "integration2",
                "integration2-updated",
                "user2-new",
                "pass2-new",
                "Work",
                "https://integration2-updated.com",
                "Updated notes",
            )
            entry = db.get_password("integration2-updated")
            self.assertEqual(entry["password"], "pass2-new")
            self.assertEqual(entry["category"], "Work")

            # Delete password - should remove integration1
            db.delete_password("integration1")
            self.assertEqual(len(db.data), 1)
            self.assertIsNone(db.get_password("integration1"))  # Should be gone

            # Test persistence
            db._save_data()
            new_db = SecureDatabase(crypto, db_path)
            # Unlock with password
            self.assertTrue(new_db.unlock("master_password"))

            # Verify data
            self.assertEqual(len(new_db.data), 1)
            self.assertIsNotNone(new_db.get_password("integration2-updated"))

        finally:
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main()
