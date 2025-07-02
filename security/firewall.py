import os
import sys
import platform
import subprocess
import logging

class FirewallManager:
    def __init__(self):
        self.os_type = platform.system()
        self.active = False
        self.logger = logging.getLogger("SecurePass")
        self.needs_privileges = self._check_privilege_requirement()
    
    def _check_privilege_requirement(self):
        """Check if firewall requires admin privileges to manage"""
        try:
            if self.os_type == "Windows":
                # Windows Firewall doesn't require elevation for status checks
                return False
            elif self.os_type == "Linux":
                # UFW requires sudo for changes but not for status
                result = subprocess.run(
                    ["ufw", "status"], 
                    capture_output=True, 
                    text=True
                )
                return result.returncode != 0 or "inactive" in result.stdout.lower()
            elif self.os_type == "Darwin":
                # PF firewall requires sudo for management
                result = subprocess.run(
                    ["pfctl", "-s", "info"], 
                    capture_output=True, 
                    text=True
                )
                return "Status: Disabled" in result.stdout
        except Exception as e:
            self.logger.error(f"Privilege check error: {e}")
            return True
        return False
    
    def block_incoming(self, use_sudo=False):
        """Block incoming connections with proper privilege handling"""
        try:
            kwargs = {}
            if sys.platform == "win32":
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            if self.os_type == "Windows":
                self._run_windows_block(kwargs)
                self.active = True
                return True
                
            elif self.os_type == "Linux":
                self._run_linux_block(use_sudo)
                self.active = True
                return True
                
            elif self.os_type == "Darwin":
                self._run_macos_block(use_sudo)
                self.active = True
                return True
            
            # Set active status based on success
            self.active = True
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Firewall command failed: {e}")
            self.active = False
            return False        
        except Exception as e:
            self.logger.exception("Unexpected firewall error")
            self.active = False
            return False
    
    def _run_windows_block(self, kwargs):
        """Windows firewall commands"""
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
    
    def _run_linux_block(self, use_sudo):
        """Linux UFW commands"""
        base_cmd = ["sudo"] if use_sudo else []
        subprocess.run(base_cmd + ["ufw", "enable"], check=True)
        subprocess.run(base_cmd + ["ufw", "default", "deny", "incoming"], check=True)
        subprocess.run(base_cmd + ["ufw", "default", "allow", "outgoing"], check=True)
    
    def _run_macos_block(self, use_sudo):
        """macOS PF firewall commands"""
        base_cmd = ["sudo"] if use_sudo else []
        subprocess.run(base_cmd + ["pfctl", "-e"], check=True)
        subprocess.run(base_cmd + ["pfctl", "-f", "/etc/pf.conf"], check=True)
    
    def is_active(self):
        """Check if firewall is active without requiring privileges"""
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
                # Non-privileged status check
                result = subprocess.run(
                    ["ufw", "status"],
                    capture_output=True,
                    text=True
                )
                return "Status: active" in result.stdout
                
            elif self.os_type == "Darwin":
                # Non-privileged status check
                result = subprocess.run(
                    ["pfctl", "-s", "info"],
                    capture_output=True,
                    text=True
                )
                return "Status: Enabled" in result.stdout
            return status_active    
        except Exception as e:
            self.logger.warning(f"Firewall status check failed: {e}")
            return False
        return False