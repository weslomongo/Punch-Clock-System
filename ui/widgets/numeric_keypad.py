from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget


class NumericKeypad(QWidget):
    digit_pressed = Signal(str)
    backspace_pressed = Signal()
    clear_pressed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(8)
        for index, digit in enumerate("123456789"):
            button = self._button(digit, lambda checked=False, value=digit: self.digit_pressed.emit(value))
            layout.addWidget(button, index // 3, index % 3)
        layout.addWidget(self._button("Clear", lambda: self.clear_pressed.emit(), secondary=True), 3, 0)
        layout.addWidget(self._button("0", lambda: self.digit_pressed.emit("0")), 3, 1)
        layout.addWidget(self._button("Back", lambda: self.backspace_pressed.emit(), secondary=True), 3, 2)

    @staticmethod
    def _button(label: str, callback: Callable[..., None], secondary: bool = False) -> QPushButton:
        button = QPushButton(label)
        button.setProperty("keypad", True)
        button.setProperty("secondary", secondary)
        button.setMinimumSize(92, 56)
        button.clicked.connect(callback)
        return button
