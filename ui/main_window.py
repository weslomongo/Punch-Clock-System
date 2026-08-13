import logging
from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from models.employee import Employee
from models.punch import PunchType
from services.admin_service import AdminAuthenticationError, AdminService
from services.employee_service import AuthenticationError, EmployeeService
from services.punch_service import PunchError, PunchService
from ui.admin_login import AdminLogin
from ui.admin_portal import AdminPortal
from ui.employee_login import EmployeeLogin
from ui.punch_clock import PunchClockPanel
from utils.time import format_time


LOGGER = logging.getLogger(__name__)
SESSION_TIMEOUT_MS = 60_000
CONFIRMATION_MS = 2_500
ADMIN_SESSION_TIMEOUT_MS = 300_000


class MainWindow(QMainWindow):
    def __init__(
        self, employee_service: EmployeeService, punch_service: PunchService,
        admin_service: AdminService,
    ) -> None:
        super().__init__()
        self.employee_service = employee_service
        self.punch_service = punch_service
        self.admin_service = admin_service
        self.current_employee: Employee | None = None
        self.setWindowTitle("Employee Punch Clock")
        self.setMinimumSize(540, 700)
        self._build_ui()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._session_timer = QTimer(self)
        self._session_timer.setSingleShot(True)
        self._session_timer.timeout.connect(self.reset_session)
        self._confirmation_timer = QTimer(self)
        self._confirmation_timer.setSingleShot(True)
        self._confirmation_timer.timeout.connect(self.reset_session)
        self._update_clock()
        QTimer.singleShot(0, self.login.reset)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("windowRoot")
        page_layout = QHBoxLayout(root)
        page_layout.setContentsMargins(36, 28, 36, 32)
        content = QWidget()
        content.setObjectName("contentColumn")
        content.setMaximumWidth(620)
        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 18, 28, 24)
        outer.setSpacing(0)
        page_layout.addStretch(1)
        page_layout.addWidget(content, 2)
        page_layout.addStretch(1)
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label = QLabel()
        self.date_label.setObjectName("dateLabel")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        outer.addWidget(self.time_label)
        outer.addWidget(self.date_label)
        outer.addSpacing(26)
        outer.addWidget(separator)
        outer.addSpacing(24)
        self.stack = QStackedWidget()
        self.login = EmployeeLogin()
        self.login.submitted.connect(self.identify_employee)
        self.punch_panel = PunchClockPanel()
        self.punch_panel.punch_requested.connect(self.record_punch)
        self.punch_panel.cancelled.connect(self.reset_session)
        self.admin_login = AdminLogin()
        self.admin_login.submitted.connect(self.authenticate_admin)
        self.admin_login.cancelled.connect(self.reset_session)
        self.admin_portal = AdminPortal()
        self.admin_portal.logout_requested.connect(self.reset_session)
        self.confirmation = self._confirmation_widget()
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.punch_panel)
        self.stack.addWidget(self.confirmation)
        self.stack.addWidget(self.admin_login)
        self.stack.addWidget(self.admin_portal)
        outer.addWidget(self.stack, 1)
        self.setCentralWidget(root)

    def _confirmation_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirmation_title = QLabel()
        self.confirmation_title.setObjectName("confirmationTitle")
        self.confirmation_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirmation_time = QLabel()
        self.confirmation_time.setObjectName("confirmationTime")
        self.confirmation_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.confirmation_title)
        layout.addWidget(self.confirmation_time)
        return widget

    def _update_clock(self) -> None:
        now = datetime.now().astimezone()
        self.time_label.setText(now.strftime("%-I:%M:%S %p"))
        self.date_label.setText(now.strftime("%A, %B %-d"))
        if self.current_employee is not None and self.stack.currentWidget() is self.punch_panel:
            self._refresh_hours()

    def identify_employee(self, pin: str) -> None:
        if pin == "8888":
            self.login.reset()
            self.admin_login.reset()
            self.stack.setCurrentWidget(self.admin_login)
            self._session_timer.start(SESSION_TIMEOUT_MS)
            return
        try:
            employee = self.employee_service.authenticate(pin)
            state = self.punch_service.get_state(employee.id)
            worked = self.punch_service.hours_worked_today(employee.id)
        except AuthenticationError as error:
            self.login.show_error(str(error))
            return
        except PunchError as error:
            self.login.show_error(str(error))
            return
        except Exception:
            LOGGER.exception("Unexpected error while identifying employee")
            self.login.show_error("Unable to identify employee. Please try again.")
            return
        self.current_employee = employee
        self.punch_panel.set_employee(employee, state)
        self.punch_panel.set_hours_worked(int(worked.total_seconds()))
        self.stack.setCurrentWidget(self.punch_panel)
        self._session_timer.start(SESSION_TIMEOUT_MS)

    def authenticate_admin(self, username: str, password: str) -> None:
        try:
            authenticated_username = self.admin_service.authenticate(username, password)
        except AdminAuthenticationError as error:
            self.admin_login.show_error(str(error))
            self._session_timer.start(SESSION_TIMEOUT_MS)
            return
        except Exception:
            LOGGER.exception("Unexpected error during administrator authentication")
            self.admin_login.show_error("Unable to sign in. Please try again.")
            self._session_timer.start(SESSION_TIMEOUT_MS)
            return
        self.admin_portal.set_username(authenticated_username)
        self.stack.setCurrentWidget(self.admin_portal)
        self._session_timer.start(ADMIN_SESSION_TIMEOUT_MS)

    def _refresh_hours(self) -> None:
        if self.current_employee is None:
            return
        try:
            worked = self.punch_service.hours_worked_today(self.current_employee.id)
        except PunchError:
            return
        except Exception:
            LOGGER.exception("Unexpected error while refreshing hours worked")
            return
        self.punch_panel.set_hours_worked(int(worked.total_seconds()))

    def record_punch(self, event_type: PunchType) -> None:
        if self.current_employee is None:
            self.reset_session()
            return
        try:
            if event_type is PunchType.CLOCK_IN:
                punch = self.punch_service.clock_in(self.current_employee.id)
                title = "Clocked in"
            else:
                punch = self.punch_service.clock_out(self.current_employee.id)
                title = "Clocked out"
        except PunchError as error:
            self.punch_panel.show_error(str(error))
            self._session_timer.start(SESSION_TIMEOUT_MS)
            return
        except Exception:
            LOGGER.exception("Unexpected error while recording punch")
            self.punch_panel.show_error("Unable to record punch. Please try again.")
            self._session_timer.start(SESSION_TIMEOUT_MS)
            return
        self._session_timer.stop()
        self.confirmation_title.setText(title)
        self.confirmation_time.setText(format_time(punch.occurred_at))
        self.stack.setCurrentWidget(self.confirmation)
        self._confirmation_timer.start(CONFIRMATION_MS)

    def reset_session(self) -> None:
        self._session_timer.stop()
        self._confirmation_timer.stop()
        self.current_employee = None
        self.admin_login.reset()
        self.login.reset()
        self.stack.setCurrentWidget(self.login)
