"""Local visual verification, no Bluetooth connection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import QApplication, MainWindow
from PySide6.QtCore import QTimer

app = QApplication([])
window = MainWindow()
window.show()
def capture():
    Path("verification").mkdir(exist_ok=True)
    window.grab().save("verification/gui.png")
    window.close()
QTimer.singleShot(500, capture)
app.exec()
