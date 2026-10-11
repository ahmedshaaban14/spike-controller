# Local verification — 11 October 2026

Environment: Windows 10 x64 (build 19045), Python 3.11.4,
PySide6 6.12.0, pygame 2.6.1, pybricksdev 2.3.2, bleak 3.0.2,
PyInstaller 6.22.3.

Passed:

- SHA-256 comparison: both backups match the untouched original files.
- Python syntax compilation for app, Hub source, launch entry and tests.
- `pip check`: no broken requirements.
- Seven automated tests: original drive direction/deadzone/speed, per-axis
  D-pad overrides, normalization/clamping, partial-line watchdog at 500 ms,
  failed startup gating, STOP latch, stale-input zeroing, disconnect cleanup,
  scan cancellation, and Qt close during scan without duplicate workers.
- Development GUI startup, screenshot capture and clean close; layout visually
  inspected. Screenshot: `verification/gui.png`.
- Offline source compilation of Hub source using pybricksdev for MPY ABI 5
  (816 bytes) and ABI 6 (876 bytes), plus WinRT BLE backend import.
  Evidence: `verification/source_bundle.json`.

Hardware availability probe: no pygame controllers detected; a five-second
read-only scan for `Pybricks Hub` timed out. It did not connect, upload or move
motors. Evidence: `verification/hardware_probe.json`.

Not verified: installed Hub firmware/API compatibility, real BLE upload and
READY handshake, PS4 axes/D-pad mapping with the actual driver, calibrated
robot movement, real watchdog timing, controller/link-loss stop delivery, or
execution on another clean Windows PC. Test with the wheels raised first.

Packaging passed:

- Executed `build_windows.bat` successfully. Folder distribution:
  `dist/SPIKE Controller/` (about 139 MB before documentation).
- Packaged `SPIKE Controller.exe --verify-bundle` exited 0: GUI opened,
  rendered and closed; bundled Hub source loaded; both MPY compilers worked;
  the ABI 6 frozen compiler-helper subprocess returned valid output; WinRT
  backend imported. Evidence: `verification/packaged_bundle.json` and `.png`.
- Repeated bundle verification with the working directory outside this project
  (`%TEMP%`), exit 0. Evidence: `verification/isolated_bundle.json`.
- Normal EXE entry with `--smoke-test`, also from `%TEMP%`, exited 0.
- Packaged screenshot visually inspected; no clipping or missing widgets.

The initial broad dependency collection was stopped and narrowed to avoid
bundling unrelated scientific/CLI libraries. Build warnings about deprecated
pygame pkg_resources, optional USB backend, and packaging license validation
did not prevent the above BLE/GUI/compiler checks. USB control is not used.
The current setuptools version is pinned for pygame compatibility.

These package checks ran on the development workstation with the bundled
runtime. They establish local startup/compilation, not compatibility with
every recipient PC or successful robot control.

## Responsive UI update (2026-10-11)

- All 8 automated tests passed, including layout checks at 360x320, 640x480,
  900x800 and 1200x900 logical pixels.
- Both window tests also passed with QT_SCALE_FACTOR=2.
- Verified footer visibility, separation from scrolling content, button bounds,
  readable status labels, compact row directions and scroll access to STOP.
- Screenshots saved under verification/responsive-*.png.
- No physical second-PC or robot test was performed for this update.

- Final Windows EXE package verification passed: GUI, responsive footer at
  640x480 and 360x320, bundled Hub source, both compiler ABIs and WinRT backend.
  Result: verification/responsive-bundle-final.json.
