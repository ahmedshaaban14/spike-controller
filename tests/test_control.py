import asyncio
import sys
import types
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch
from app.drive import motor_power
from app.ble_worker import BleWorker, ConnectionState, StatusFlag


class DriveTests(unittest.TestCase):
    def test_original_mapping_and_speed(self):
        self.assertEqual(motor_power(0, 1), (80, 80))
        self.assertEqual(motor_power(1, 0), (80, -80))
        self.assertEqual(motor_power(0, -1), (-80, -80))
        self.assertEqual(motor_power(.1, .1), (0, 0))
        self.assertEqual(motor_power(0, 1, speed=50), (40, 40))
        self.assertEqual(motor_power(1, 1), (80, 0))

    def test_dpad_overrides_only_corresponding_axis(self):
        self.assertEqual(motor_power(-1, 0, (1, 0)), (80, -80))
        self.assertEqual(motor_power(0, -1, (0, 1)), (80, 80))
        self.assertEqual(motor_power(1, -1, (0, 1)), (80, 0))
        for x in (-10, -1, 0, 1, 10):
            for y in (-10, -1, 0, 1, 10):
                self.assertTrue(all(-100 <= p <= 100 for p in motor_power(x, y)))


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_ready_gate_stop_latch_and_disconnect(self):
        worker = BleWorker()
        writes = []
        ready = []
        class FakeHub:
            def __init__(self, device): pass
            connection_state_observable = types.SimpleNamespace(value=ConnectionState.CONNECTED)
            status_observable = types.SimpleNamespace(value=StatusFlag.USER_PROGRAM_RUNNING)
            async def connect(self): pass
            async def run(self, *args, **kwargs):
                self.assert_no_writes()
            def assert_no_writes(self):
                assert writes == []
            async def read_line(self): return "READY"
            async def write_line(self, line): writes.append(line)
            async def stop_user_program(self): pass
            async def disconnect(self): self.connection_state_observable.value = ConnectionState.DISCONNECTED
        async def find(**kwargs): return object()
        worker.ready.connect(ready.append)
        messages = []
        worker.log.connect(messages.append)
        with patch("app.ble_worker.find_device", find), patch("app.ble_worker.PybricksHubBLE", FakeHub):
            task = asyncio.create_task(worker._main())
            for _ in range(100):
                if True in ready: break
                await asyncio.sleep(.01)
            self.assertIn(True, ready, messages)
            worker.command(80, 80)
            await asyncio.sleep(.07)
            self.assertNotIn("80,80", writes)
            worker.command(0, 0)
            worker.command(80, 80)
            await asyncio.sleep(.07)
            self.assertIn("80,80", writes)
            await asyncio.sleep(.3)
            self.assertEqual(writes[-1], "0,0")
            worker.stop_motors()
            await asyncio.sleep(.02)
            self.assertEqual(writes[-1], "0,0")
            worker.command(80, 80)
            await asyncio.sleep(.07)
            self.assertEqual(writes[-1], "0,0")
            worker.shutdown()
            await asyncio.wait_for(task, 2)
            self.assertEqual(writes[-1], "0,0")

    async def test_scan_cancellation(self):
        worker = BleWorker()
        async def find(**kwargs): await asyncio.sleep(30)
        with patch("app.ble_worker.find_device", find):
            task = asyncio.create_task(worker._main())
            await asyncio.sleep(.05)
            worker.shutdown()
            await asyncio.wait_for(task, .5)

    async def test_failed_startup_never_enables_motion(self):
        worker = BleWorker()
        ready = []
        writes = []
        worker.ready.connect(ready.append)
        class FakeHub:
            def __init__(self, device):
                self.connection_state_observable = types.SimpleNamespace(value=ConnectionState.CONNECTED)
            async def connect(self): pass
            async def run(self, *args, **kwargs): raise RuntimeError("unsupported Hub API")
            async def write_line(self, line): writes.append(line)
            async def stop_user_program(self): pass
            async def disconnect(self):
                self.connection_state_observable.value = ConnectionState.DISCONNECTED
        async def find(**kwargs): return object()
        with patch("app.ble_worker.find_device", find), patch("app.ble_worker.PybricksHubBLE", FakeHub):
            task = asyncio.create_task(worker._main())
            worker.command(80, 80)
            await asyncio.sleep(.1)
            worker.shutdown()
            await asyncio.wait_for(task, 1)
        self.assertNotIn(True, ready)
        self.assertTrue(all(line == "0,0" for line in writes))


class WatchdogTests(unittest.TestCase):
    def test_partial_line_does_not_block_watchdog(self):
        clock = [0]
        powers = []
        chars = list("80,80\n")
        class Motor:
            def __init__(self, port, positive_direction):
                self.port = port
                self.direction = positive_direction
            def dc(self, power): powers.append((clock[0], self.port, power))
        class Watch:
            def __init__(self): self.start = clock[0]
            def reset(self): self.start = clock[0]
            def time(self): return clock[0] - self.start
        class Poll:
            def register(self, *args): pass
            def poll(self, timeout): return bool(chars)
        class EndTest(Exception): pass
        def wait(ms):
            clock[0] += ms
            if clock[0] == 100: chars.extend("20,")
            if clock[0] > 600: raise EndTest()
        modules = {
            "pybricks": types.ModuleType("pybricks"),
            "pybricks.hubs": types.SimpleNamespace(EssentialHub=lambda: None),
            "pybricks.pupdevices": types.SimpleNamespace(Motor=Motor),
            "pybricks.parameters": types.SimpleNamespace(Port=types.SimpleNamespace(A="A", B="B"), Direction=types.SimpleNamespace(CLOCKWISE=1, COUNTERCLOCKWISE=-1)),
            "pybricks.tools": types.SimpleNamespace(wait=wait, StopWatch=Watch),
            "uselect": types.SimpleNamespace(poll=Poll, POLLIN=1),
        }
        stdin = types.SimpleNamespace(read=lambda n: chars.pop(0))
        with patch.dict(sys.modules, modules), patch.object(sys, "stdin", stdin):
            with self.assertRaises(EndTest):
                runpy.run_path(str(Path(__file__).resolve().parents[1] / "hub/hub_controller.py"))
        self.assertIn((0, "A", 80), powers)
        self.assertIn((500, "A", 0), powers)
        self.assertIn((500, "B", 0), powers)


if __name__ == "__main__":
    unittest.main()
