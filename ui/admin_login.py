from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class AdminLogin(QWidget):
    submitted = Signal(str, str)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        title = QLabel("Administrator Sign In")
        title.setObjectName("employeeName")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setMaxLength(64)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMaxLength(128)
        self.password.returnPressed.connect(self._submit)
        self.error = QLabel()
        self.error.setObjectName("errorLabel")
        self.error.setWordWrap(True)
        self.submit_button = QPushButton("Sign In")
        self.submit_button.setObjectName("primaryButton")
        self.submit_button.setMinimumHeight(50)
        self.submit_button.clicked.connect(self._submit)
        cancel = QPushButton("Back to punch clock")
        cancel.setObjectName("linkButton")
        cancel.clicked.connect(self.cancelled.emit)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(12)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.error)
        layout.addWidget(self.submit_button)
        layout.addWidget(cancel)
        layout.addStretch()

    def reset(self) -> None:
        self.username.clear()
        self.password.clear()
        self.error.clear()
        self.submit_button.setEnabled(True)
        self.username.setFocus()

    def show_error(self, message: str) -> None:
        self.error.setText(message)
        self.password.clear()
        self.submit_button.setEnabled(True)
        self.password.setFocus()

    def _submit(self) -> None:
        if self.submit_button.isEnabled():
            self.submit_button.setEnabled(False)
            self.submitted.emit(self.username.text(), self.password.text())
