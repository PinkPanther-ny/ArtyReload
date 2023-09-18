import math
import multiprocessing
import threading
import time

import keyboard
import mouse

from audio import speak, terminate_audio, init_audio

stop = False
in_progress = False
number_buffer = [0, 0, 0, 0]

arty_type_is_allies = True
arty_location = (-1, -1)
SECOND_POSITION_OFFSET = -47


def hold_key(key, duration):
    print(f"Holding {key}")
    keyboard.press(key)
    time.sleep(duration)
    keyboard.release(key)
    print(f"Release {key}")


def do_task_for_time(task, duration, fps=100):
    t0 = time.time()
    while time.time() - t0 < duration:
        task()
        time.sleep(1 / fps)


def _reload_and_shoot():
    hold_key('f2', 1.4)
    time.sleep(0.1)

    print("Reloading")
    do_task_for_time(lambda: keyboard.send('R'), 1)
    time.sleep(2.6)

    hold_key('f1', 1.4)
    time.sleep(0.1)

    print("Fire!")
    do_task_for_time(lambda: mouse.click(), 0.4)


def reload_and_shoot(n):
    global stop, in_progress
    if in_progress:
        return
    in_progress = True

    stop = False

    count_shoot = 0
    for ith_shell in range(n):
        if stop:
            break
        print(f"Reload {ith_shell + 1} out of {n}")
        speak(f"Reload {ith_shell + 1} out of {n}")
        _reload_and_shoot()
        count_shoot += 1

    print(f"Shoot {count_shoot} finished")
    speak(f"Shoot {count_shoot} finished")
    in_progress = False


def stop_execution():
    global stop
    stop = True
    print(f"Shooting cancelled!")
    speak(f"Shooting cancelled!")


def record_number(key: keyboard.KeyboardEvent):
    global number_buffer
    if key.name.isdigit():
        number_buffer.pop(0)
        number_buffer.append(int(key.name))


def calculate_levitation():
    distance = sum(number_buffer[idx] * 10 ** (3 - idx) for idx in range(4))
    if 100 <= distance <= 1600:
        allies = round(-0.237 * distance + 1001.7)
        soviet = round(-0.213 * distance + 1141.3)
        print(f"Distance {distance}, levitation: allies {allies}, soviet {soviet}")
        speak(f"{allies if arty_type_is_allies else soviet}")


def switch_arty_type():
    global arty_type_is_allies
    arty_type_is_allies = not arty_type_is_allies
    print(f"Artillery type switched, currently {'allies' if arty_type_is_allies else 'soviet'}")
    speak(f"Artillery type switched, currently {'allies' if arty_type_is_allies else 'soviet'}")


def set_arty_location():
    global arty_location
    arty_location = mouse.get_position()
    print(f"Artillery location set, {arty_location}")
    speak(f"Artillery location set, {arty_location}")


def calculate_angle():
    global arty_location
    if arty_location == (-1, -1):
        print(f"Artillery location not set")
        speak(f"Artillery location not set")
        return

    cx, cy = arty_location
    px, py = mouse.get_position()

    dx = px - cx
    dy = py - cy

    angle = math.degrees(math.atan2(-dy, dx))

    final_angle = (90 - angle) % 360 + SECOND_POSITION_OFFSET
    if final_angle < 0:
        final_angle += 360

    print(f"Artillery angle, {round(final_angle, 1)}")
    speak(f"Artillery angle, {round(final_angle, 1)}")


if __name__ == '__main__':

    multiprocessing.freeze_support()
    init_audio()
    print("""
    Instruction:
    The program simulates artillery shooting and calculates levitation based on distance.

    1. Press 'SHIFT+number' (number from 1 to 9) to initiate reloading and shooting the specified number of times. 
       For example, 'SHIFT+3' will reload and shoot three times.

    2. Press 'DELETE' to cancel the shooting action in progress.

    3. Press 'SHIFT+TAB' to switch the artillery type. The program supports two artillery types: allies and soviet. 
       It will announce the current artillery type upon switching.

    4. Press 'SHIFT+O' to set artillery location. Press 'SHIFT+P' to calculate artillery angle from second position. 

    5. During the game, you can input a four-digit number. After inputting the number, press 'CAPSLOCK' to calculate 
       and announce the levitation for the current artillery type based on the inputted distance. The distance should be 
       between 100 and 1600.

    6. To exit the program, press 'SHIFT+Q'.

    """)

    # Assign hotkeys to perform #actions
    for i in range(1, 10):
        keyboard.add_hotkey(f'SHIFT+{i}',
                            lambda x=i: threading.Thread(target=reload_and_shoot, args=(x,)).start())

    keyboard.add_hotkey('DELETE', stop_execution)
    keyboard.add_hotkey('SHIFT+TAB', switch_arty_type)
    keyboard.add_hotkey('CAPSLOCK', calculate_levitation)
    keyboard.add_hotkey('right shift+O', set_arty_location)
    keyboard.add_hotkey('right shift+P', calculate_angle)
    keyboard.on_press(record_number, suppress=False)

    keyboard.wait('SHIFT+Q')
    terminate_audio()
