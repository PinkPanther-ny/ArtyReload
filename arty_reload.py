import multiprocessing
import threading
import time

import keyboard
import pyautogui

from audio import speak, terminate_audio, init_audio
from ocr import get_arty_angle, get_arty_mil
from util import get_angle_from_map, shortest_turn_direction, get_distance_from_map, switch_to_second, hold_key, \
    do_task_for_time

pyautogui.FAILSAFE = False

stop = False
in_progress = False
number_buffer = [0, 0, 0, 0]

arty_type_is_allies = True
arty_location = (-1, -1)


def _reload_and_shoot():
    with switch_to_second():
        print("Reloading")
        do_task_for_time(lambda: pyautogui.press('R'), 1)
        time.sleep(2.6)

    print("Fire!")
    do_task_for_time(lambda: pyautogui.click(), 0.4)


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


def calculate_levitation(distance):
    allies = round(-0.237 * distance + 1001.7)
    soviet = round(-0.213 * distance + 1141.3)
    levitation = allies if arty_type_is_allies else soviet
    print(f"Distance {round(distance)}, levitation: allies {allies}, soviet {soviet}")

    global number_buffer
    number_buffer = [int(c) for c in str(round(distance)).zfill(4)]

    return levitation


def calculate_levitation_from_keyboard():
    distance = sum(number_buffer[idx] * 10 ** (3 - idx) for idx in range(4))
    levitation = calculate_levitation(distance)
    speak(f"levitation {levitation}")


def switch_arty_type():
    global arty_type_is_allies
    arty_type_is_allies = not arty_type_is_allies
    print(f"Artillery type switched, currently {'allies' if arty_type_is_allies else 'soviet'}")
    speak(f"Artillery type switched, currently {'allies' if arty_type_is_allies else 'soviet'}")


def set_arty_location():
    global arty_location
    arty_location = pyautogui.position()
    print(f"Artillery location set, {arty_location}")
    speak(f"Artillery location set")


def move_arty():
    global arty_location
    if arty_location == (-1, -1):
        print(f"Artillery location not set")
        speak(f"Artillery location not set")
        return

    origin, target = arty_location, pyautogui.position()

    target_distance = get_distance_from_map(origin, target)
    if not (100 <= target_distance <= 1600):
        speak(f"Invalid distance!")
        print(f"Invalid distance!")
        return

    pyautogui.press('M')
    time.sleep(0.2)

    # Gather info
    # TODO: Add value manual check
    current_levitation = get_arty_mil()
    if current_levitation == -1:
        speak(f"Invalid levitation!")
        print(f"Invalid levitation!")
        return

    current_1_angle = get_arty_angle()
    if current_1_angle == -1:
        speak(f"Invalid direction!")
        print(f"Invalid direction!")
        return

    # Calculate target levitation and direction
    target_levitation = calculate_levitation(target_distance)
    target_angle = get_angle_from_map(origin, target)
    turn_direction, d_angle = shortest_turn_direction(current_1_angle, target_angle)

    speak(f"Current angle {current_1_angle}, target angle {round(target_angle, 1)}")
    print(f"Current angle {current_1_angle}, target angle {round(target_angle, 1)}")

    speak(f"Current levitation {current_levitation}, target levitation {round(target_levitation)}")
    print(f"Current levitation {current_levitation}, target levitation {round(target_levitation)}")

    # Adjust levitation and direction
    hold_key(
        'W' if current_levitation < target_levitation else 'S',
        0.2246 * abs(current_levitation - target_levitation)
    )

    with switch_to_second():
        hold_key(turn_direction, abs(d_angle))


def redeploy():
    time.sleep(0.3)
    pyautogui.click(150, 700)
    pyautogui.click(840, 590)
    for _ in range(5):
        time.sleep(10)
        try:
            pyautogui.locateOnScreen('images/REDEPLOY.png', region=(760, 520, 1200, 580))
            pyautogui.press('space')
        except pyautogui.ImageNotFoundException:
            pass


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
    keyboard.add_hotkey('CAPSLOCK', calculate_levitation_from_keyboard)
    keyboard.add_hotkey('CTRL+S', set_arty_location)
    keyboard.add_hotkey('CTRL+SHIFT+S', move_arty)
    keyboard.add_hotkey('SHIFT+ESC', redeploy)
    keyboard.on_press(record_number, suppress=False)

    keyboard.wait('SHIFT+Q')
    terminate_audio()
