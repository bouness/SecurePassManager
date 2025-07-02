from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, 
    QMessageBox, QCheckBox, QHBoxLayout, QFileDialog,
    QGroupBox, QInputDialog
)
from PySide6.QtCore import Qt


class LoginWindow(QDialog):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.setWindowTitle("SecurePass Manager")
        self.setMinimumSize(500, 300)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        layout = QVBoxLayout()
        
        # Database selection group
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)
        
        # Single database path input
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Database Path:"))
        
        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("Select database file...")
        self.db_path_input.setReadOnly(True)
        path_layout.addWidget(self.db_path_input)
        
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.open_database)
        path_layout.addWidget(self.btn_browse)
        
        db_layout.addLayout(path_layout)
        
        layout.addWidget(db_group)
        
        # Password group
        pwd_group = QGroupBox("Authentication")
        pwd_layout = QVBoxLayout(pwd_group)
        
        self.master_pwd = QLineEdit()
        self.master_pwd.setEchoMode(QLineEdit.Password)
        self.master_pwd.setPlaceholderText("Master Password")
        
        # Connect Enter key to authenticate
        self.master_pwd.returnPressed.connect(self.authenticate)
        
        pwd_layout.addWidget(self.master_pwd)
        
        self.show_password = QCheckBox("Show password")
        self.show_password.stateChanged.connect(self.toggle_password_visibility)
        pwd_layout.addWidget(self.show_password)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_unlock = QPushButton("Unlock")
        self.btn_unlock.clicked.connect(self.authenticate)
        
        # Set as default button
        self.btn_unlock.setDefault(True)
        
        btn_layout.addWidget(self.btn_unlock)
        
        self.btn_create = QPushButton("Create New")
        self.btn_create.clicked.connect(self.create_database)
        btn_layout.addWidget(self.btn_create)
        
        pwd_layout.addLayout(btn_layout)
        
        layout.addWidget(pwd_group)
        
        self.setLayout(layout)

    def open_database(self):
        """Open file dialog to select database"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database",
            "",
            "All Files (*)"
        )
        
        if file_path:
            self.db_path_input.setText(file_path)
            self.app_manager.db.db_path = file_path

    def toggle_password_visibility(self, checked):
        if checked:
            self.master_pwd.setEchoMode(QLineEdit.Normal)
            self.show_password.setText("Hide")
        else:
            self.master_pwd.setEchoMode(QLineEdit.Password)
            self.show_password.setText("Show")

    def authenticate(self):
        """Unlock existing database"""
        db_path = self.db_path_input.text()
        if not db_path:
            QMessageBox.warning(self, "Error", "Please select a database file")
            return
            
        password = self.master_pwd.text()
        self.app_manager.crypto.secure_clear(password)
        
        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty!")
            return
        
        try:
            # Set database path in app manager
            self.app_manager.db.db_path = db_path
            
            if self.app_manager.db.unlock(password):
                # Create and show main window
                from gui.main_window import MainWindow
                self.main_window = MainWindow(self.app_manager)
                self.main_window.show()
                
                # Notify app manager that database is unlocked
                self.app_manager.on_database_unlocked(db_path)
                self.close()  # Close login window
            else:
                QMessageBox.critical(self, "Error", "Invalid password or database format")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Decryption failed: {str(e)}")
        finally:
            self.master_pwd.clear()

    def create_database(self):
        """Create new database workflow"""
        # First open save dialog to choose location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create Database",
            "",
            "SecurePass Database (*.spdb);;All Files (*)"
        )
        
        if not file_path:
            return  # User canceled
            
        # Add extension if missing
        if not file_path.endswith(".spdb"):
            file_path += ".spdb"

        # Set database path in app manager
        self.db_path_input.setText(file_path)
        self.app_manager.db.db_path = file_path
        
        # Now prompt for password
        password, ok = QInputDialog.getText(
            self,
            "Create Master Password",
            "Enter a strong master password (min 12 characters):",
            QLineEdit.Password
        )
        
        if not ok or not password:
            return  # User canceled
            
        if len(password) < 12:
            QMessageBox.warning(self, "Weak Password", 
                            "Master password must be at least 12 characters")
            return
            
        try:
            # Initialize will create the new database
            self.app_manager.db.initialize(password)
            QMessageBox.information(self, "Success", f"New database created at:\n{file_path}")
            
            # Now unlock the newly created database
            if self.app_manager.db.unlock(password):
                from gui.main_window import MainWindow
                self.main_window = MainWindow(self.app_manager)
                self.main_window.show()
                
                # Notify app manager that database is unlocked
                self.app_manager.on_database_unlocked(file_path)
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database creation failed: {str(e)}")
        finally:
            # Securely clear password
            self.app_manager.crypto.secure_clear(password)

