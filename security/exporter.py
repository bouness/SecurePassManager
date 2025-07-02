import csv
import json
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox
from PySide6.QtCore import Qt


class PasswordExporter:
    def __init__(self, db):
        self.db = db
    
    def export_passwords(self, file_path, format_type, parent=None):
        """Export passwords to various formats"""
        if format_type not in ("csv", "json"):
            raise ValueError(f"Unsupported export format: {format_type}")

        try:
            if format_type == "csv":
                return self.export_to_csv(file_path, parent)
            elif format_type == "json":
                return self.export_to_json(file_path, parent)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export passwords: {str(e)}")
            return False
    
    def export_to_csv(self, file_path, parent):
        """Export to generic CSV format"""
        entries = self.db.get_all_entries()
        total = len(entries)
        
        progress = QProgressDialog("Exporting Passwords...", "Cancel", 0, total, parent)
        progress.setWindowTitle("Export Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Service", "Username", "Password", "URL", "Category", "Notes"])
                
                for i, (service, data) in enumerate(entries.items()):
                    if progress.wasCanceled():
                        break
                    
                    writer.writerow([
                        service,
                        data.get('username', ''),
                        data.get('password', ''),
                        data.get('url', ''),
                        data.get('category', ''),
                        data.get('notes', '')
                    ])
                    progress.setValue(i)
            
            progress.close()
            return True
        finally:
            progress.close()
    
    def export_to_json(self, file_path, parent):
        """Export to JSON format"""
        entries = self.db.get_all_entries()
        total = len(entries)
        
        progress = QProgressDialog("Exporting Passwords...", "Cancel", 0, total, parent)
        progress.setWindowTitle("Export Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            export_data = []
            for i, (service, data) in enumerate(entries.items()):
                if progress.wasCanceled():
                    break
                
                export_data.append({
                    "service": service,
                    "username": data.get('username', ''),
                    "password": data.get('password', ''),
                    "url": data.get('url', ''),
                    "category": data.get('category', ''),
                    "notes": data.get('notes', ''),
                    "created": data.get('created', ''),
                    "updated": data.get('updated', '')
                })
                progress.setValue(i)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            progress.close()
            return True
        finally:
            progress.close()

    def get_all_entries(self):
        """Get all password entries"""
        return self.db.get_all_entries()
