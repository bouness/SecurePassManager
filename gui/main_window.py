import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QLineEdit,
    QLabel,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QSplitter,
    QListWidgetItem,
    QToolBar,
    QStatusBar,
    QApplication,
    QProgressBar,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QSize, QSettings, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QAction, QKeySequence, QIntValidator, QFont, QPalette

from gui.about_dialog import AboutDialog
from gui.help_dialog import HelpDialog
from security.importer import PasswordImporter
from security.exporter import PasswordExporter
from utils import resource_path


class ImportDialog(QDialog):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle("Import Passwords")
        self.setFixedSize(450, 350)
        
        # Modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid palette(mid);
                border-radius: 6px;
                background-color: palette(button);
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
            QComboBox {
                padding: 6px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title with emoji
        title_label = QLabel("📥 Import Passwords")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Format selection
        format_label = QLabel("Select import format:")
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "📊 LastPass (CSV)",
            "🔐 Bitwarden (JSON)",
            "🏷️ 1Password (1PUX)",
            "🌐 Chrome (CSV)",
            "🦊 Firefox (CSV)",
            "📄 Generic JSON",
            "📊 Generic CSV",
        ])
        layout.addWidget(self.format_combo)

        # File selection
        file_label = QLabel("Select file to import:")
        layout.addWidget(file_label)
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("No file selected...")
        layout.addWidget(self.file_path)

        browse_button = QPushButton("📁 Browse...")
        browse_button.clicked.connect(self.browse_file)
        layout.addWidget(browse_button)

        # Import button
        import_button = QPushButton("📥 Import Passwords")
        import_button.clicked.connect(self.import_passwords)
        import_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(import_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: palette(text); font-style: italic;")
        layout.addWidget(self.status_label)

        # Cancel button
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select import file"""
        format_map = {
            "📊 LastPass (CSV)": "CSV Files (*.csv)",
            "🔐 Bitwarden (JSON)": "JSON Files (*.json)",
            "🏷️ 1Password (1PUX)": "1PUX Files (*.1pux)",
            "🌐 Chrome (CSV)": "CSV Files (*.csv)",
            "🦊 Firefox (CSV)": "CSV Files (*.csv)",
            "📄 Generic JSON": "JSON Files (*.json)",
            "📊 Generic CSV": "CSV Files (*.csv)",
        }

        current_format = self.format_combo.currentText()
        file_filter = format_map.get(current_format, "All Files (*.*)")

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Import File", "", file_filter
        )

        if file_path:
            self.file_path.setText(file_path)

    def import_passwords(self):
        """Perform the import operation"""
        file_path = self.file_path.text()
        if not file_path:
            QMessageBox.warning(self, "Import Error", "Please select a file to import")
            return

        format_map = {
            "📊 LastPass (CSV)": "lastpass",
            "🔐 Bitwarden (JSON)": "bitwarden",
            "🏷️ 1Password (1PUX)": "1password",
            "🌐 Chrome (CSV)": "chrome",
            "🦊 Firefox (CSV)": "firefox",
            "📄 Generic JSON": "json",
            "📊 Generic CSV": "csv",
        }

        format_type = format_map.get(self.format_combo.currentText())
        if not format_type:
            QMessageBox.critical(self, "Import Error", "Invalid import format selected")
            return

        importer = PasswordImporter(self.app_manager.crypto, self.app_manager.db)
        count = importer.import_passwords(file_path, format_type, self)

        if count is not False:
            self.status_label.setText(f"✅ Successfully imported {count} passwords!")
            # Refresh UI
            self.parent().load_passwords()

            # Auto-close after success
            QTimer.singleShot(3000, self.accept)


class ExportDialog(QDialog):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.setWindowTitle("Export Passwords")
        self.setFixedSize(450, 300)
        
        # Modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid palette(mid);
                border-radius: 6px;
                background-color: palette(button);
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
            QComboBox {
                padding: 6px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title with emoji
        title_label = QLabel("📤 Export Passwords")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Format selection
        format_label = QLabel("Select export format:")
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["📊 CSV", "📄 JSON"])
        layout.addWidget(self.format_combo)

        # File selection
        file_label = QLabel("Select export location:")
        layout.addWidget(file_label)
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("No location selected...")
        layout.addWidget(self.file_path)

        browse_button = QPushButton("📁 Browse...")
        browse_button.clicked.connect(self.browse_file)
        layout.addWidget(browse_button)

        # Export button
        export_button = QPushButton("📤 Export Passwords")
        export_button.clicked.connect(self.export_passwords)
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(export_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: palette(text); font-style: italic;")
        layout.addWidget(self.status_label)

        # Cancel button
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select export location"""
        format_map = {"📊 CSV": ("CSV Files (*.csv)", ".csv"), "📄 JSON": ("JSON Files (*.json)", ".json")}

        current_format = self.format_combo.currentText()
        if current_format in format_map:
            file_filter, default_ext = format_map[current_format]
        else:
            file_filter = "All Files (*.*)"
            default_ext = ""

        # Suggest a default file name with extension
        default_name = f"SecurePass_Export_{datetime.now().strftime('%Y%m%d')}{default_ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Passwords", default_name, file_filter
        )

        if file_path:
            # Ensure the correct extension is added
            root, ext = os.path.splitext(file_path)
            if not ext or ext.lower() != default_ext.lower():
                file_path += default_ext
            self.file_path.setText(file_path)

    def export_passwords(self):
        """Perform the export operation"""
        file_path = self.file_path.text()
        if not file_path:
            QMessageBox.warning(self, "Export Error", "Please select an export location")
            return

        format_type = self.format_combo.currentText().split()[1].lower()  # Remove emoji

        exporter = PasswordExporter(self.app_manager.db)
        success = exporter.export_passwords(file_path, format_type, self)

        if success:
            self.status_label.setText("✅ Passwords exported successfully!")
            # Auto-close after success
            QTimer.singleShot(3000, self.accept)


class ModernTreeWidget(QTreeWidget):
    """Custom tree widget with modern styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 6px;
                outline: none;
                font-size: 13px;
                padding: 2px;
            }
            QTreeWidget::item {
                padding: 4px 2px;
                border-radius: 2px;
                margin: 1px;
            }
            QTreeWidget::item:hover {
                background-color: palette(light);
            }
            QTreeWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QTreeWidget::branch {
                width: 16px;
            }
        """)
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setRootIsDecorated(True)
        self.setUniformRowHeights(False)


class MainWindow(QMainWindow):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.setWindowTitle("🔐 SecurePass Manager")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 500)

        # Category emoji mapping
        self.category_emojis = {
            "Social": "👥",
            "Email": "📧",
            "Work": "💼",
            "Finance": "💰",
            "Shopping": "🛒",
            "Gaming": "🎮",
            "Streaming": "📺",
            "Developer": "💻",
            "Travel": "✈️",
            "Health": "🏥",
            "Government": "🏛️",
            "Miscellaneous": "📝",
        }

        # Apply modern styling
        self.apply_modern_styling()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create splitter for resizable panels
        splitter = QSplitter()
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: palette(mid);
                width: 2px;
                margin: 0px 2px;
            }
            QSplitter::handle:hover {
                background-color: palette(highlight);
            }
        """)
        main_layout.addWidget(splitter)

        # Left panel: Password tree view with search
        left_panel = self.create_left_panel()
        
        # Right panel: Password details
        right_panel = self.create_right_panel()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])

        # Create modern toolbar
        self.create_modern_toolbar()

        # Create status bar
        self.create_status_bar()

        # Initialize UI state
        self.current_password = None
        self.current_service = None
        self.clear_clipboard_timer = None
        self.copied_password = ""
        
        # Clipboard timer and progress
        self.clipboard_timer = QTimer()
        self.clipboard_timer.setInterval(1000)  # 1 second
        self.clipboard_timer.timeout.connect(self.update_clipboard_progress)
        self.clipboard_seconds_left = 0

        self.load_passwords()

    def apply_modern_styling(self):
        """Apply modern styling to the main window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: palette(window);
            }
            QWidget {
                font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid palette(mid);
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: palette(base);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: palette(text);
            }
            QPushButton {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: palette(light);
                border-color: palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
            QPushButton:disabled {
                background-color: palette(mid);
                color: palette(mid);
            }
            QLineEdit {
                border: 2px solid palette(mid);
                border-radius: 6px;
                padding: 8px 12px;
                background-color: palette(base);
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: palette(highlight);
            }
            QComboBox {
                border: 2px solid palette(mid);
                border-radius: 6px;
                padding: 8px 12px;
                background-color: palette(base);
                min-width: 6em;
            }
            QComboBox:focus {
                border-color: palette(highlight);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid palette(mid);
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid palette(text);
            }
        """)

    def create_left_panel(self):
        """Create the left panel with tree view"""
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        # Search bar with icon
        search_container = QHBoxLayout()
        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 16px; color: palette(mid);")
        search_container.addWidget(search_label)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search passwords...")
        self.search_bar.textChanged.connect(self.filter_passwords)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 2px solid palette(mid);
                border-radius: 20px;
                padding: 8px 15px;
                background-color: palette(window);
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: palette(highlight);
                background-color: palette(base);
            }
        """)
        search_container.addWidget(self.search_bar)
        left_layout.addLayout(search_container)

        # Tree widget for categories and passwords
        self.password_tree = ModernTreeWidget()
        self.password_tree.itemSelectionChanged.connect(self.load_selected_password)
        self.password_tree.itemDoubleClicked.connect(self.load_selected_password)
        left_layout.addWidget(self.password_tree)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_add = QPushButton("➕ Add")
        self.btn_add.clicked.connect(self.add_password)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏️ Edit")
        self.btn_edit.clicked.connect(self.edit_password)
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.clicked.connect(self.delete_password)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        btn_layout.addWidget(self.btn_delete)
        
        left_layout.addLayout(btn_layout)

        return left_panel

    def create_right_panel(self):
        """Create the right panel with password details"""
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.StyledPanel)
        # right_panel.setStyleSheet("""
        #     QFrame {
        #         background-color: palette(base);
        #         border: 1px solid palette(mid);
        #         border-radius: 6px;
        #     }
        # """)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(12)

        # Password details group
        self.details_group = QGroupBox("🔐 Password Details")
        details_layout = QFormLayout(self.details_group)
        details_layout.setSpacing(12)
        details_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Category combo box
        self.category_combo = QComboBox()
        category_items = []
        for category, emoji in self.category_emojis.items():
            category_items.append(f"{emoji} {category}")
        self.category_combo.addItems(category_items)
        details_layout.addRow("📂 Category:", self.category_combo)

        # Service field
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("Enter service name...")
        details_layout.addRow("🏷️ Service:", self.service_input)

        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username or email...")
        details_layout.addRow("👤 Username:", self.username_input)

        # Password field with show/hide button
        password_container = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password...")
        self.password_input.textChanged.connect(lambda: self.update_strength_indicator(self.password_input.text()))
        password_container.addWidget(self.password_input)
        
        self.show_password = QPushButton("👁️")
        self.show_password.setCheckable(True)
        self.show_password.toggled.connect(self.toggle_password_visibility)
        self.show_password.setFixedSize(44, 44)
        self.show_password.setStyleSheet("""
            QPushButton {
                border-radius: 5px;
                background-color: palette(mid);
            }
            QPushButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        password_container.addWidget(self.show_password)
        details_layout.addRow("🔑 Password:", password_container)

        # URL field
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        details_layout.addRow("🌐 URL:", self.url_input)

        # Notes field
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Additional notes...")
        details_layout.addRow("📝 Notes:", self.notes_input)

        # Password strength indicator
        self.strength_label = QLabel("Password Strength: -")
        self.strength_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                background-color: palette(window);
            }
        """)
        details_layout.addRow("💪 Strength:", self.strength_label)

        # Save/Cancel buttons
        btn_save_layout = QHBoxLayout()
        btn_save_layout.setSpacing(10)
        
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.clicked.connect(self.save_password)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_save_layout.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("❌ Cancel")
        self.btn_cancel.clicked.connect(self.clear_form)
        btn_save_layout.addWidget(self.btn_cancel)
        
        details_layout.addRow(btn_save_layout)

        # Copy buttons
        copy_layout = QHBoxLayout()
        copy_layout.setSpacing(10)
        
        self.btn_copy_user = QPushButton("📋 Copy Username")
        self.btn_copy_user.clicked.connect(self.copy_username)
        self.btn_copy_user.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        copy_layout.addWidget(self.btn_copy_user)

        self.btn_copy_pass = QPushButton("🔐 Copy Password")
        self.btn_copy_pass.clicked.connect(self.copy_password)
        self.btn_copy_pass.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        copy_layout.addWidget(self.btn_copy_pass)
        
        details_layout.addRow(copy_layout)

        right_layout.addWidget(self.details_group)
        
        # Add spacer to push everything to top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        right_layout.addItem(spacer)

        return right_panel

    def create_modern_toolbar(self):
        """Create a modern toolbar with emoji icons"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet("""
            QToolBar {
                background: palette(window);
                border: none;
                spacing: 8px;
                padding: 8px;
            }
            QToolButton {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 8px 12px;
                margin: 2px;
                font-weight: 500;
            }
            QToolButton:hover {
                background-color: palette(light);
                border-color: palette(highlight);
            }
            QToolButton:pressed {
                background-color: palette(dark);
            }
        """)
        self.addToolBar(toolbar)

        # Security actions
        lock_action = QAction("🔒 Lock Database", self)
        lock_action.triggered.connect(self.lock_database)
        lock_action.setShortcut(QKeySequence("Ctrl+L"))
        toolbar.addAction(lock_action)
        toolbar.addSeparator()

        # Backup action
        backup_action = QAction("💾 Backup Now", self)
        backup_action.triggered.connect(self.perform_backup_now)
        toolbar.addAction(backup_action)
        toolbar.addSeparator()

        # Password actions
        generate_action = QAction("🎲 Generate Password", self)
        generate_action.triggered.connect(self.generate_password)
        generate_action.setShortcut(QKeySequence("Ctrl+G"))
        toolbar.addAction(generate_action)
        toolbar.addSeparator()

        # Import/Export actions
        import_action = QAction("📥 Import", self)
        import_action.triggered.connect(self.show_import_dialog)
        toolbar.addAction(import_action)

        export_action = QAction("📤 Export", self)
        export_action.triggered.connect(self.show_export_dialog)
        toolbar.addAction(export_action)
        toolbar.addSeparator()

        # Settings
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        toolbar.addSeparator()

        # Help actions
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

        help_action = QAction("❓ Help", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)

    def create_status_bar(self):
        """Create a modern status bar"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: palette(window);
                border-top: 1px solid palette(mid);
                padding: 4px;
            }
            QLabel {
                padding: 2px 8px;
            }
        """)
        self.setStatusBar(self.status_bar)

        # Database info
        self.db_info = QLabel()
        self.db_info.setStyleSheet("font-weight: 500;")
        self.status_bar.addWidget(self.db_info)

        # Clipboard progress bar
        self.clipboard_progress = QProgressBar()
        self.clipboard_progress.setFixedWidth(200)
        self.clipboard_progress.setMinimum(0)
        self.clipboard_progress.setMaximum(30)
        self.clipboard_progress.setFormat("Clearing in %vs")
        self.clipboard_progress.setAlignment(Qt.AlignCenter)
        self.clipboard_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid palette(mid);
                border-radius: 6px;
                text-align: center;
                background: palette(base);
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 4px;
            }
        """)
        self.clipboard_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.clipboard_progress)

        # Backup status
        self.backup_status = QLabel()
        self.backup_status.setToolTip("Last backup status")
        self.backup_status.setStyleSheet("color: palette(mid);")
        self.status_bar.addPermanentWidget(self.backup_status)
        
        self.update_db_info()
        self.update_backup_status()

        # Connect backup signals
        if hasattr(self.app_manager, "backup_manager"):
            self.app_manager.backup_manager.backup_performed.connect(self.on_backup_performed)
            self.app_manager.backup_manager.backup_failed.connect(self.on_backup_failed)

    def load_passwords(self):
        """Load all passwords into the tree widget organized by category"""
        self.password_tree.clear()

        # Check if database is loaded and has data
        if not hasattr(self.app_manager.db, "data") or not self.app_manager.db.data:
            self.status_bar.showMessage("Database is empty")
            self.update_db_info()
            return

        # Group passwords by category
        categories = {}
        for service, entry in self.app_manager.db.data.items():
            category = entry.get("category", "Miscellaneous")
            if category not in categories:
                categories[category] = []
            categories[category].append((service, entry))

        # Create category nodes
        for category, services in sorted(categories.items()):
            emoji = self.category_emojis.get(category, "📝")
            category_item = QTreeWidgetItem([f"{emoji} {category} ({len(services)})"])
            category_item.setData(0, Qt.UserRole, f"category:{category}")
            
            # Style category items
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            self.password_tree.addTopLevelItem(category_item)

            # Add password entries under category
            for service, entry in sorted(services, key=lambda x: x[0].lower()):
                username = entry.get("username", "")
                service_item = QTreeWidgetItem([f"🔑 {service}"])
                service_item.setData(0, Qt.UserRole, f"service:{service}")
                service_item.setToolTip(0, f"Service: {service}\nUsername: {username}" if username else service)
                category_item.addChild(service_item)

        # Expand all categories
        self.password_tree.expandAll()
        
        self.update_db_info()
        self.status_bar.showMessage(f"Loaded {len(self.app_manager.db.data)} passwords")

    def filter_passwords(self):
        """Filter password tree based on search text"""
        search_text = self.search_bar.text().lower()
        
        if not search_text:
            # Show all items
            for i in range(self.password_tree.topLevelItemCount()):
                category_item = self.password_tree.topLevelItem(i)
                category_item.setHidden(False)
                for j in range(category_item.childCount()):
                    service_item = category_item.child(j)
                    service_item.setHidden(False)
            return

        # Filter based on search text
        for i in range(self.password_tree.topLevelItemCount()):
            category_item = self.password_tree.topLevelItem(i)
            category_has_match = False
            
            for j in range(category_item.childCount()):
                service_item = category_item.child(j)
                service_data = service_item.data(0, Qt.UserRole)
                
                if service_data and service_data.startswith("service:"):
                    service_name = service_data.split(":", 1)[1]
                    entry = self.app_manager.db.get_password(service_name) or {}
                    
                    # Search in service name, username, and category
                    username = entry.get("username", "").lower()
                    category = entry.get("category", "").lower()
                    
                    match = (search_text in service_name.lower() or 
                            search_text in username or 
                            search_text in category)
                    
                    service_item.setHidden(not match)
                    if match:
                        category_has_match = True
            
            category_item.setHidden(not category_has_match)

    def load_selected_password(self):
        """Load selected password details into form"""
        current_item = self.password_tree.currentItem()
        if not current_item:
            return

        item_data = current_item.data(0, Qt.UserRole)
        if not item_data or not item_data.startswith("service:"):
            return

        service = item_data.split(":", 1)[1]
        self.current_service = service

        entry = self.app_manager.db.get_password(service)
        if not entry:
            return

        self.service_input.setText(service)
        self.username_input.setText(entry.get("username", ""))
        self.password_input.setText(entry.get("password", ""))
        self.url_input.setText(entry.get("url", ""))
        self.notes_input.setText(entry.get("notes", ""))

        # Set category
        category = entry.get("category", "Miscellaneous")
        emoji = self.category_emojis.get(category, "📝")
        category_text = f"{emoji} {category}"
        
        index = self.category_combo.findText(category_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        self.update_strength_indicator(entry.get("password", ""))
        self.service_input.setEnabled(True)

    def add_password(self):
        """Clear form for new password entry"""
        self.current_service = None
        self.service_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.url_input.clear()
        self.notes_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.service_input.setEnabled(True)
        self.service_input.setFocus()
        self.strength_label.setText("Password Strength: -")
        self.password_tree.clearSelection()
        self.status_bar.showMessage("Ready to add new password")

    def edit_password(self):
        """Edit selected password"""
        current_item = self.password_tree.currentItem()
        if current_item:
            self.load_selected_password()

    def save_password(self):
        """Save current password to database"""
        new_service = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        url = self.url_input.text().strip()
        notes = self.notes_input.text().strip()
        
        # Extract category from combo box (remove emoji)
        category_text = self.category_combo.currentText()
        category = category_text.split(" ", 1)[1] if " " in category_text else category_text

        if not new_service:
            QMessageBox.warning(self, "Error", "Service name is required!")
            return

        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty!")
            return

        try:
            # Check if we're updating an existing entry
            if hasattr(self, "current_service") and self.current_service:
                self.app_manager.db.update_password(
                    self.current_service, new_service, username, password, category, url, notes
                )
                self.status_bar.showMessage(f"Password for {new_service} updated successfully")
            else:
                # Add new password
                self.app_manager.db.add_password(new_service, username, password, category, url, notes)
                self.status_bar.showMessage(f"Password for {new_service} added successfully")

            # Refresh the tree
            self.load_passwords()

            # Select the updated/added item
            self.select_service_in_tree(new_service)
            
            # Clear current service reference
            self.current_service = None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save password: {str(e)}")

    def select_service_in_tree(self, service_name):
        """Select a specific service in the tree"""
        for i in range(self.password_tree.topLevelItemCount()):
            category_item = self.password_tree.topLevelItem(i)
            for j in range(category_item.childCount()):
                service_item = category_item.child(j)
                item_data = service_item.data(0, Qt.UserRole)
                if item_data and item_data == f"service:{service_name}":
                    self.password_tree.setCurrentItem(service_item)
                    return

    def delete_password(self):
        """Delete selected password"""
        current_item = self.password_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No password selected!")
            return

        item_data = current_item.data(0, Qt.UserRole)
        if not item_data or not item_data.startswith("service:"):
            QMessageBox.warning(self, "Error", "Please select a password entry!")
            return

        service = item_data.split(":", 1)[1]

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the password for {service}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from database
            if service in self.app_manager.db.data:
                del self.app_manager.db.data[service]
                self.app_manager.db._save_data()
                self.load_passwords()
                self.clear_form()
                self.status_bar.showMessage(f"Password for {service} deleted")

    def clear_form(self):
        """Clear the password details form"""
        self.service_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.url_input.clear()
        self.notes_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.strength_label.setText("Password Strength: -")
        self.strength_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                background-color: palette(window);
            }
        """)
        self.current_service = None
        self.password_tree.clearSelection()
        self.service_input.setEnabled(True)

        # Reset password visibility
        if self.show_password.isChecked():
            self.show_password.setChecked(False)

    def toggle_password_visibility(self, checked):
        """Toggle password visibility"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password.setText("👁️")

    def copy_username(self):
        """Copy username to clipboard"""
        username = self.username_input.text()
        if username:
            QApplication.clipboard().setText(username)
            self.status_bar.showMessage("Username copied to clipboard", 3000)
            
            # Visual feedback
            original_style = self.btn_copy_user.styleSheet()
            self.btn_copy_user.setStyleSheet(original_style + """
                QPushButton {
                    background-color: #4CAF50 !important;
                }
            """)
            QTimer.singleShot(1000, lambda: self.btn_copy_user.setStyleSheet(original_style))

            # Clear any existing password timer
            if self.clipboard_timer.isActive():
                self.clipboard_timer.stop()
                self.clipboard_progress.setVisible(False)

    def copy_password(self):
        """Copy password to clipboard with security measures"""
        password = self.password_input.text()
        if password:
            # Store the password we're copying
            self.copied_password = password

            # Set clipboard content
            clipboard = QApplication.clipboard()
            clipboard.setText(password)

            # Visual feedback
            original_style = self.btn_copy_pass.styleSheet()
            self.btn_copy_pass.setStyleSheet(original_style + """
                QPushButton {
                    background-color: #4CAF50 !important;
                }
            """)
            QTimer.singleShot(1000, lambda: self.btn_copy_pass.setStyleSheet(original_style))

            # Start clipboard countdown
            self.clipboard_seconds_left = getattr(self.app_manager, 'clipboard_timeout', 30)
            self.clipboard_progress.setMaximum(self.clipboard_seconds_left)
            self.clipboard_progress.setValue(self.clipboard_seconds_left)
            self.clipboard_progress.setVisible(True)
            self.clipboard_progress.setFormat(f"Clearing in {self.clipboard_seconds_left}s")
            self.status_bar.showMessage(
                f"Password copied to clipboard - will clear in {self.clipboard_seconds_left} seconds", 3000
            )

            # Start the timer
            self.clipboard_timer.start()

    def update_clipboard_progress(self):
        """Update clipboard clearing progress"""
        self.clipboard_seconds_left -= 1
        self.clipboard_progress.setValue(self.clipboard_seconds_left)
        self.clipboard_progress.setFormat(f"Clearing in {self.clipboard_seconds_left}s")
        
        if self.clipboard_seconds_left <= 0:
            self.clipboard_timer.stop()
            QApplication.clipboard().setText("")
            self.status_bar.showMessage("Clipboard cleared", 3000)
            self.clipboard_progress.setVisible(False)
            self.copied_password = ""

    def generate_password(self):
        """Generate a strong random password"""
        import secrets
        import string

        # Generate 16-character password with letters, digits, and symbols
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = "".join(secrets.choice(alphabet) for i in range(16))

        self.password_input.setText(password)
        self.update_strength_indicator(password)
        self.status_bar.showMessage("Generated strong password")

    def update_strength_indicator(self, password):
        """Update password strength indicator with modern styling"""
        if not password:
            self.strength_label.setText("Password Strength: -")
            self.strength_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: palette(window);
                }
            """)
            return

        # Calculate strength
        strength = 0
        if len(password) >= 8:
            strength += 1
        if len(password) >= 12:
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in "!@#$%^&*()" for c in password):
            strength += 1

        # Map to strength levels
        levels = ["Very Weak", "Weak", "Moderate", "Good", "Strong", "Very Strong"]
        level = levels[min(strength, len(levels) - 1)] if strength > 0 else "Very Weak"

        # Set color and emoji based on strength
        strength_config = {
            "Very Weak": {"color": "#f44336", "emoji": "🔴", "bg": "#ffebee"},
            "Weak": {"color": "#ff5722", "emoji": "🟠", "bg": "#fff3e0"},
            "Moderate": {"color": "#ff9800", "emoji": "🟡", "bg": "#fff8e1"},
            "Good": {"color": "#4caf50", "emoji": "🟢", "bg": "#e8f5e8"},
            "Strong": {"color": "#2196f3", "emoji": "🔵", "bg": "#e3f2fd"},
            "Very Strong": {"color": "#9c27b0", "emoji": "🟣", "bg": "#f3e5f5"}
        }

        config = strength_config.get(level, strength_config["Very Weak"])
        
        self.strength_label.setText(f'{config["emoji"]} {level}')
        self.strength_label.setStyleSheet(f"""
            QLabel {{
                color: {config["color"]};
                background-color: {config["bg"]};
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {config["color"]};
            }}
        """)

    def update_backup_status(self):
        """Update backup status in status bar"""
        if not hasattr(self.app_manager, "backup_manager") or not self.app_manager.backup_manager:
            self.backup_status.setText("💾 Backup: Not initialized")
            return

        if not self.app_manager.backup_manager.enabled:
            self.backup_status.setText("💾 Backup: Disabled")
            return

        if not self.app_manager.backup_manager.last_backup:
            self.backup_status.setText("💾 Backup: Never")
            return

        # Format time since last backup
        time_since = datetime.now() - self.app_manager.backup_manager.last_backup

        if time_since < timedelta(minutes=1):
            status = "Just now"
        elif time_since < timedelta(hours=1):
            mins = int(time_since.total_seconds() / 60)
            status = f"{mins} min ago"
        elif time_since < timedelta(days=1):
            hours = int(time_since.total_seconds() / 3600)
            status = f"{hours} hours ago"
        else:
            days = time_since.days
            status = f"{days} days ago"

        self.backup_status.setText(f"💾 {status}")

    def on_backup_performed(self, backup_path):
        """Handle successful backup signal"""
        self.update_backup_status()
        self.status_bar.showMessage(f"✅ Backup created: {os.path.basename(backup_path)}", 5000)

    def on_backup_failed(self, error):
        """Handle backup failure signal"""
        self.update_backup_status()
        self.status_bar.showMessage(f"❌ Backup failed: {error}", 5000)

    def update_db_info(self):
        """Update database information in status bar"""
        try:
            if not hasattr(self.app_manager.db, "db_path") or not self.app_manager.db.db_path:
                self.db_info.setText("🗄️ Database: Not loaded")
                return

            db_path = self.app_manager.db.db_path
            db_name = os.path.basename(db_path)
            folder = os.path.dirname(db_path)

            # Get password count
            count = len(self.app_manager.db.data) if hasattr(self.app_manager.db, "data") else 0

            # Truncate folder path if too long
            if len(folder) > 30:
                folder = "..." + folder[-27:]

            self.db_info.setText(f"🗄️ {db_name} | 📁 {folder} | 🔑 {count} passwords")
            self.db_info.setToolTip(f"Full Path: {db_path}")

            # Also update backup manager's knowledge of the path
            if hasattr(self.app_manager, "backup_manager"):
                if hasattr(self.app_manager, 'logger'):
                    self.app_manager.logger.debug(f"Updating backup manager with database path: {db_path}")
        except Exception as e:
            if hasattr(self.app_manager, 'logger'):
                self.app_manager.logger.error(f"Error updating db info: {str(e)}")
            self.db_info.setText("🗄️ Database info error")

    def perform_backup_now(self):
        """Perform an immediate manual backup"""
        if not hasattr(self.app_manager, "backup_manager") or not self.app_manager.backup_manager:
            QMessageBox.warning(self, "Backup Error", "Backup manager not initialized")
            return

        # Get current backup settings
        backup_settings = {
            "enabled": getattr(self.app_manager.settings, 'value', lambda x, y: y)("Backup/enabled", False),
            "frequency": getattr(self.app_manager.settings, 'value', lambda x, y: y)("Backup/frequency", "Daily"),
            "location": getattr(self.app_manager.settings, 'value', lambda x, y: y)("Backup/location", ""),
        }

        # Validate location
        if not backup_settings["location"]:
            QMessageBox.warning(
                self, "Backup Error",
                "Backup location is not set. Please configure backup settings first."
            )
            return

        # Update backup manager with current settings
        self.app_manager.backup_manager.update_settings(
            backup_settings["enabled"],
            backup_settings["frequency"],
            backup_settings["location"],
        )

        # Perform backup immediately
        try:
            backup_path = self.app_manager.backup_manager.perform_backup()
            if backup_path:
                QMessageBox.information(
                    self, "Backup Successful",
                    f"✅ Backup created successfully at:\n{backup_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Backup Failed",
                    "❌ Backup could not be created. Please check the logs."
                )
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"❌ Error during backup: {str(e)}")

    def show_import_dialog(self):
        """Show the import dialog"""
        dialog = ImportDialog(self.app_manager, self)
        dialog.exec()

    def show_export_dialog(self):
        """Show the export dialog"""
        dialog = ExportDialog(self.app_manager, self)
        dialog.exec()

    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()

    def show_help(self):
        """Show help dialog"""
        dialog = HelpDialog(self)
        dialog.exec()

    def lock_database(self):
        """Lock the database and return to login screen"""
        # Clear clipboard and any active timers
        if self.clipboard_timer.isActive():
            self.clipboard_timer.stop()

        clipboard = QApplication.clipboard()
        clipboard.clear()
        self.clipboard_progress.setVisible(False)

        # Clear our reference
        self.copied_password = ""

        # Clear sensitive data
        self.clear_form()
        self.password_tree.clear()

        # Create a new login window
        from gui.login import LoginWindow

        self.login_window = LoginWindow(self.app_manager)
        self.login_window.show()
        self.close()

    def open_settings(self):
        """Open application settings"""
        from gui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.app_manager, self)
        dialog.exec()

    def is_clipboard_clear(self):
        """Check if clipboard is empty"""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        return text == ""

    def clear_clipboard(self):
        """Manually clear clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText("")
        if self.clipboard_timer.isActive():
            self.clipboard_timer.stop()
            self.clipboard_progress.setVisible(False)
        self.copied_password = ""
        self.status_bar.showMessage("Clipboard manually cleared", 3000)