import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from database.connection import Database
from database.schema import initialize_database
from services.admin_service import AdminService
from services.employee_service import EmployeeService
from services.punch_service import PunchService
from ui.main_window import MainWindow
from ui.styles import APPLICATION_STYLE


BASE_DIR = Path(__file__).resolve().parent


def configure_logging() -> None:
    log_directory = BASE_DIR / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_directory / "application.log", maxBytes=1_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def main() -> int:
    configure_logging()
    application = QApplication(sys.argv)
    application.setApplicationName("Employee Punch Clock")
    application.setStyle("Fusion")
    application.setStyleSheet(APPLICATION_STYLE)
    try:
        database = Database(BASE_DIR / "data" / "business.db")
        initialize_database(database)
        window = MainWindow(EmployeeService(database), PunchService(database), AdminService(database))
    except Exception:
        logging.getLogger(__name__).exception("Application startup failed")
        QMessageBox.critical(None, "Startup Error", "The punch clock could not start. Check the application log for details.")
        return 1
    window.showFullScreen()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
