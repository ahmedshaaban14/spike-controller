from pybricks.hubs import EssentialHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait

import uselect
import sys


hub = EssentialHub()

# Motor A normal
motor_a = Motor(
    Port.A,
    positive_direction=Direction.CLOCKWISE
)

# Motor B reversed
motor_b = Motor(
    Port.B,
    positive_direction=Direction.COUNTERCLOCKWISE
)

poll = uselect.poll()
poll.register(sys.stdin)

print("READY")


while True:

    if poll.poll(0):

        line = sys.stdin.readline().strip()

        try:

            left, right = line.split(",")

            left = int(left)
            right = int(right)

            motor_a.dc(left)
            motor_b.dc(right)

        except Exception:
            pass

    wait(10)