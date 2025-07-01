# security/firewall.py
import os
import sys
import platform
import subprocess
from PySide6.QtWidgets import QMessageBox

class FirewallManager:
    def __init__(self):
        self.os_type = platform.system()
        self.active = False
    
    def block_incoming(self):
        """Block incoming connections with proper privilege handling"""
        try:
            kwargs = {}
            if sys.platform == "win32":
                # Only add CREATE_NO_WINDOW on Windows
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            if self.os_type == "Windows":
                subprocess.run(
                    ["netsh", "advfirewall", "set", "allprofiles", "state", "on"],
                    check=True,
                    **kwargs
                )
                subprocess.run(
                    ["netsh", "advfirewall", "set", "allprofiles", "firewallpolicy", "blockinbound,allowoutbound"],
                    check=True,
                    **kwargs
                )
                self.active = True
                return True
                
            elif self.os_type == "Linux":
                subprocess.run(["sudo", "ufw", "enable"], check=True)
                subprocess.run(["sudo", "ufw", "default", "deny", "incoming"], check=True)
                subprocess.run(["sudo", "ufw", "default", "allow", "outgoing"], check=True)
                self.active = True
                return True
                
            elif self.os_type == "Darwin":
                subprocess.run(["sudo", "pfctl", "-e"], check=True)
                subprocess.run(["sudo", "pfctl", "-f", "/etc/pf.conf"], check=True)
                self.active = True
                return True
            
            self.active = True
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Return False but don't show error here - handled in main app
            self.active = False
            return False        
        except Exception as e:  # Catch all exceptions
            self.active = False
            return False
    
    def _run_windows_block(self):
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        subprocess.run(
            ["netsh", "advfirewall", "set", "allprofiles", "state", "on"],
            check=True,
            **kwargs
        )
        subprocess.run(
            ["netsh", "advfirewall", "set", "allprofiles", "firewallpolicy", "blockinbound,allowoutbound"],
            check=True,
            **kwargs
        )
    
    def _run_linux_block(self):
        subprocess.run(["sudo", "ufw", "enable"], check=True)
        subprocess.run(["sudo", "ufw", "default", "deny", "incoming"], check=True)
        subprocess.run(["sudo", "ufw", "default", "allow", "outgoing"], check=True)
    
    def _run_macos_block(self):
        subprocess.run(["sudo", "pfctl", "-e"], check=True)
        subprocess.run(["sudo", "pfctl", "-f", "/etc/pf.conf"], check=True)
    
    def is_active(self):
        """Check if firewall is active with better error handling"""
        try:
            if self.os_type == "Windows":
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return "ON" in result.stdout and "OFF" not in result.stdout
                
            elif self.os_type == "Linux":
                result = subprocess.run(
                    ["sudo", "ufw", "status", "verbose"],
                    capture_output=True,
                    text=True
                )
                return "Status: active" in result.stdout and "Default: deny (incoming)" in result.stdout
                
            elif self.os_type == "Darwin":
                result = subprocess.run(
                    ["sudo", "pfctl", "-s", "info"],
                    capture_output=True,
                    text=True
                )
                return "Status: Enabled" in result.stdout
                
        except Exception:
            return False
        return False