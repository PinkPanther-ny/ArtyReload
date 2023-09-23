import math
import time
from contextlib import contextmanager
from functools import wraps

import pyautogui


def get_angle_from_map(origin, target):
    cx, cy = origin
    px, py = target

    dx = px - cx
    dy = py - cy

    angle = math.degrees(math.atan2(-dy, dx))

    angle = (90 - angle) % 360
    if angle < 0:
        angle += 360

    return angle


def get_distance_from_map(origin, target):
    cx, cy = origin
    px, py = target

    dx = px - cx
    dy = py - cy

    # 88 pixels per 200m block
    pixel_distance = math.sqrt(dx ** 2 + dy ** 2)
    distance = pixel_distance * (200 / 88)

    return distance


def shortest_turn_direction(current_dir, target_dir):
    """Determine the shortest turn direction and distance."""
    diff_inside = abs(target_dir - current_dir)
    diff_outside = 360 - max(target_dir, current_dir) + min(target_dir, current_dir)
    if target_dir < current_dir:
        if diff_inside < diff_outside:
            return 'A', diff_inside
        else:
            return 'D', diff_outside
    else:
        if diff_inside < diff_outside:
            return 'D', diff_inside
        else:
            return 'A', diff_outside


def hold_key(key, duration):
    with pyautogui.hold(key):
        print(f"Holding {key}")
        time.sleep(duration)
        print(f"Release {key}")


def do_task_for_time(task, duration, fps=100):
    t0 = time.time()
    while time.time() - t0 < duration:
        task()
        time.sleep(1 / fps)


def manual_check_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"Function {func.__name__} returned {result}. Is this okay? [Press Enter if yes]")
        user_input = input()

        if user_input == "":
            return result
        else:
            try:
                new_result = float(user_input)
                print(f"Returning manually entered value: {new_result}")
                return new_result
            except ValueError:
                print("Invalid input. Returning original result.")
                return result

    return wrapper


@contextmanager
def switch_to_second():
    try:
        hold_key('F2', 1.4)
        time.sleep(0.1)
        yield  # This is where foo() will be executed.
    finally:
        hold_key('F1', 1.4)
        time.sleep(0.1)
