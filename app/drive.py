"""Original arcade mixing, with per-axis D-pad overrides."""
MAX_SPEED = 80
DEADZONE = 0.12


def motor_power(x, y, hat=(0, 0), speed=100):
    x = 0.0 if abs(x) < DEADZONE else x
    y = 0.0 if abs(y) < DEADZONE else y
    if hat[0]:
        x = hat[0]
    if hat[1]:
        y = hat[1]
    left, right = y + x, y - x
    maximum = max(1.0, abs(left), abs(right))
    scale = MAX_SPEED * max(10, min(100, speed)) / 100
    return tuple(max(-100, min(100, int(v / maximum * scale))) for v in (left, right))
