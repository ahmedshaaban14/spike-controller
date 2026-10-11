"""Read-only hardware availability probe; does not connect or drive."""
import asyncio
import json
import os
from pathlib import Path
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from pybricksdev.ble import find_device
from bleak.backends.winrt.util import uninitialize_sta

pygame.display.init()
pygame.joystick.init()
result = {"controllers": []}
for i in range(pygame.joystick.get_count()):
    controller = pygame.joystick.Joystick(i)
    controller.init()
    result["controllers"].append(controller.get_name())
pygame.quit()
uninitialize_sta()
async def probe():
    try:
        device = await find_device(name="Pybricks Hub", timeout=5)
        result["hub"] = device.name
    except Exception as exc:
        result["hub"] = f"{type(exc).__name__}: {exc}"
asyncio.run(probe())
Path("verification/hardware_probe.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
