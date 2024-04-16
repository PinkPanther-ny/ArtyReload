import tkinter as tk

import keyboard
import pyautogui
import win32con
import win32gui
from PIL import ImageGrab
from PIL import ImageTk, Image

from util import resource_path


class MagnifierCanvas(tk.Canvas):
    def __init__(self, parent, width, height, mag_ratio):
        super().__init__(parent, bg='#000000', highlightthickness=1,
                         width=width, height=height)
        self.window_width = width
        self.window_height = height
        self.mag_ratio = mag_ratio

        # Get screen size
        screen_width, screen_height = pyautogui.size()
        # Coordinates of the center of the screen
        self.x_center_screen = screen_width // 2
        self.y_center_screen = screen_height // 2
        self.image = None
        self.is_visible = True
        self.after(100, self.magnify)

    def magnify(self):
        if keyboard.is_pressed('+') and self.mag_ratio < 5:
            self.mag_ratio += 0.1
        elif keyboard.is_pressed('-') and self.mag_ratio > 1:
            self.mag_ratio -= 0.1

        cap_width = round(self.winfo_width() / self.mag_ratio)
        cap_height = round(self.winfo_height() / self.mag_ratio)

        try:
            # Capture the screen region around the center
            screenshot = ImageGrab.grab(
                bbox=(self.x_center_screen - cap_width // 2, self.y_center_screen - cap_height // 2,
                      self.x_center_screen + cap_width // 2, self.y_center_screen + cap_height // 2)
            )
        except OSError:
            self.after(5, self.magnify)
            return

        # Resize the screenshot to simulate magnification
        screenshot = screenshot.resize((self.winfo_width(), self.winfo_height()))

        # Convert the screenshot to a format Tkinter can use
        # Keep the reference to avoid garbage collection
        self.image = ImageTk.PhotoImage(screenshot)

        # Remove the old magnified image if it exists
        self.delete("magnified")

        # Place the new magnified image on the canvas
        self.create_image(self.winfo_width() // 2, self.winfo_height() // 2,
                          image=self.image, tags="magnified")

        self.after(5, self.magnify)

    def hide(self):
        self.pack_forget()
        self.is_visible = False

    def show(self):
        self.pack()
        self.is_visible = True

    def switch_visibility(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()


class MagnifierApp(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#000000")
        self.wm_attributes('-fullscreen', 'True')
        self.wm_attributes("-alpha", 1)
        self.config(bg='#000000')
        self.title("MagnifierApp")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        ico = ImageTk.PhotoImage(Image.open(resource_path('images/arty.ico')))
        self.iconphoto(False, ico)  # noqa

        self.canvas_mag = MagnifierCanvas(parent=self, width=230 * 2, height=230, mag_ratio=2)
        self.canvas_mag.pack()
        self.canvas_mag.hide()
        self.after(100, self.make_click_through)
        keyboard.add_hotkey('CTRL+V', lambda: self.canvas_mag.switch_visibility())

    @staticmethod
    def make_click_through():
        hwnd = win32gui.FindWindow(None, "MagnifierApp")
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                               | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
