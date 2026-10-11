"""Explicit offline package check, including the frozen compiler subprocess."""
import asyncio
import json
import sys
from pathlib import Path


def verify():
    destination = Path(sys.argv[sys.argv.index("--verify-bundle") + 1])
    result = {}
    try:
        from PySide6.QtTest import QTest
        from app.main import QApplication, MainWindow
        from app.ble_worker import program_path
        from pybricksdev.compile import compile_multi_file
        import pygame
        from bleak.backends.winrt.client import BleakClientWinRT
        app = QApplication([])
        window = MainWindow()
        window.show()
        app.processEvents()
        window.grab().save(str(destination.with_suffix(".png")))
        assert window.footer.text() == "Developed by Ahmed Shaaban"
        for width, height in ((640, 480), (360, 320)):
            window.resize(width, height)
            QTest.qWait(150)
            assert window.footer.isVisible()
            assert window.scroll.geometry().bottom() < window.footer.geometry().top()
            assert window.scroll.horizontalScrollBar().maximum() == 0
            window.grab().save(str(destination.with_name(f"{destination.stem}-{width}x{height}.png")))
        result["responsive_footer"] = "passed at default, 640x480 and 360x320"
        window.close()
        result["gui"] = "opened, rendered, closed"
        result["hub_source"] = str(program_path())
        async def compile_all():
            for abi in (5, 6):
                data = await compile_multi_file(str(program_path()), abi)
                result[f"mpy_abi_{abi}"] = len(data)
        asyncio.run(compile_all())
        result["winrt_backend"] = BleakClientWinRT.__name__
        result["status"] = "passed"
    except Exception:
        import traceback
        result["status"] = "failed"
        result["error"] = traceback.format_exc()
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["status"] == "passed" else 1
