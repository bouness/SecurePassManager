import tempfile
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QSettings

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security.proxy import ProxyManager

class TestProxyManager(unittest.TestCase):
    
    def test_save_settings_success(self):
        """Test successful saving of settings to a real file"""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Mock the config path to use our temp file
            with patch('utils.get_config_path', return_value=temp_path):
                proxy = ProxyManager()
                
                # Set test settings
                test_settings = {
                    "enabled": True,
                    "type": "SOCKS5",
                    "host": "127.0.0.1",
                    "port": "1080",
                    "auth_enabled": True,
                    "username": "testuser",
                    "password": "testpass",
                    "system_wide": True,
                    "Backup/enabled": True,
                    "Backup/frequency": "Weekly",
                    "Backup/location": "/tmp/backup",
                    "Logging/config": "Full logging",
                    "Logging/level": "DEBUG",
                }
                
                # Test saving
                result = proxy.save_settings(test_settings)
                self.assertTrue(result, "save_settings should return True on success")
                
                # Verify file was created and contains expected data
                self.assertTrue(os.path.exists(temp_path), "Settings file should exist")
                
                # Read back the settings to verify they were saved correctly
                saved_settings = QSettings(temp_path, QSettings.IniFormat)
                
                # Check proxy settings
                saved_settings.beginGroup("Proxy")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("type", type=str), "SOCKS5")
                self.assertEqual(saved_settings.value("host", type=str), "127.0.0.1")
                self.assertEqual(saved_settings.value("port", type=str), "1080")
                saved_settings.endGroup()
                
                # Check backup settings
                saved_settings.beginGroup("Backup")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("frequency", type=str), "Weekly")
                saved_settings.endGroup()
                
                # Check logging settings
                saved_settings.beginGroup("Logging")
                self.assertEqual(saved_settings.value("config", type=str), "Full logging")
                self.assertEqual(saved_settings.value("level", type=str), "DEBUG")
                saved_settings.endGroup()
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_settings_uses_instance_settings(self):
        """Test that save_settings uses instance settings when no parameter provided"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch('utils.get_config_path', return_value=temp_path):
                proxy = ProxyManager()
                
                # Modify instance settings
                proxy.settings["enabled"] = True
                proxy.settings["host"] = "proxy.example.com"
                proxy.settings["port"] = "8080"
                
                # Call save_settings without parameters (should use instance settings)
                result = proxy.save_settings()
                self.assertTrue(result)
                
                # Verify the instance settings were saved
                saved_settings = QSettings(temp_path, QSettings.IniFormat)
                saved_settings.beginGroup("Proxy")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("host", type=str), "proxy.example.com")
                self.assertEqual(saved_settings.value("port", type=str), "8080")
                saved_settings.endGroup()
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_settings_readonly_directory(self):
        """Test save_settings when trying to write to a readonly directory"""
        # Mock get_config_path to return a problematic path
        with patch('utils.get_config_path', return_value="/root/nonexistent/readonly/settings.ini"):
            # Also mock QSettings to simulate failure
            with patch('security.proxy.QSettings') as MockQSettings:
                mock_settings = MockQSettings.return_value
                mock_settings.status.return_value = QSettings.AccessError
                
                proxy = ProxyManager()
                result = proxy.save_settings()
                
                # Should return False when file cannot be written
                self.assertFalse(result)

    def test_save_settings_empty_settings(self):
        """Test save_settings with minimal/empty settings"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch('utils.get_config_path', return_value=temp_path):
                proxy = ProxyManager()
                
                # Test with minimal settings
                minimal_settings = {
                    "enabled": False,
                    "type": "",
                    "host": "",
                    "port": "",
                    "auth_enabled": False,
                    "username": "",
                    "password": "",
                    "system_wide": False,
                    "Backup/enabled": False,
                    "Backup/frequency": "",
                    "Backup/location": "",
                    "Logging/config": "",
                    "Logging/level": "",
                }
                
                result = proxy.save_settings(minimal_settings)
                self.assertTrue(result)
                
                # Verify empty values were saved correctly
                saved_settings = QSettings(temp_path, QSettings.IniFormat)
                saved_settings.beginGroup("Proxy")
                self.assertEqual(saved_settings.value("enabled", type=bool), False)
                self.assertEqual(saved_settings.value("host", type=str), "")
                saved_settings.endGroup()
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_settings_with_none_parameter(self):
        """Test that passing None to save_settings uses instance settings"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch('utils.get_config_path', return_value=temp_path):
                proxy = ProxyManager()
                
                # Modify instance settings
                proxy.settings["enabled"] = True
                proxy.settings["type"] = "HTTP"
                
                # Call with None (should use instance settings)
                result = proxy.save_settings(None)
                self.assertTrue(result)
                
                # Verify instance settings were used
                saved_settings = QSettings(temp_path, QSettings.IniFormat)
                saved_settings.beginGroup("Proxy")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("type", type=str), "HTTP")
                saved_settings.endGroup()
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_settings_integration(self):
        """Integration test using a real temporary file"""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Mock the config path to use our temp file
            with patch('utils.get_config_path', return_value=temp_path):
                proxy = ProxyManager()
                
                # Set test settings
                test_settings = {
                    "enabled": True,
                    "type": "SOCKS5",
                    "host": "127.0.0.1",
                    "port": "1080",
                    "auth_enabled": True,
                    "username": "testuser",
                    "password": "testpass",
                    "system_wide": True,
                    "Backup/enabled": True,
                    "Backup/frequency": "Weekly",
                    "Backup/location": "/tmp/backup",
                    "Logging/config": "Full logging",
                    "Logging/level": "DEBUG",
                }
                
                # Test saving
                result = proxy.save_settings(test_settings)
                self.assertTrue(result, "save_settings should return True on success")
                
                # Verify file was created and contains expected data
                self.assertTrue(os.path.exists(temp_path), "Settings file should exist")
                
                # Read back the settings to verify they were saved correctly
                saved_settings = QSettings(temp_path, QSettings.IniFormat)
                
                # Check proxy settings
                saved_settings.beginGroup("Proxy")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("type", type=str), "SOCKS5")
                self.assertEqual(saved_settings.value("host", type=str), "127.0.0.1")
                self.assertEqual(saved_settings.value("port", type=str), "1080")
                self.assertEqual(saved_settings.value("auth_enabled", type=bool), True)
                self.assertEqual(saved_settings.value("username", type=str), "testuser")
                self.assertEqual(saved_settings.value("password", type=str), "testpass")
                self.assertEqual(saved_settings.value("system_wide", type=bool), True)
                saved_settings.endGroup()
                
                # Check backup settings
                saved_settings.beginGroup("Backup")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("frequency", type=str), "Weekly")
                self.assertEqual(saved_settings.value("location", type=str), "/tmp/backup")
                saved_settings.endGroup()
                
                # Check logging settings
                saved_settings.beginGroup("Logging")
                self.assertEqual(saved_settings.value("config", type=str), "Full logging")
                self.assertEqual(saved_settings.value("level", type=str), "DEBUG")
                saved_settings.endGroup()
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_settings_exception(self):
        """Test save_settings when QSettings constructor raises exception"""
        # Mock get_config_path to return a valid path
        with patch('utils.get_config_path', return_value="/fake/path"):
            proxy = ProxyManager()
            
            # Patch QSettings to raise an exception
            with patch('security.proxy.QSettings', side_effect=Exception("Test exception")):
                result = proxy.save_settings()
                
                # Should return False when exception occurs
                self.assertFalse(result)

    def test_save_settings_file_permission_error(self):
        """Test save_settings when file cannot be written"""
        # Mock get_config_path to return a problematic path
        with patch('utils.get_config_path', return_value="/nonexistent/readonly/settings.ini"):
            # Also mock QSettings to simulate failure
            with patch('security.proxy.QSettings') as MockQSettings:
                mock_settings = MockQSettings.return_value
                mock_settings.status.return_value = QSettings.AccessError
                
                proxy = ProxyManager()
                result = proxy.save_settings()
                
                # Should return False when file cannot be written
                self.assertFalse(result)

    @patch('security.proxy.QSettings')
    def test_save_settings_qsettings_error(self, MockQSettings):
        """Test save_settings when QSettings reports an error"""
        from PySide6.QtCore import QSettings
        
        # Create mock that simulates QSettings error
        mock_settings = MagicMock()
        mock_settings.status.return_value = QSettings.AccessError  # Simulate an error
        MockQSettings.return_value = mock_settings
        
        # Mock get_config_path to return a valid path
        with patch('utils.get_config_path', return_value='/fake/path'):
            proxy = ProxyManager()
            result = proxy.save_settings()
            
            # Should return False when QSettings reports an error
            self.assertFalse(result)
            
            # Verify QSettings methods were called
            self.assertTrue(mock_settings.beginGroup.called)
            self.assertTrue(mock_settings.setValue.called)
            self.assertTrue(mock_settings.endGroup.called)
            self.assertTrue(mock_settings.sync.called)
            self.assertTrue(mock_settings.status.called)

    def test_save_settings_with_default_values(self):
        """Test save_settings uses instance settings when no parameter provided"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch('utils.get_config_path', return_value=temp_path):
                proxy = ProxyManager()
                
                # Modify instance settings
                proxy.settings["enabled"] = True
                proxy.settings["host"] = "proxy.example.com"
                
                # Call save_settings without parameters (should use instance settings)
                result = proxy.save_settings()
                self.assertTrue(result)
                
                # Verify the instance settings were saved
                saved_settings = QSettings(temp_path, QSettings.IniFormat)
                saved_settings.beginGroup("Proxy")
                self.assertEqual(saved_settings.value("enabled", type=bool), True)
                self.assertEqual(saved_settings.value("host", type=str), "proxy.example.com")
                saved_settings.endGroup()
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)