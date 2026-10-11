import os
import sys
import logging
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

# PyInstaller's windowed bootloader leaves stdout/stderr unset. pybricksdev's
# uploader uses tqdm, so provide real file streams in packaged applications.
log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SPIKE Controller"
log_dir.mkdir(parents=True, exist_ok=True)
if sys.stdout is None:
    sys.stdout = open(log_dir / "runtime.log", "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout
logging.basicConfig(filename=log_dir / "application.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SPIKE Controller")
    app.setOrganizationName("SPIKE Controller")
    window = MainWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(1500, window.close)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
