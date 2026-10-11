import asyncio
import unittest
from unittest.mock import patch
from PySide6.QtTest import QTest
from app.main import QApplication, MainWindow


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_close_cancels_scan_without_duplicate_worker(self):
        async def find(**kwargs):
            await asyncio.sleep(30)
        with patch("app.ble_worker.find_device", find):
            window = MainWindow()
            window.show()
            window.connect_hub()
            first = window.worker
            window.connect_hub()
            self.assertIs(window.worker, first)
            QTest.qWait(100)
            self.assertTrue(first.isRunning())
            window.close()
            for _ in range(100):
                QTest.qWait(20)
                if not first.isRunning() and not window.isVisible():
                    break
            self.assertFalse(first.isRunning())
            self.assertFalse(window.isVisible())

    def test_resizing_keeps_footer_and_controls_accessible(self):
        from PySide6.QtWidgets import QBoxLayout
        window = MainWindow()
        window.show()
        try:
            for width, height in ((900, 800), (640, 480), (360, 320), (1200, 900)):
                window.resize(width, height)
                QTest.qWait(100)
                self.assertEqual(window.footer.text(), "Developed by Ahmed Shaaban")
                self.assertTrue(window.footer.isVisible())
                self.assertTrue(window.centralWidget().rect().contains(window.footer.geometry()))
                self.assertLess(window.scroll.geometry().bottom(), window.footer.geometry().top())
                self.assertEqual(window.scroll.horizontalScrollBar().maximum(), 0)
                for button in (window.connect_button, window.disconnect_button, window.stop_button):
                    self.assertGreaterEqual(button.width(), button.minimumSizeHint().width())
                for text in (window.hub_status, window.pad_status, window.speed_text):
                    self.assertGreaterEqual(text.width(), text.fontMetrics().horizontalAdvance(text.text()))
                a = window.connect_button.geometry()
                b = window.disconnect_button.geometry()
                self.assertFalse(a.intersects(b))
                expected = QBoxLayout.TopToBottom if width < 620 else QBoxLayout.LeftToRight
                self.assertTrue(all(row.direction() == expected for row in window.responsive_rows))
                window.scroll.ensureWidgetVisible(window.stop_button)
                QTest.qWait(30)
                center = window.stop_button.mapTo(window.scroll.viewport(), window.stop_button.rect().center())
                self.assertTrue(window.scroll.viewport().rect().contains(center))
                window.grab().save(f"verification/responsive-{width}x{height}.png")
        finally:
            window.close()
