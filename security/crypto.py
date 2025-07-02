import os
import logging
import ctypes
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoManager:
    def __init__(self):
        self.salt = None
        self.cipher = None
    
    def derive_key(self, password, salt=None):
        """Derive encryption key from password and salt"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        key = kdf.derive(password.encode())
        return base64.urlsafe_b64encode(key)

    def initialize_cipher(self, key):
        """Initialize Fernet cipher with derived key"""
        self.cipher = Fernet(key)

    def encrypt(self, data):
        """Encrypt data using initialized cipher"""
        if not self.cipher:
            raise RuntimeError("Cipher not initialized")
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)

    def decrypt(self, encrypted_data):
        """Decrypt data using initialized cipher"""
        if not self.cipher:
            raise RuntimeError("Cipher not initialized")
        return self.cipher.decrypt(encrypted_data)

    def get_salt(self):
        """Get the salt used for the current session"""
        if self.salt:
            return self.salt
        return os.urandom(16) 

    def secure_clear(self, data):
        """Truly secure memory clearing using ctypes"""
        try:
            if isinstance(data, bytearray):
                # Clear bytearray in place
                buffer = (ctypes.c_byte * len(data)).from_buffer(data)
                ctypes.memset(ctypes.addressof(buffer), 0, len(data))
            elif isinstance(data, bytes):
                # Convert to mutable bytearray and clear
                mutable = bytearray(data)
                buffer = (ctypes.c_byte * len(mutable)).from_buffer(mutable)
                ctypes.memset(ctypes.addressof(buffer), 0, len(mutable))
        except Exception as e:
            logging.error(f"Secure clear error: {str(e)}")
            