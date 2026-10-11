import asyncio
import sys

# ==========================================
# WINDOWS BLUETOOTH FIX
# ==========================================

if sys.platform == "win32":
    from bleak.backends.winrt.util import allow_sta
    allow_sta()

from pybricksdev.ble import find_device
from pybricksdev.connections.pybricks import PybricksHubBLE

import pygame


# ==========================================
# SETTINGS
# ==========================================

HUB_NAME = "Pybricks Hub"
HUB_PROGRAM = "hub_controller.py"

MAX_SPEED = 80
DEADZONE = 0.12
SEND_DELAY = 0.05


async def main():

    hub = None

    # ======================================
    # FIND HUB
    # ======================================

    print()
    print("==============================")
    print("Searching for Pybricks Hub...")
    print("==============================")
    print()

    try:

        device = await find_device(
            name=HUB_NAME,
            timeout=15
        )

    except asyncio.TimeoutError:

        print("ERROR: Pybricks Hub not found!")
        return

    except Exception as e:

        print("Bluetooth Error:")
        print(type(e).__name__)
        print(e)
        return


    print("Hub found:", device.name)

    # ======================================
    # CONNECT
    # ======================================

    hub = PybricksHubBLE(device)

    print("Connecting to SPIKE...")

    try:

        await hub.connect()

    except Exception as e:

        print("Connection Error:")
        print(type(e).__name__)
        print(e)
        return


    print("CONNECTED!")

    # ======================================
    # RUN HUB PROGRAM
    # ======================================

    try:

        print("Uploading + starting hub_controller.py...")

        await hub.run(
            HUB_PROGRAM,
            wait=False,
            print_output=True,
            line_handler=True
        )

        await asyncio.sleep(2)

        print()
        print("Hub program started!")

    except Exception as e:

        print()
        print("ERROR starting hub program:")
        print(type(e).__name__)
        print(e)

        try:
            await hub.disconnect()
        except Exception:
            pass

        return


    # ======================================
    # START PS4
    # ======================================

    print()
    print("Starting PS4 Controller...")

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:

        print("ERROR: PS4 Controller not found!")

        try:
            await hub.write_line("0,0")
        except Exception:
            pass

        try:
            await hub.disconnect()
        except Exception:
            pass

        pygame.quit()
        return


    controller = pygame.joystick.Joystick(0)
    controller.init()

    print("Controller:", controller.get_name())

    # ======================================
    # READY
    # ======================================

    print()
    print("==============================")
    print("            READY")
    print("==============================")
    print()
    print("LEFT ANALOG")
    print()
    print("UP    = Forward")
    print("DOWN  = Backward")
    print("LEFT  = Turn Left")
    print("RIGHT = Turn Right")
    print()
    print("CTRL+C = STOP")
    print()

    # ======================================
    # CONTROL LOOP
    # ======================================

    try:

        while True:

            pygame.event.pump()

            # ------------------------------
            # READ LEFT STICK
            # ------------------------------

            x = controller.get_axis(0)
            y = -controller.get_axis(1)

            # ------------------------------
            # DEADZONE
            # ------------------------------

            if abs(x) < DEADZONE:
                x = 0.0

            if abs(y) < DEADZONE:
                y = 0.0

            # ------------------------------
            # ARCADE DRIVE
            # ------------------------------

            left = y + x
            right = y - x

            # ------------------------------
            # NORMALIZE
            # ------------------------------

            maximum = max(
                1.0,
                abs(left),
                abs(right)
            )

            left /= maximum
            right /= maximum

            # ------------------------------
            # MOTOR POWER
            # ------------------------------

            left_power = int(
                left * MAX_SPEED
            )

            right_power = int(
                right * MAX_SPEED
            )

            # ------------------------------
            # SEND TO HUB STDIN
            # ------------------------------

            await hub.write_line(
                f"{left_power},{right_power}"
            )

            print(
                f"Motor A: {left_power:4}   "
                f"Motor B: {right_power:4}",
                end="\r"
            )

            await asyncio.sleep(
                SEND_DELAY
            )


    except KeyboardInterrupt:

        print()
        print()
        print("STOP requested.")


    except Exception as e:

        print()
        print()
        print("CONTROL ERROR:")
        print(type(e).__name__)
        print(e)


    finally:

        # ==================================
        # STOP MOTORS
        # ==================================

        print()
        print("Stopping motors...")

        try:

            await hub.write_line("0,0")

            await asyncio.sleep(0.2)

        except Exception:
            pass


        pygame.quit()


        # ==================================
        # DISCONNECT
        # ==================================

        print("Disconnecting SPIKE...")

        try:

            await hub.disconnect()

        except Exception:
            pass


        print("DONE.")


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print("Stopped.")