# tests/conftest.py
import sys

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Session-wide QApplication fixture"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    # Clean up after all tests complete
    app.quit()
