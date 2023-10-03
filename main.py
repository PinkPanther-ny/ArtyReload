import math
import multiprocessing
import os
import sys
import threading
import time
import tkinter as tk
from string import Template
from threading import Thread, Lock

import keyboard
import pyautogui
from PIL import ImageTk, Image

from audio import speak, init_audio, terminate_audio
from log_template import get_aim_string, get_target_string
from ocr import get_arty_mil, get_arty_angle
from util import do_task_for_time, switch_to_second, hold_key, switch_focus_to

pyautogui.FAILSAFE = False


def is_integer(p):
    return p == "" or p.isdigit()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # noqa
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ShootingController:
    def __init__(self):
        self.interrupt = False
        self.in_progress = False

    def reload_and_shoot(self, n):
        if self.in_progress:
            return
        self.in_progress = True
        self.interrupt = False

        count_shoot = 0
        for ith_shell in range(n):
            if self.interrupt:
                break
            print(f"Reloading {ith_shell + 1} out of {n}")
            speak(f"Reloading {ith_shell + 1} out of {n}")

            with switch_to_second():
                do_task_for_time(lambda: pyautogui.press('R'), 1)
                time.sleep(2.6)
            do_task_for_time(lambda: pyautogui.click(), 0.4)

            count_shoot += 1

        print(f"Shoot {count_shoot} finished")
        speak(f"Shoot {count_shoot} finished")
        self.in_progress = False

    def stop_execution(self):
        self.interrupt = True
        print(f"Shooting cancelled!")
        speak(f"Shooting cancelled!")


class Arty:
    def __init__(self, location):

        self.location = location
        self.levitation = None
        self.direction = None

        self.target = None
        self.target_distance = None
        self.target_levitation = None
        self.target_direction = None

        self.aim_lock = Lock()

        print(f"Artillery location set, {location}")
        speak(f"Artillery location set")

    def ocr_set_current_levi_and_dir(self):
        self.levitation = get_arty_mil()
        self.direction = get_arty_angle()

    def set_target(self, target):
        self.target = target

        # Calculate target distance and levitation
        cx, cy = self.location
        px, py = target

        # 88 pixels per 200m block
        distance = math.sqrt((px - cx) ** 2 + (py - cy) ** 2) * (200 / 88)
        self.target_distance = round(distance)
        self.target_levitation = round(-0.237 * self.target_distance + 1001.7)

        # Calculate target direction
        angle = math.degrees(math.atan2(-(py - cy), px - cx))
        angle = (90 - angle) % 360
        if angle < 0:
            angle += 360

        self.target_direction = round(angle, 1)
        print(get_target_string(self))
        speak(f"Target set")

    def aim_target(self):
        """Determine the shortest turn direction and distance."""
        with self.aim_lock:
            speak("Start aiming!")
            print(get_aim_string(self))
            diff_inside = abs(self.direction - self.target_direction)
            diff_outside = 360 - diff_inside
            is_target_less = self.target_direction < self.direction

            if diff_inside < diff_outside:
                operation = 'A' if is_target_less else 'D'
                diff = diff_inside
            else:
                operation = 'D' if is_target_less else 'A'
                diff = diff_outside

            # Adjust levitation and direction
            hold_key(
                'W' if self.levitation < self.target_levitation else 'S',
                0.2246 * abs(self.levitation - self.target_levitation)
            )

            with switch_to_second():
                hold_key(operation, abs(diff))

            print("Done!")

    def aim_target_threaded(self):
        # Run aim_target in its own thread and return its expected duration
        diff_inside = abs(self.direction - self.target_direction)
        diff_outside = 360 - diff_inside
        total_duration = (0.2246 * abs(self.levitation - self.target_levitation) +
                          min(diff_inside, diff_outside)) + 3
        if not self.aim_lock.locked():
            thread = Thread(target=self.aim_target)
            thread.start()
            print(total_duration, "total_duration")
            return total_duration
        else:
            print("Already aiming, cannot start another aim concurrently.")
            return 0


class AutoArtyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.arty = None
        self.shooting_controller = ShootingController()
        self.number_buffer = [0, 0, 0, 0]

        self.wm_attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#000000")
        self.wm_attributes('-fullscreen', 'True')
        self.wm_attributes("-alpha", 0.0)
        self.config(bg='#000000')
        self.title("ArtyStatsDisplay")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        ico = ImageTk.PhotoImage(Image.open(resource_path('images/arty.ico')))
        self.iconphoto(False, ico)  # noqa

        # Create a Tcl wrapper for the integer validation function
        self.integer_validation = self.register(is_integer)

        self.canvas = tk.Canvas(self, width=320, height=200)
        self.canvas.place(relx=1720 / 1920, rely=190 / 1080, anchor='center')

        self.title_label = tk.Label(self.canvas, text="OCR RESULTS:")
        self.title_label.place(x=10, y=10)

        self.label1 = tk.Label(self.canvas, text="Current levitation:")
        self.label1.place(x=10, y=40)
        self.value1 = tk.StringVar()
        self.entry1 = tk.Entry(self.canvas, textvariable=self.value1,
                               validate='key', validatecommand=(self.integer_validation, '%P'))
        self.entry1.place(x=120, y=40)
        self.entry1.place(x=120, y=40)

        self.label2 = tk.Label(self.canvas, text="Current direction:")
        self.label2.place(x=10, y=70)
        self.value2 = tk.StringVar()
        self.entry2 = tk.Entry(self.canvas, textvariable=self.value2,
                               validate='key', validatecommand=(self.integer_validation, '%P'))
        self.entry2.place(x=120, y=70)

        self.confirm_button = tk.Button(self.canvas, text="Confirm", command=self.confirm)
        self.confirm_button.place(x=250, y=40, width=50, height=50)

        self.text_template = Template("""
        Levitation: $levitation       ==>> Target : $target_levitation
        Direction : $direction ($direction2) ==>> Target : $target_direction ($target_direction2) 
        """)

        self.value3 = tk.StringVar()
        self.label3 = tk.Label(self.canvas, textvariable=self.value3, justify='left')
        self.label3.place(x=10, y=100)

        self.is_visible = False
        self.add_hotkeys()

    def record_number(self, key: keyboard.KeyboardEvent):
        if key.name.isdigit():
            self.number_buffer.pop(0)
            self.number_buffer.append(int(key.name))

    def calculate_levitation_from_keyboard(self):
        distance = sum(self.number_buffer[idx] * 10 ** (3 - idx) for idx in range(4))
        levitation = round(-0.237 * distance + 1001.7)
        print(f"Distance {distance} - Levitation {levitation}")
        speak(f"Levitation {levitation}")

    def switch_visibility(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def hide(self):
        self.wm_attributes("-alpha", 0)
        self.is_visible = False

    def show(self):
        self.wm_attributes("-alpha", 0.5)
        self.is_visible = True

    def run(self):
        self.mainloop()

    @staticmethod
    def redeploy():
        time.sleep(0.3)
        pyautogui.click(150, 700)
        pyautogui.click(840, 590)
        print("Redeploy!")
        speak("Redeploy!")

    @staticmethod
    def force_quit():
        os._exit(0)  # noqa

    @staticmethod
    def force_quit_all():
        name = "HLL-Win64-Shipping.exe"
        os.system(f'tasklist | find /i "{name}" && taskkill /im {name} /F || echo process "{name}" not running.')
        os._exit(0)  # noqa

    def add_hotkeys(self):
        keyboard.add_hotkey('CTRL+V', self.switch_visibility)
        keyboard.add_hotkey('CTRL+SHIFT+X', self.update_arty)
        keyboard.add_hotkey('CTRL+X', self.update_target)
        keyboard.add_hotkey('CTRL+SPACE', self.confirm)
        keyboard.add_hotkey('CAPSLOCK', self.calculate_levitation_from_keyboard)
        keyboard.add_hotkey('GRAVE+ESC', self.redeploy)
        keyboard.add_hotkey('CTRL+Q', self.force_quit)
        keyboard.add_hotkey('CTRL+SHIFT+DELETE', self.force_quit_all)

        for i in range(1, 10):
            keyboard.add_hotkey(
                f'SHIFT+{i}',
                lambda x=i: threading.Thread(
                    target=self.shooting_controller.reload_and_shoot, args=(x,)
                ).start()
            )

        keyboard.add_hotkey('DELETE', self.shooting_controller.stop_execution)
        keyboard.on_press(self.record_number, suppress=False)

    def update_arty(self):
        self.arty = Arty(pyautogui.position())

    def update_target(self):
        if self.arty is None:
            print(f"Artillery location not set")
            speak(f"Artillery location not set")
            return
        self.arty.set_target(pyautogui.position())
        self.value3.set(get_target_string(self.arty))
        pyautogui.press("M")
        self._update_arty_ocr_result()
        switch_focus_to("ArtyStatsDisplay")
        pyautogui.moveTo(1720, 190)

    def _update_arty_ocr_result(self):
        self.arty.ocr_set_current_levi_and_dir()
        self.show()
        self.entry1.config(state='normal')
        self.entry2.config(state='normal')
        self.value1.set(str(self.arty.levitation))
        self.value2.set(str(self.arty.direction))

    def confirm(self):
        if not self.is_visible:
            return
        switch_focus_to("Hell Let Loose  ")
        self.arty.levitation = int(self.value1.get())
        self.arty.direction = int(self.value2.get())

        self.canvas.configure(height=260)
        self.value3.set(self.value3.get() + get_aim_string(self.arty))
        self.entry1.config(state='readonly')
        self.entry2.config(state='readonly')

        duration = int(self.arty.aim_target_threaded() * 1000)
        if duration > 0:
            self.after(duration + 500, self.hide)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    init_audio()
    print("""
    Instruction:
    1. Press 'CTRL+V' to toggle the visibility of the application window.

    2. Press 'CTRL+X' to set the target position based on the cursor's current location.

    3. Press 'CTRL+SHIFT+X' to set the artillery position based on the cursor's current location.

    4. Press 'CTRL+SPACE' to confirm the OCR results and start aiming.

    5. Press 'CAPSLOCK' after entering a four-digit number to calculate and announce the levitation for the artillery.

    6. Press 'CTRL+Q' to force quit the application.

    7. Press 'DELETE' to cancel any ongoing shooting action.

    8. Press 'SHIFT+<number>' to initiate the reloading and shooting action <number> times.

    9. Press 'GRAVE+ESC' to perform a redeploy action in the game.

    10. Press 'CTRL+SHIFT+DELETE' to quit both HLL game process and this app.

    """)

    app = AutoArtyApp()
    app.mainloop()
    terminate_audio()
