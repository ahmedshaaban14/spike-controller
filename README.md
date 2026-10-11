# SPIKE Controller

A Windows desktop controller for the LEGO SPIKE Essential Small Hub running
Pybricks. Motors use ports A and B. No firmware flashing is performed.

## Development

Use Windows x64 and Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -m app.main
```

On this workstation Python is `C:\Python311\python.exe`; the `py` launcher is
not installed. Close the original command-line controller before connecting.

## Pairing and driving

1. Enable Bluetooth in Windows Settings and make sure the Bluetooth adapter's
   driver is installed. Allow Bluetooth/device access if Windows or your
   organization's policy prompts. Administrator rights are not normally needed.
2. Pair the PS4 controller in Windows Bluetooth settings: hold SHARE + PS until
   its light flashes, then add the Wireless Controller. USB also works. Close
   software that hides/remaps the controller if it prevents pygame detection.
3. Turn on the Pybricks Hub and leave it advertising. The application scans for
   `Pybricks Hub`; close Pybricks Code and other apps connected to it first.
4. Choose **Connect to Hub**. The app uploads `hub/hub_controller.py` as a user
   program, then waits for both `READY` and program-running status. This does not
   install or update firmware. The activity log shows startup errors.
5. Return the stick and D-pad to neutral. Left stick drives; D-pad overrides
   only its corresponding axis. The speed slider scales the original 80-power
   ceiling: 100% is 80, 50% is 40. The deadzone remains 0.12.
6. **STOP MOTORS** or Space requests `0,0`, and movement remains latched off
   until controls return to neutral. Disconnect and window close also attempt
   `0,0`, stop the Hub program, and release BLE before closing.

The supplied original `ps4_spike.py` did **not** contain an X-axis inversion or
D-pad mapping. This application preserves its actual `x = axis(0)`,
`y = -axis(1)`, `left = y+x`, `right = y-x` behavior and adds D-pad overrides.
Motor A remains CLOCKWISE; B remains COUNTERCLOCKWISE. Confirm steering with
the wheels raised before normal use, especially if a different controller
driver presents different axis indices.

Only controllers named PS4, DualShock, or Wireless Controller are selected.
pygame's hat 0 provides the D-pad, as is usual for this Windows controller
configuration; drivers exposing D-pad buttons instead require a hardware
mapping check. Movement indicators show the last successfully transmitted
command, not measured motor feedback.

## Connection and safety behavior

All BLE work runs on a dedicated Qt worker thread with its own asyncio loop.
Only one worker can connect at a time. Failed connections retry after three
seconds until Disconnect is chosen. Scanning and startup can be cancelled.
The GUI stays responsive during connection and shutdown.

Controller removal requests a stop. Input older than 250 ms is replaced by
zero. On link loss or program exit, readiness is cleared and motion is blocked
through reconnection until startup completes and the controls are neutral.
Commands refresh every 50 ms, including neutral commands.

The Hub watchdog zeros both motors after 500 ms without a valid command.
It reads available characters instead of blocking on an incomplete line and
uses a bounded buffer. Its StopWatch, poll and stdin APIs are documented in
[Pybricks timing tools](https://docs.pybricks.com/en/v3.3.0/tools/),
[uselect](https://docs.pybricks.com/en/v4.0.0/micropython/uselect.html), and
[PC communication](https://pybricks.com/projects/tutorials/wireless/hub-to-device/pc-communication/).
The installed Hub firmware version cannot be determined without a physical
connection. API compatibility and the actual stop interval must therefore be
verified on that Hub. An unsupported API prevents READY and blocks desktop
movement. If BLE is unavailable, delivery of a desktop stop cannot be confirmed.

## Build and distribute

Double-click `build_windows.bat`, or run it from a terminal. It verifies Python
3.11, installs pinned dependencies and PyInstaller, and builds an x64 folder
distribution at:

```text
dist/SPIKE Controller/SPIKE Controller.exe
```

Copy the **entire SPIKE Controller folder**, including `_internal`, to the
recipient Windows PC. Launch the EXE by double-clicking; no Python installation
or terminal is required. The Hub source and MicroPython compilers are bundled.
Bluetooth hardware, drivers, controller pairing, and existing Pybricks firmware
are still required. This unsigned application may trigger Windows reputation
checks; distribute through a trusted channel. Do not copy just the EXE.

Activity and runtime logs are saved under `%LOCALAPPDATA%\SPIKE Controller`.
The build does not connect to hardware automatically. The smoke-test option
`--smoke-test` opens the interface and closes it after 1.5 seconds without
scanning for the Hub.

Local build and packaged GUI/compiler checks passed on this workstation.
No controller or advertising Hub was found during the hardware probe; actual
robot behavior and installation on another Windows PC remain untested.

## Source layout and verification

- `app/`: Qt window, controller polling, arcade mixer, asynchronous BLE worker.
- `hub/hub_controller.py`: canonical GUI Hub program with watchdog.
- `launch.py`, `SPIKE Controller.spec`, `build_windows.bat`: packaging entry.
- `backups/original/`: byte-for-byte backups of the supplied files.
- Root `ps4_spike.py` and `hub_controller.py`: untouched original CLI path.
  The GUI only loads the canonical program under `hub/`.

```powershell
python -m compileall -q app hub tests launch.py
python -m unittest discover -s tests -v
python -m app.main --smoke-test
```

Automated tests use fake BLE and Pybricks APIs; they do not establish a real
Bluetooth connection. See `TEST_RESULTS.md` for this workstation's executed
checks. A physical Hub/PS4 test and a clean recipient PC test are required
before claiming end-to-end robot or distribution compatibility.

## Responsive window

The window adapts to narrow widths by stacking connection statuses and buttons.
Instructions wrap, and smaller screens can scroll the content vertically.
The initial size fits the available screen area, including Windows display scaling.
A muted, centered Developed by Ahmed Shaaban footer stays below the content
and remains visible while resizing or scrolling.
