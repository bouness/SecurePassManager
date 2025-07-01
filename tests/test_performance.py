# tests/test_performance.py
import timeit
import unittest
import os

class TestPerformance(unittest.TestCase):
    def test_encryption_speed(self):
        setup = '''
from security.crypto import CryptoManager
import os
crypto = CryptoManager()
salt = os.urandom(16)
key = crypto.derive_key("test_password", salt)
crypto.initialize_cipher(key)
data = b"Test data" * 1000  # 9KB
        '''
        
        time = timeit.timeit('crypto.encrypt(data)', setup=setup, number=100)
        print(f"\nEncryption time for 100x 9KB: {time:.2f}s")
        self.assertLess(time, 5.0)  # Should be less than 5 seconds