import os
import sys
import logging
import platform
import subprocess
from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtCore import QSettings

from utils import get_config_path, get_app_data_dir

class ProxyManager:
    def __init__(self):
        self.settings = {}
        self.os_type = platform.system()
        self.config_path = get_config_path()
        self.load_settings()
        
    def load_settings(self):
        """Load settings from config file using cross-platform location"""
        logging.debug(f"Loading settings from: {self.config_path}")
        settings = QSettings(str(self.config_path), QSettings.IniFormat)
        
        # Create settings dictionary with defaults and proper types
        self.settings = {
            # Proxy settings
            "enabled": False,
            "type": "HTTP",
            "host": "",
            "port": "",
            "auth_enabled": False,
            "username": "",
            "password": "",
            "system_wide": False,
            
            # Backup settings
            "Backup/enabled": False,
            "Backup/frequency": "Daily",
            "Backup/location": "",

            # Logging settings
            "Logging/config": "Minimal logging",
            "Logging/level": "INFO"
        }

        try:
            # Load proxy settings with type conversion
            settings.beginGroup("Proxy")
            self.settings["enabled"] = settings.value("enabled", False, type=bool)
            self.settings["type"] = settings.value("type", "HTTP", type=str)
            self.settings["host"] = settings.value("host", "", type=str)
            self.settings["port"] = settings.value("port", "", type=str)
            self.settings["auth_enabled"] = settings.value("auth_enabled", False, type=bool)
            self.settings["username"] = settings.value("username", "", type=str)
            self.settings["password"] = settings.value("password", "", type=str)
            self.settings["system_wide"] = settings.value("system_wide", False, type=bool)
            settings.endGroup()
            
            # Load backup settings with type conversion
            settings.beginGroup("Backup")
            self.settings["Backup/enabled"] = settings.value("enabled", False, type=bool)
            self.settings["Backup/frequency"] = settings.value("frequency", "Daily", type=str)
            self.settings["Backup/location"] = settings.value("location", "", type=str)
            settings.endGroup()

            # Load logging settings
            settings.beginGroup("Logging")
            self.settings["Logging/config"] = settings.value("config", "Minimal logging", type=str)
            log_level = settings.value("level", "INFO", type=str)
            if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                self.settings["Logging/level"] = log_level
            else:
                self.settings["Logging/level"] = "INFO"  # Enforce valid value
            settings.endGroup()

            logging.debug(f"Loaded settings: {self.settings}")

        except Exception as e:
            logging.error(f"Error loading settings: {e}")
        
        return self.settings
    
    def save_settings(self, settings=None):
        """Save settings to config file using cross-platform location"""
        if settings is None:
            settings = self.settings
        
        logging.debug(f"Saving settings to: {self.config_path}")
        
        try:
            qsettings = QSettings(str(self.config_path), QSettings.IniFormat)

            # Save proxy settings
            qsettings.beginGroup("Proxy")
            qsettings.setValue("enabled", settings["enabled"])
            qsettings.setValue("type", settings["type"])
            qsettings.setValue("host", settings["host"])
            qsettings.setValue("port", settings["port"])
            qsettings.setValue("auth_enabled", settings["auth_enabled"])
            qsettings.setValue("username", settings["username"])
            qsettings.setValue("password", settings["password"])
            qsettings.setValue("system_wide", settings["system_wide"])
            qsettings.endGroup()
            
            # Save backup settings
            qsettings.beginGroup("Backup")
            qsettings.setValue("enabled", settings.get("Backup/enabled", False))
            qsettings.setValue("frequency", settings.get("Backup/frequency", "Daily"))
            qsettings.setValue("location", settings.get("Backup/location", ""))
            qsettings.endGroup()

            # Save logging settings
            qsettings.beginGroup("Logging")
            qsettings.setValue("config", settings.get("Logging/config", "Minimal logging"))
            qsettings.setValue("level", settings.get("Logging/level", "INFO"))
            qsettings.endGroup()
            
            # Force immediate write to disk
            qsettings.sync()

            # Verify settings were saved
            if qsettings.status() != QSettings.NoError:
                logging.error(f"Failed to save settings: QSettings error {qsettings.status()}")
                return False
                
            logging.info("Settings saved successfully")            
            return True
        except Exception as e:
            logging.error(f"Failed to save settings: {e}", exc_info=True)
            return False

    def set_application_proxy(self, settings=None):
        """Set application-level proxy using Qt's network stack"""
        if settings is None:
            settings = self.settings
        
        if not settings["enabled"]:
            QNetworkProxy.setApplicationProxy(QNetworkProxy.NoProxy)
            return
        
        # Map proxy type string to Qt enum
        proxy_type_map = {
            "HTTP": QNetworkProxy.HttpProxy,
            "HTTPS": QNetworkProxy.HttpProxy,
            "SOCKS5": QNetworkProxy.Socks5Proxy
        }
        
        proxy_type = proxy_type_map.get(settings["type"], QNetworkProxy.HttpProxy)
        
        proxy = QNetworkProxy()
        proxy.setType(proxy_type)
        proxy.setHostName(settings["host"])
        
        try:
            port = int(settings["port"])
        except (TypeError, ValueError):
            port = 0
        
        proxy.setPort(port)
        
        if settings["auth_enabled"]:
            proxy.setUser(settings["username"])
            proxy.setPassword(settings["password"])
        
        QNetworkProxy.setApplicationProxy(proxy)

    def set_system_proxy(self, settings=None):
        """Set system-level proxy (if supported)"""
        if settings is None:
            settings = self.settings
        
        if not settings["enabled"] or not settings["system_wide"]:
            self.clear_system_proxy()
            return
        
        host = settings["host"]
        port = settings["port"]
        proxy_url = f"http://{host}:{port}"
        
        os_type = self.os_type
        try:
            if os_type == "Windows":
                kwargs = {}
                if sys.platform == "win32":
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

                subprocess.run(
                    f"netsh winhttp set proxy {host}:{port}", 
                    shell=True, 
                    check=True,
                    **kwargs
                )
            elif os_type == "Darwin":  # macOS
                networksetup_cmd = f"networksetup -setwebproxy Wi-Fi {host} {port}"
                subprocess.run(networksetup_cmd, shell=True, check=True)
            elif os_type == "Linux":
                os.environ["http_proxy"] = proxy_url
                os.environ["https_proxy"] = proxy_url
                os.environ["HTTP_PROXY"] = proxy_url
                os.environ["HTTPS_PROXY"] = proxy_url

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"System proxy error: {e}")
            return False
        return True

    def clear_system_proxy(self):
        """Clear system-level proxy settings"""
        os_type = platform.system()
        try:
            if os_type == "Windows":
                subprocess.run(
                    "netsh winhttp reset proxy", 
                    shell=True, 
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif os_type == "Darwin":  # macOS
                subprocess.run("networksetup -setwebproxystate Wi-Fi off", shell=True, check=True)
            elif os_type == "Linux":
                for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
                    os.environ.pop(var, None)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"Clear proxy error: {e}")
            return False
        return True
