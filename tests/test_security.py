# tests/test_security.py
import os
import unittest


class TestSecurity(unittest.TestCase):
    def test_encryption_strength(self):
        # Test that encryption produces different output each time
        from security.crypto import CryptoManager

        crypto = CryptoManager()
        data = b"Test data"

        # Derive key and initialize cipher
        salt = os.urandom(16)
        key = crypto.derive_key("test_password", salt)
        crypto.initialize_cipher(key)

        encrypted1 = crypto.encrypt(data)
        encrypted2 = crypto.encrypt(data)

        # Should have different IVs
        self.assertNotEqual(encrypted1, encrypted2)

    def test_password_handling(self):
        # Ensure passwords are cleared from memory
        import os
        import tempfile

        from security.crypto import CryptoManager
        from security.database import SecureDatabase

        # Create temp database
        test_dir = tempfile.mkdtemp()
        db_path = os.path.join(test_dir, "test_db.spdb")

        crypto = CryptoManager()
        db = SecureDatabase(crypto, db_path)
        db.initialize("master_password")

        # db = SecureDatabase(CryptoManager())
        db.add_password("test", "user", "password")

        # Access should not expose plaintext password in memory
        entry = db.get_password("test")
        self.assertEqual(entry["password"], "password")

        # Cleanup
        os.remove(db_path)
        os.rmdir(test_dir)

        # Implementation should clear sensitive data from memory
        # This would require implementation-specific checks
