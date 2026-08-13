from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ui.widgets.numeric_keypad import NumericKeypad


class EmployeeLogin(QWidget):
    submitted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.prompt = QLabel("Employee PIN")
        self.prompt.setObjectName("fieldLabel")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly)
        self.pin_input.setMaxLength(12)
        self.pin_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_input.setPlaceholderText("Enter PIN")
        self.pin_input.returnPressed.connect(self._submit)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(24)
        keypad = NumericKeypad()
        keypad.digit_pressed.connect(self._append_digit)
        keypad.backspace_pressed.connect(self.pin_input.backspace)
        keypad.clear_pressed.connect(self.pin_input.clear)
        self.continue_button = QPushButton("Continue")
        self.continue_button.setObjectName("primaryButton")
        self.continue_button.setMinimumHeight(48)
        self.continue_button.clicked.connect(self._submit)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.prompt)
        layout.addWidget(self.pin_input)
        layout.addWidget(self.error_label)
        layout.addWidget(keypad)
        layout.addSpacing(4)
        layout.addWidget(self.continue_button)

    def reset(self) -> None:
        self.pin_input.clear()
        self.error_label.clear()
        self.continue_button.setEnabled(True)
        self.pin_input.setFocus()

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.pin_input.selectAll()
        self.pin_input.setFocus()
        self.continue_button.setEnabled(True)

    def _append_digit(self, digit: str) -> None:
        if len(self.pin_input.text()) < self.pin_input.maxLength():
            self.pin_input.insert(digit)

    def _submit(self) -> None:
        if not self.continue_button.isEnabled():
            return
        self.continue_button.setEnabled(False)
        self.submitted.emit(self.pin_input.text())
