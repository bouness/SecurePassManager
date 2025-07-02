from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QSpacerItem, QTextEdit,
                               QVBoxLayout)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SecurePass Manager")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        title_label = QLabel(
            "<h2>🔐 SecurePass Manager - Your Ultimate Digital Vault</h2>"
        )
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml(
            """
        <p><b>Why Choose SecurePass Manager?</b></p>
        <p>In today's digital world, we juggle countless online accounts—email, banking, social media, work apps. 
        Reusing passwords or choosing weak ones leads to real risks. <b>SecurePass Manager</b> solves this problem 
        with <b>military-grade encryption</b> and complete <b>local data storage</b>. Nothing leaves your device.</p>

        <p><b>Comprehensive Security Features:</b></p>
        <ul>
            <li><b>🔒 Military-Grade Encryption:</b> AES-256, zero-knowledge, client-side encryption</li>
            <li><b>🛡️ Advanced Security:</b> Firewall protection, proxy support, clipboard clearing</li>
            <li><b>🛠️ Password Tools:</b> Generator, strength meter, tagging, search, history</li>
            <li><b>🔄 Cross-Platform:</b> Native on Windows, macOS, Linux</li>
            <li><b>🧠 Smart Automation:</b> Auto-lock, backups, expiration alerts</li>
        </ul>

        <p><b>Security First. Privacy Always.</b></p>
        <ul>
            <li>No telemetry</li>
            <li>No internet required</li>
            <li>Fully offline and open source</li>
            <li>Emergency wipe (self-destruct) support</li>
        </ul>
        """
        )

        layout.addWidget(info_text)

        donate_layout = QHBoxLayout()
        donate_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        donate_btn = QPushButton("💖 Donate via Venmo")
        donate_btn.clicked.connect(self.open_venmo)
        donate_layout.addWidget(donate_btn)

        donate_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        layout.addLayout(donate_layout)

    def open_venmo(self):
        QDesktopServices.openUrl(QUrl("https://venmo.com/youness-bougteb"))
