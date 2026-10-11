from pybricks.hubs import EssentialHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait, StopWatch
import uselect
import sys

hub = EssentialHub()
motor_a = Motor(Port.A, positive_direction=Direction.CLOCKWISE)
motor_b = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)
watchdog = StopWatch()
buffer = ""
stopped = True
motor_a.dc(0)
motor_b.dc(0)
print("READY")

try:
    while True:
        # Read only available characters: an incomplete line cannot block safety.
        for _ in range(64):
            if not poll.poll(0):
                break
            char = sys.stdin.read(1)
            if not char:
                break
            if char == "\n":
                try:
                    left, right = buffer.strip().split(",")
                    left = max(-100, min(100, int(left)))
                    right = max(-100, min(100, int(right)))
                    motor_a.dc(left)
                    motor_b.dc(right)
                    watchdog.reset()
                    stopped = left == 0 and right == 0
                except Exception:
                    pass
                buffer = ""
            elif len(buffer) < 32:
                buffer += char
            else:
                buffer = ""
        if watchdog.time() >= 500 and not stopped:
            motor_a.dc(0)
            motor_b.dc(0)
            stopped = True
        wait(10)
finally:
    motor_a.dc(0)
    motor_b.dc(0)
