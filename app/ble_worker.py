import asyncio
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from pybricksdev.ble import find_device
from pybricksdev.connections import ConnectionState
from pybricksdev.connections.pybricks import PybricksHubBLE, StatusFlag


def program_path():
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return root / "hub" / "hub_controller.py"


class BleWorker(QThread):
    state = Signal(str)
    log = Signal(str)
    power = Signal(int, int)
    ready = Signal(bool)

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.desired = (0, 0)
        self.updated = 0
        self.halted = True
        self.quit_requested = threading.Event()
        self.program_active = threading.Event()
        self.loop = None
        self.wake = None

    def command(self, a, b):
        with self.lock:
            if not self.program_active.is_set():
                return
            if self.halted:
                if (a, b) == (0, 0):
                    self.halted = False
                else:
                    return
            self.desired = (a, b)
            self.updated = time.monotonic()

    def stop_motors(self):
        with self.lock:
            self.desired = (0, 0)
            self.halted = True
        self._wake()

    def shutdown(self):
        self.quit_requested.set()
        self.program_active.clear()
        self.stop_motors()

    def _wake(self):
        if self.loop and self.wake:
            try:
                self.loop.call_soon_threadsafe(self.wake.set)
            except RuntimeError:
                pass

    def run(self):
        # This worker has no COM/Qt dispatcher; use Bleak's MTA support.
        if sys.platform == "win32":
            from bleak.backends.winrt.util import uninitialize_sta
            uninitialize_sta()
        try:
            asyncio.run(self._main())
        except Exception as exc:
            self.log.emit(f"Bluetooth worker: {type(exc).__name__}: {exc}")
        finally:
            self.ready.emit(False)
            self.power.emit(0, 0)
            self.state.emit("Disconnected")

    async def _interruptible(self, awaitable, timeout):
        task = asyncio.create_task(awaitable)
        deadline = time.monotonic() + timeout
        try:
            while not task.done():
                if self.quit_requested.is_set():
                    raise asyncio.CancelledError()
                if time.monotonic() >= deadline:
                    raise TimeoutError("Bluetooth operation timed out")
                await asyncio.wait({task}, timeout=0.05)
            return await task
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    async def _main(self):
        self.loop = asyncio.get_running_loop()
        self.wake = asyncio.Event()
        attempt = 0
        while not self.quit_requested.is_set():
            hub = None
            self.program_active.clear()
            self.ready.emit(False)
            self.stop_motors()
            try:
                self.state.emit("Reconnecting" if attempt else "Searching")
                self.log.emit("Searching for Pybricks Hub…")
                device = await self._interruptible(find_device(name="Pybricks Hub", timeout=15), 18)
                hub = PybricksHubBLE(device)
                self.state.emit("Connecting")
                await self._interruptible(hub.connect(), 20)
                self.log.emit("Bluetooth connected. Uploading Hub control program…")
                await self._interruptible(hub.run(str(program_path()), wait=False,
                                                print_output=False, line_handler=True), 30)
                async def wait_ready():
                    while True:
                        line = await hub.read_line()
                        if isinstance(line, bytes):
                            line = line.decode("utf-8", "replace")
                        self.log.emit(f"Hub: {line}")
                        if line.strip() == "READY":
                            return
                await self._interruptible(wait_ready(), 10)
                async def wait_running():
                    while not hub.status_observable.value & StatusFlag.USER_PROGRAM_RUNNING:
                        await asyncio.sleep(0.025)
                await self._interruptible(wait_running(), 3)
                if hub.connection_state_observable.value != ConnectionState.CONNECTED:
                    raise RuntimeError("Hub disconnected during startup")
                # READY is emitted after motor initialization and watchdog setup.
                self.stop_motors()
                self.program_active.set()
                self.state.emit("Connected")
                self.ready.emit(True)
                self.log.emit("Hub program ready. Return controls to neutral to enable movement.")
                attempt = 0
                while not self.quit_requested.is_set():
                    if hub.connection_state_observable.value != ConnectionState.CONNECTED:
                        raise ConnectionError("Bluetooth link lost")
                    if not hub.status_observable.value & StatusFlag.USER_PROGRAM_RUNNING:
                        raise RuntimeError("Hub control program stopped")
                    self.wake.clear()
                    with self.lock:
                        output = self.desired if not self.halted and time.monotonic() - self.updated < 0.25 else (0, 0)
                    await asyncio.wait_for(hub.write_line(f"{output[0]},{output[1]}"), 1)
                    self.power.emit(*output)
                    try:
                        await asyncio.wait_for(self.wake.wait(), 0.05)
                    except TimeoutError:
                        pass
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.log.emit(f"{type(exc).__name__}: {exc}")
            finally:
                self.program_active.clear()
                self.ready.emit(False)
                self.power.emit(0, 0)
                if hub:
                    if hub.connection_state_observable.value == ConnectionState.CONNECTED:
                        try:
                            await asyncio.wait_for(hub.write_line("0,0"), 1)
                            await asyncio.wait_for(hub.stop_user_program(), 2)
                        except Exception as exc:
                            self.log.emit(f"Stop could not be confirmed: {exc}")
                    try:
                        await asyncio.wait_for(hub.disconnect(), 3)
                    except Exception as exc:
                        self.log.emit(f"Disconnect: {exc}")
            if not self.quit_requested.is_set():
                attempt += 1
                self.state.emit("Reconnecting")
                self.log.emit("Retrying in 3 seconds…")
                for _ in range(60):
                    if self.quit_requested.is_set():
                        break
                    await asyncio.sleep(0.05)
