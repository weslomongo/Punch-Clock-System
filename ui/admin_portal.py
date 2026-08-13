from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class AdminPortal(QWidget):
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.welcome = QLabel()
        self.welcome.setObjectName("employeeName")
        self.welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message = QLabel("Administrative tools will be added in a later phase.")
        message.setObjectName("statusLabel")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning = QLabel("The default password must be replaced before production use.")
        warning.setObjectName("errorLabel")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning.setWordWrap(True)
        logout = QPushButton("Sign Out")
        logout.setObjectName("primaryButton")
        logout.setMinimumHeight(50)
        logout.clicked.connect(self.logout_requested.emit)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.addStretch()
        layout.addWidget(self.welcome)
        layout.addWidget(message)
        layout.addWidget(warning)
        layout.addSpacing(12)
        layout.addWidget(logout)
        layout.addStretch()

    def set_username(self, username: str) -> None:
        self.welcome.setText(f"Administrator: {username}")
