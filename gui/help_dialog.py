from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
)
from PySide6.QtCore import Qt


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help - SecurePass Manager")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        title_label = QLabel("<h2>🧠 SecurePass Manager - Help Guide</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>🔑 Getting Started</h3>
        <ul>
            <li>Click <b>"Add New"</b> to create a new password entry.</li>
            <li>Fill in service name, username, password, URL, and notes.</li>
            <li>Click <b>"Save Changes"</b> to securely store the password.</li>
        </ul>

        <h3>🔍 Searching & Organizing</h3>
        <ul>
            <li>Use the search bar to quickly find services.</li>
            <li>Organize by tags and categories (Social, Work, Finance, etc.).</li>
        </ul>

        <h3>🔒 Clipboard Security</h3>
        <ul>
            <li>Click <b>"Copy Password"</b> or <b>"Copy Username"</b> to use credentials.</li>
            <li>Clipboard automatically clears after 30 seconds (configurable).</li>
            <li>Manual clear option also available in the toolbar.</li>
        </ul>

        <h3>🛠️ Tools & Features</h3>
        <ul>
            <li>Use <b>"Generate Password"</b> to create secure passwords.</li>
            <li>Check strength in real-time with the visual indicator.</li>
            <li>Supports multiple encryption algorithms (AES, ChaCha20).</li>
        </ul>

        <h3>🧰 Database & Security</h3>
        <ul>
            <li>All data is stored <b>locally</b> with <b>AES-256 encryption</b>.</li>
            <li>No internet access required. Works fully offline.</li>
            <li>Auto-lock after inactivity. Enable backups in settings.</li>
        </ul>

        <h3>🆘 Need More Help?</h3>
        <ul>
            <li>Report bugs or suggest features on the <b>GitHub Issues</b> page.</li>
            <li>For urgent security concerns, contact the maintainer directly.</li>
        </ul>
        """)
        layout.addWidget(help_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
