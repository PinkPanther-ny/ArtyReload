import argparse
import math
import multiprocessing
import os
import subprocess
import threading
import time
import tkinter as tk
from threading import Thread, Lock

import keyboard
import pyautogui
from PIL import ImageTk, Image

from audio import speak, init_audio, terminate_audio
from build_assist import BuildAssist
from log_template import get_aim_string, get_target_string
from magnifier import MagnifierApp
from map_data import map_data
from ocr import get_arty_mil, get_arty_angle
from util import do_task_for_time, switch_to_second, hold_key, switch_focus_to, resource_path, check_process_exists

pyautogui.FAILSAFE = False

MAP_SOUTH_EAST = (520, 971)


def is_integer(p):
    return p == "" or p.isdigit()


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
            speak(f"{ith_shell + 1} out of {n}", rate=250)

            with switch_to_second():
                do_task_for_time(lambda: pyautogui.press('R'), 1 + 2.6, fps=30)

            if self.interrupt:
                break
            do_task_for_time(lambda: pyautogui.click(), 0.4, fps=30)

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
        self.wm_attributes("-alpha", 1)
        self.config(bg='#000000')
        self.title("ArtyStatsDisplay")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        ico = ImageTk.PhotoImage(Image.open(resource_path('images/arty.ico')))
        self.iconphoto(False, ico)  # noqa

        self.canvas1 = tk.Canvas(self, width=320, height=200, highlightthickness=0)
        self.tickbox_var = tk.IntVar()
        self.checkbutton = tk.Checkbutton(self.canvas1,
                                          text="Enable Build Assist",
                                          variable=self.tickbox_var,
                                          command=self.toggle_build_assist)
        self.checkbutton.place(x=180, y=10)
        self.title_label = tk.Label(self.canvas1, text="OCR RESULTS:")
        self.title_label.place(x=10, y=10)

        # Create a Tcl wrapper for the integer validation function
        self.integer_validation = self.register(is_integer)
        self.label1 = tk.Label(self.canvas1, text="Current levitation:")
        self.label1.place(x=10, y=40)
        self.value1 = tk.StringVar(value='0')
        self.entry1 = tk.Entry(self.canvas1, textvariable=self.value1,
                               validate='key', validatecommand=(self.integer_validation, '%P'))
        self.entry1.place(x=120, y=40)
        self.entry1.place(x=120, y=40)

        self.label2 = tk.Label(self.canvas1, text="Current direction:")
        self.label2.place(x=10, y=70)
        self.value2 = tk.StringVar(value='0')
        self.entry2 = tk.Entry(self.canvas1, textvariable=self.value2,
                               validate='key', validatecommand=(self.integer_validation, '%P'))
        self.entry2.place(x=120, y=70)

        self.confirm_button = tk.Button(self.canvas1, text="Confirm", command=self.confirm)
        self.confirm_button.place(x=250, y=40, width=50, height=50)

        self.value3 = tk.StringVar()
        self.label3 = tk.Label(self.canvas1, textvariable=self.value3, justify='left')
        self.label3.place(x=10, y=100)

        # Add front sight
        sight_radius = 10
        self.canvas2 = tk.Canvas(self, bg='#000000', highlightthickness=0)
        self.canvas2.place(relx=.5, rely=.5,
                           width=sight_radius * 2, height=sight_radius * 2, anchor='center')
        self.canvas2.create_line(0, sight_radius, sight_radius * 2, sight_radius, fill='red', dash=(3, 5))
        self.canvas2.create_line(sight_radius, 0, sight_radius, sight_radius * 2, fill='red', dash=(3, 5))

        self.canvas_arty_location = tk.Canvas(self, bg='#000000', highlightthickness=0)
        self.canvas_arty_location.create_oval(0, 0, 22, 22, outline="#f11", fill="#1f1", width=2)
        # Add arty levitation
        self.canvas3 = tk.Canvas(self, bg='#000000', width=200, height=105, highlightthickness=0)
        self.value4 = tk.StringVar()
        self.label4 = tk.Label(self.canvas3, textvariable=self.value4, justify='left')
        self.label4.place(x=10, y=10)
        self.history_levi = []

        # Add arty location setter
        self.canvas4 = tk.Canvas(self, width=200, height=140, highlightthickness=1)
        self.label5 = tk.Label(self.canvas4, text="Select Map & Arty", justify='left')
        self.label5.place(x=10, y=10)
        # Add the dropdown for selecting the map
        self.map_var = tk.StringVar()
        sorted_map_names = sorted(map_data["mapData"][i]["name"] for i in range(len(map_data["mapData"])))
        self.map_dropdown = tk.OptionMenu(self.canvas4, self.map_var, *sorted_map_names)
        self.map_dropdown.place(x=10, y=30, width=180)

        # Dropdown for selecting the artillery based on the selected map
        self.arty_var = tk.StringVar()
        self.arty_dropdown = tk.OptionMenu(self.canvas4, self.arty_var, '')
        self.arty_dropdown.place(x=10, y=70, width=180)
        self.arty_dropdown.configure(state="disabled")  # Initially disabled

        self.map_var.trace('w', self.update_arty_options)
        self.arty_var.trace('w', self.update_confirm_status)

        self.confirm_button = tk.Button(self.canvas4, text="Confirm", command=self.confirm_selection, state="disabled")
        self.confirm_button.place(x=11, y=110, width=178, height=30)

        # Window visibility control
        self.is_visible = False
        self.is_visible_levi = False
        self.is_visible_arti_select = False
        self.hide()

        self.add_hotkeys()

    # Update artillery options when a map is selected
    def update_arty_options(self, *args):
        selected_map = self.map_var.get()
        self.arty_dropdown.configure(state="disabled")  # Disable when map changes
        self.arty_var.set('')
        for map_item in map_data["mapData"]:
            if map_item["name"] == selected_map:
                artillery_names = [arty['name'] for arty in map_item['artillery']]
                self.arty_dropdown['menu'].delete(0, 'end')
                for arty in artillery_names:
                    self.arty_dropdown['menu'].add_command(label=arty, command=tk._setit(self.arty_var, arty))
                if artillery_names:
                    self.arty_dropdown.configure(state="normal")
                break

        self.confirm_button.configure(state="disabled")  # Keep confirm disabled until artillery is selected

    # Enable confirm button only if both map and artillery are selected
    def update_confirm_status(self, *args):
        if self.map_var.get() and self.arty_var.get():
            self.confirm_button.configure(state="normal")
        else:
            self.confirm_button.configure(state="disabled")

    # Confirm button to print selected map, artillery, and vector2
    def confirm_selection(self):
        selected_map = self.map_var.get()
        selected_arty = self.arty_var.get()
        for map_item in map_data["mapData"]:
            if map_item["name"] == selected_map:
                for arty in map_item["artillery"]:
                    if arty["name"] == selected_arty:
                        print(f"Selected Map: {selected_map}, "
                              f"Selected Artillery: {selected_arty}, "
                              f"Vector2: {arty['vector2']}")
                        scaled = [0.88 * x for x in arty['vector2']]
                        self.arty = Arty((MAP_SOUTH_EAST[0] + scaled[0], MAP_SOUTH_EAST[1] - scaled[1]))
                        self.canvas_arty_location.place(x=self.arty.location[0], y=self.arty.location[1],
                                                        width=48, height=48, anchor='center')

                        switch_focus_to("Hell Let Loose  ")
                        self.after(2500, self.hide_arti)

                        break

    def toggle_build_assist(self):
        if self.tickbox_var.get():
            BuildAssist.hook()
        else:
            BuildAssist.unhook()

    def record_number(self, key: keyboard.KeyboardEvent):
        if key.name.isdigit():
            self.number_buffer.pop(0)
            self.number_buffer.append(int(key.name))

    def calculate_levitation_from_keyboard(self):
        distance = sum(self.number_buffer[idx] * 10 ** (3 - idx) for idx in range(4))
        levitation = int(round(-0.237 * distance + 1001.7))
        levi_str = f"Distance {str(distance):>6} - Levitation {str(levitation):>6}"
        self.history_levi.append(levi_str)
        if len(self.history_levi) > 5:
            self.history_levi.pop(0)
        print(levi_str)
        speak(f"{' '.join(str(levitation))}", rate=300)
        self.value4.set('\n'.join(self.history_levi))

    def switch_visibility(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def hide(self):
        self.canvas1.place_forget()
        self.is_visible = False

    def show(self):
        self.canvas1.place(x=self.winfo_screenwidth() - 10, y=10, anchor='ne')
        self.is_visible = True

    def switch_visibility_levi(self):
        if self.is_visible_levi:
            self.hide_levi()
        else:
            self.show_levi()

    def hide_levi(self):
        self.canvas3.place_forget()
        self.is_visible_levi = False

    def show_levi(self):
        self.canvas3.place(x=10, y=10, anchor='nw')
        self.is_visible_levi = True

    def switch_visibility_arti(self):
        if self.is_visible_arti_select:
            self.hide_arti()
        else:
            self.show_arti()

    def hide_arti(self):
        self.canvas4.place_forget()
        self.canvas_arty_location.place_forget()
        self.is_visible_arti_select = False

    def show_arti(self):
        self.canvas4.place(relx=.5, rely=.1, anchor='center')
        if self.arty is not None:
            self.canvas_arty_location.place(x=self.arty.location[0], y=self.arty.location[1],
                                            width=48, height=48, anchor='center')
        self.is_visible_arti_select = True

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

        keyboard.add_hotkey('CTRL+C', self.switch_visibility)
        keyboard.add_hotkey('CTRL+SHIFT+X', self.update_arty)
        keyboard.add_hotkey('CTRL+X', self.update_target)
        keyboard.add_hotkey('SHIFT+X', self.switch_visibility_arti)
        keyboard.add_hotkey('CTRL+SPACE', self.confirm)
        keyboard.add_hotkey('CAPSLOCK', self.calculate_levitation_from_keyboard)
        keyboard.add_hotkey('SHIFT+CAPSLOCK', self.switch_visibility_levi)
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

        self.canvas1.configure(height=260)
        self.value3.set(self.value3.get() + get_aim_string(self.arty))
        self.entry1.config(state='readonly')
        self.entry2.config(state='readonly')

        duration = int(self.arty.aim_target_threaded() * 1000)
        if duration > 0:
            self.after(duration + 500, self.hide)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the application with optional debug mode.")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode")
    args = parser.parse_args()

    multiprocessing.freeze_support()
    init_audio()
    print("""
    Instruction:
    1. Press 'CTRL+V' to toggle the visibility of the application window.

    2. Press 'CTRL+X' to set the target position based on the cursor's current location, press 'CTRL+SPACE' to confirm.

    3. Press 'CTRL+SHIFT+X' to set the artillery position based on the cursor's current location.

    4. Press 'SHIFT+X' to toggle the visibility of the Map & Artillery select window.

    5. Press 'CTRL+SPACE' to confirm the OCR results and start aiming.

    6. Press 'CAPSLOCK' after entering a four-digit number to calculate and announce the levitation for the artillery.

    7. Press 'SHIFT+CAPSLOCK' to toggle the visibility of the artillery levitation window.

    8. Press 'CTRL+Q' to force quit the application.

    9. Press 'DELETE' to cancel any ongoing shooting action.

    10. Press 'SHIFT+<number>' to initiate the reloading and shooting action <number> times.

    11. Press 'GRAVE+ESC' to perform a redeploy action in the game.

    12. Press 'CTRL+SHIFT+DELETE' to quit both HLL game process and this app.

    13. Build Assist: 'Right click' / Press 'C' to start auto-build; 'Middle click' / Press 'V' to interrupt

    """)
    if not args.debug:
        if not check_process_exists("leigod.exe"):
            subprocess.Popen(r"D:\Program Files (x86)\LeiGod_Acc\leigod.exe")
        if not check_process_exists("HLL-Win64-Shipping.exe"):
            subprocess.run(['start', 'steam://rungameid/686810'], shell=True)

    main_app = AutoArtyApp()
    magnifier_app = MagnifierApp()
    tk.mainloop()
    terminate_audio()
