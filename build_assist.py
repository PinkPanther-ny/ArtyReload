import keyboard
import mouse
import pyautogui
import time
import threading

pyautogui.FAILSAFE = False


class BuildAssist:
    # Using a class variable to keep the toggle state
    r_pressed = False
    # Timer thread for pressing 'R' continuously
    press_thread = None

    @staticmethod
    def switch_hold():
        pyautogui.mouseUp()
        pyautogui.mouseDown()

    @staticmethod
    def press_r():
        while BuildAssist.r_pressed:
            pyautogui.press('r')
            time.sleep(0.05)  # sleep for 100ms to press R approximately 10 times per second

    @staticmethod
    def toggle_r_press():
        BuildAssist.r_pressed = not BuildAssist.r_pressed
        if BuildAssist.r_pressed:
            # Start the thread if R needs to be pressed
            BuildAssist.press_thread = threading.Thread(target=BuildAssist.press_r)
            BuildAssist.press_thread.start()
        elif BuildAssist.press_thread is not None:
            # Stop the thread if R should not be pressed anymore
            BuildAssist.press_thread = None

    @staticmethod
    def hook():
        mouse.on_right_click(BuildAssist.switch_hold)
        mouse.on_middle_click(lambda: pyautogui.mouseUp())

        keyboard.add_hotkey('C', BuildAssist.switch_hold)
        keyboard.add_hotkey('V', lambda: pyautogui.mouseUp())

        # Adding the new hotkey for CAPS+R
        keyboard.add_hotkey('CAPSLOCK+R', BuildAssist.toggle_r_press)

    @staticmethod
    def unhook():
        mouse.unhook_all()
        keyboard.remove_hotkey('C')
        keyboard.remove_hotkey('V')
        keyboard.remove_hotkey('CAPSLOCK+R')

        # Ensure all keys are released if we are unhooking
        if BuildAssist.press_thread is not None:
            BuildAssist.r_pressed = False
            BuildAssist.press_thread.join()
