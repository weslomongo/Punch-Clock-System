from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from models.employee import Employee
from models.punch import PunchType
from services.punch_service import PunchState
from utils.time import format_time


class PunchClockPanel(QWidget):
    punch_requested = Signal(object)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.employee_name = QLabel()
        self.employee_name.setObjectName("employeeName")
        self.employee_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status = QLabel()
        self.status.setObjectName("statusLabel")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hours = QLabel()
        self.hours.setObjectName("hoursLabel")
        self.hours.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_button = QPushButton()
        self.action_button.setObjectName("primaryButton")
        self.action_button.setMinimumHeight(58)
        self.action_button.clicked.connect(self._request_punch)
        cancel_button = QPushButton("Back to PIN entry")
        cancel_button.setObjectName("linkButton")
        cancel_button.clicked.connect(self.cancelled.emit)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 26, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self.employee_name)
        layout.addWidget(self.status)
        layout.addWidget(self.hours)
        layout.addSpacing(12)
        layout.addWidget(self.action_button)
        layout.addWidget(cancel_button)
        self._event_type = PunchType.CLOCK_IN

    def set_employee(self, employee: Employee, state: PunchState) -> None:
        self.employee_name.setText(employee.first_name)
        if state.clocked_in:
            assert state.latest_punch is not None
            self.status.setText(f"Clocked In Since {format_time(state.latest_punch.occurred_at)}")
            self.action_button.setText("Clock Out")
            self._event_type = PunchType.CLOCK_OUT
        else:
            self.status.setText("Currently Clocked Out")
            self.action_button.setText("Clock In")
            self._event_type = PunchType.CLOCK_IN
        self.action_button.setEnabled(True)

    def set_hours_worked(self, duration_seconds: int) -> None:
        hours, remainder = divmod(max(0, duration_seconds), 3600)
        minutes = remainder // 60
        self.hours.setText(f"Worked Today: {hours:d} hr {minutes:02d} min")

    def show_error(self, message: str) -> None:
        self.status.setText(message)
        self.action_button.setEnabled(True)

    def _request_punch(self) -> None:
        if self.action_button.isEnabled():
            self.action_button.setEnabled(False)
            self.punch_requested.emit(self._event_type)
