import runpy
import sys


def attach_helper_streams():
    """Restore inherited pipes for a windowed compiler helper subprocess."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    import ctypes
    from ctypes import wintypes
    import msvcrt
    import os
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    for name, identifier in (("stdout", -11), ("stderr", -12)):
        handle = kernel.GetStdHandle(identifier & 0xffffffff)
        if handle and handle != wintypes.HANDLE(-1).value:
            fd = msvcrt.open_osfhandle(handle, os.O_WRONLY)
            setattr(sys, name, os.fdopen(fd, "w", encoding="utf-8", buffering=1))

if __name__ == "__main__":
    # pybricksdev invokes mpy-tool via `sys.executable -m ...`. In a frozen
    # app sys.executable is this EXE, so dispatch that helper before Qt loads.
    if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "pybricksdev._vendored.mpy_tool_v6_3"]:
        attach_helper_streams()
        sys.argv = [sys.argv[2], *sys.argv[3:]]
        runpy.run_module("pybricksdev._vendored.mpy_tool_v6_3", run_name="__main__")
    elif "--verify-bundle" in sys.argv:
        from app.bundle_check import verify
        raise SystemExit(verify())
    else:
        from app.main import main
        raise SystemExit(main())
