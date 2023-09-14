import os
import threading
import time
from multiprocessing import Process

import keyboard
import mouse
import pyttsx3

stop = False
in_progress = False
number_buffer = [0, 0, 0, 0]


class Audio:
    engine = None
    rate = None

    def __init__(self, text):
        self.text = text
        self.process = Process(target=self._say)
        self.process.start()

    def _say(self):
        engine = pyttsx3.init()
        engine.say(self.text)
        engine.runAndWait()
        del self


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

    do_task_for_time(lambda: keyboard.send('R'), 1)
    time.sleep(2.6)

    hold_key('f1', 1.4)
    time.sleep(0.1)

    do_task_for_time(lambda: mouse.click(), 0.4)


def reload_and_shoot(n):
    global stop, in_progress
    if in_progress:
        return
    in_progress = True

    t0 = time.time()
    stop = False

    count_shoot = 0
    for ith_shell in range(n):
        if stop:
            break
        Audio(f"Reload {ith_shell + 1} out of {n}")
        _reload_and_shoot()
        count_shoot += 1

    print((time.time() - t0) / n)
    Audio(f"Shoot {count_shoot} finished")
    in_progress = False


def stop_execution():
    global stop
    stop = True
    Audio(f"Shooting cancelled!")


def exit_program():
    print("Exiting the program...")
    os._exit(0)


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
        print(f"Distance {distance}, levitation: {allies}, {soviet}")
        Audio(f"Distance {distance}, levitation: {allies}, {soviet}")


if __name__ == '__main__':
    # Assign hotkeys to perform actions
    for i in range(1, 10):
        keyboard.add_hotkey(f'SHIFT+{i}',
                            lambda x=i: threading.Thread(target=reload_and_shoot, args=(x,)).start())

    keyboard.add_hotkey('DELETE', stop_execution)
    keyboard.add_hotkey(f'SHIFT+Q', exit_program)
    keyboard.add_hotkey(f'CAPSLOCK', calculate_levitation)
    keyboard.on_press(record_number, suppress=False)

    keyboard.wait()

    # pyinstaller.exe --icon=arty.ico -F arty_reload.py --noconsole
