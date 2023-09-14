import os
import threading
import time

import keyboard
import mouse
import winsound

stop = False
in_progress = False


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
    winsound.MessageBeep(winsound.MB_OK)

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

    stop = False
    for _ in range(n):
        if stop:
            break
        _reload_and_shoot()
    in_progress = False


def stop_execution():
    global stop
    stop = True
    winsound.MessageBeep(winsound.MB_ICONHAND)


def exit_program():
    print("Exiting the program...")
    os._exit(0)


# Assign hotkeys to perform actions
for i in range(1, 10):
    keyboard.add_hotkey(f'SHIFT+{i}', lambda x=i: threading.Thread(target=reload_and_shoot, args=(x,)).start())

keyboard.add_hotkey('DELETE', stop_execution)
keyboard.add_hotkey(f'SHIFT+Q', exit_program)

keyboard.wait()

# pyinstaller.exe --icon=arty.ico -F arty_reload.py --noconsole
