# security/importer.py
import csv
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from cryptography.fernet import Fernet
from PySide6.QtWidgets import QProgressDialog, QMessageBox
from PySide6.QtCore import Qt


class PasswordImporter:
    def __init__(self, crypto_manager, db):
        self.crypto = crypto_manager
        self.db = db
    
    def import_passwords(self, file_path, format_type, parent=None):
        """Import passwords from various formats"""
        try:
            if format_type == "lastpass":
                return self.import_lastpass(file_path, parent)
            elif format_type == "bitwarden":
                return self.import_bitwarden(file_path, parent)
            elif format_type == "1password":
                return self.import_1password(file_path, parent)
            elif format_type == "chrome":
                return self.import_chrome(file_path, parent)
            elif format_type == "firefox":
                return self.import_firefox(file_path, parent)
            elif format_type in ("csv", "generic_csv"):
                return self.import_generic_csv(file_path, parent)
            elif format_type in ("json", "generic_json"):
                return self.import_generic_json(file_path, parent)
            else:
                raise ValueError(f"Unsupported import format: {format_type}")
        except Exception as e:
            QMessageBox.critical(parent, "Import Error", f"Failed to import passwords: {str(e)}")
            return False
    
    def import_lastpass(self, file_path, parent):
        """Import from LastPass CSV format"""
        imported_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            # Detect header
            header = f.readline().strip().split(',')
            if "url" not in header or "username" not in header or "password" not in header:
                raise ValueError("Invalid LastPass CSV format")
            
            # Create progress dialog
            total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8')) - 1
            progress = QProgressDialog("Importing LastPass Passwords...", "Cancel", 0, total_lines, parent)
            progress.setWindowTitle("Import Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Reset file pointer
            f.seek(0)
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if progress.wasCanceled():
                    break
                
                # Map LastPass fields to our structure
                service = row.get('name', row.get('url', ''))
                username = row.get('username', '')
                password = row.get('password', '')
                url = row.get('url', '')
                notes = row.get('extra', '')
                category = row.get('grouping', 'Imported')
                
                # Add to database
                if service and password:
                    self.db.add_password(
                        service, 
                        username, 
                        password, 
                        category,
                        url,
                        notes
                    )
                    imported_count += 1
                
                progress.setValue(i)
        
        progress.close()
        return imported_count
    
    def import_bitwarden(self, file_path, parent):
        """Import from Bitwarden JSON format"""
        imported_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Create progress dialog
            total_items = len(data.get('items', []))
            progress = QProgressDialog("Importing Bitwarden Passwords...", "Cancel", 0, total_items, parent)
            progress.setWindowTitle("Import Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            for i, item in enumerate(data.get('items', [])):
                if progress.wasCanceled():
                    break
                
                # Skip non-login items
                if item.get('type') != 1:
                    continue
                
                # Extract login information
                login_info = item.get('login', {})
                service = item.get('name', '')
                username = login_info.get('username', '')
                password = login_info.get('password', '')
                url = login_info.get('uris', [{}])[0].get('uri', '') if login_info.get('uris') else ''
                notes = item.get('notes', '')
                
                # Add to database
                if service and password:
                    self.db.add_password(
                        service, 
                        username, 
                        password, 
                        "Imported",
                        url,
                        notes
                    )
                    imported_count += 1
                
                progress.setValue(i)
        
        progress.close()
        return imported_count
    
    def import_1password(self, file_path, parent):
        """Import from 1Password 1PUX format"""
        imported_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Create progress dialog
            total_items = len(data.get('items', []))
            progress = QProgressDialog("Importing 1Password Passwords...", "Cancel", 0, total_items, parent)
            progress.setWindowTitle("Import Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            for i, item in enumerate(data.get('items', [])):
                if progress.wasCanceled():
                    break
                
                # Skip non-login items
                if item.get('category') != 'LOGIN':
                    continue
                
                # Extract fields
                service = item.get('title', '')
                username = ''
                password = ''
                url = ''
                notes = ''
                
                # Parse fields
                for field in item.get('fields', []):
                    if field.get('designation') == 'username':
                        username = field.get('value', '')
                    elif field.get('designation') == 'password':
                        password = field.get('value', '')
                
                # Parse URLs
                for url_field in item.get('urls', []):
                    url = url_field.get('href', '')
                    if url:
                        break
                
                # Add to database
                if service and password:
                    self.db.add_password(
                        service, 
                        username, 
                        password, 
                        "Imported",
                        url,
                        notes
                    )
                    imported_count += 1
                
                progress.setValue(i)
        
        progress.close()
        return imported_count
    
    def import_chrome(self, file_path, parent):
        """Import from Chrome CSV export"""
        return self.import_generic_csv(file_path, parent, expected_headers=["name", "url", "username", "password"])
    
    def import_firefox(self, file_path, parent):
        """Import from Firefox CSV export"""
        return self.import_generic_csv(file_path, parent, expected_headers=["url", "username", "password"])
    
    def import_generic_csv(self, file_path, parent, expected_headers=None):
        """Generic CSV importer with header detection"""
        imported_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            # Detect header
            header_line = f.readline().strip()
            dialect = csv.Sniffer().sniff(header_line)
            f.seek(0)
            
            reader = csv.DictReader(f, dialect=dialect)
            fieldnames = reader.fieldnames
            
            # Validate headers
            if expected_headers:
                missing = [h for h in expected_headers if h.lower() not in [f.lower() for f in fieldnames]]
                if missing:
                    raise ValueError(f"Missing required headers: {', '.join(missing)}")
            
            # Create progress dialog
            total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8')) - 1
            progress = QProgressDialog("Importing Passwords...", "Cancel", 0, total_lines, parent)
            progress.setWindowTitle("Import Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Field mapping
            service_field = self._detect_field(fieldnames, ["name", "title", "service", "website"])
            user_field = self._detect_field(fieldnames, ["username", "user", "login", "email"])
            pass_field = self._detect_field(fieldnames, ["password", "pass", "pwd", "secret"])
            url_field = self._detect_field(fieldnames, ["url", "website", "link"])
            notes_field = self._detect_field(fieldnames, ["notes", "comment", "description"])
            
            for i, row in enumerate(reader):
                if progress.wasCanceled():
                    break
                
                if not pass_field or not service_field:
                    raise ValueError("Could not detect required fields (service or password)")
                    
                service = row.get(service_field, '')
                username = row.get(user_field, '')
                password = row.get(pass_field, '')
                url = row.get(url_field, '')
                notes = row.get(notes_field, '')
                
                # Add to database
                if service and password:
                    self.db.add_password(
                        service, 
                        username, 
                        password, 
                        "Imported",
                        url,
                        notes
                    )
                    imported_count += 1
                
                progress.setValue(i)
        
        progress.close()
        return imported_count

    def import_generic_json(self, file_path, parent, expected_keys=None):
        """Generic JSON importer with key detection"""
        imported_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, list):
            raise ValueError("JSON must be a list of objects")

        # Validate keys
        all_keys = set()
        for entry in data:
            if isinstance(entry, dict):
                all_keys.update(entry.keys())
        if expected_keys:
            missing = [k for k in expected_keys if k.lower() not in [key.lower() for key in all_keys]]
            if missing:
                raise ValueError(f"Missing required keys: {', '.join(missing)}")

        # Create progress dialog
        total_items = len(data)
        progress = QProgressDialog("Importing Passwords...", "Cancel", 0, total_items, parent)
        progress.setWindowTitle("Import Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        # Field mapping
        service_field = self._detect_field(all_keys, ["name", "title", "service", "website"])
        user_field = self._detect_field(all_keys, ["username", "user", "login", "email"])
        pass_field = self._detect_field(all_keys, ["password", "pass", "pwd", "secret"])
        url_field = self._detect_field(all_keys, ["url", "website", "link"])
        notes_field = self._detect_field(all_keys, ["notes", "comment", "description"])

        for i, entry in enumerate(data):
            if progress.wasCanceled():
                break

            if not isinstance(entry, dict):
                continue

            if not pass_field or not service_field:
                raise ValueError("Could not detect required fields (service or password)")

            service = entry.get(service_field, '')
            username = entry.get(user_field, '')
            password = entry.get(pass_field, '')
            url = entry.get(url_field, '')
            notes = entry.get(notes_field, '')

            # Add to database
            if service and password:
                self.db.add_password(
                    service,
                    username,
                    password,
                    "Imported",
                    url,
                    notes
                )
                imported_count += 1

            progress.setValue(i + 1)

        progress.close()
        return imported_count


    def _detect_field(self, fieldnames, candidates):
        """Find the best matching field from candidates"""
        # Create a normalized list of fieldnames
        normalized_fields = [f.lower() for f in fieldnames]
        
        # Try exact match first
        for candidate in candidates:
            if candidate in fieldnames:
                return candidate
        
        # Try case-insensitive match
        for candidate in candidates:
            candidate_lower = candidate.lower()
            if candidate_lower in normalized_fields:
                return fieldnames[normalized_fields.index(candidate_lower)]
        
        # Try partial match and common abbreviations
        for candidate in candidates:
            candidate_lower = candidate.lower()
            for i, field in enumerate(normalized_fields):
                # Handle common abbreviations like "pwd" for "password"
                if candidate_lower in field:
                    return fieldnames[i]
        
        return None