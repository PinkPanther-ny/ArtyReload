import keyboard
import mouse
import pyautogui
import time
import threading

pyautogui.FAILSAFE = False


class BuildAssist:
    # Using a class dictionary to keep the toggle state for multiple keys
    key_pressed = {'r': False, 'f': False}
    # Timer threads for pressing keys continuously
    press_threads = {'r': None, 'f': None}

    @staticmethod
    def switch_hold():
        pyautogui.mouseUp()
        pyautogui.mouseDown()

    @staticmethod
    def press_key(key):
        while BuildAssist.key_pressed[key]:
            pyautogui.press(key)
            time.sleep(0.05)  # sleep for 100ms to press the key approximately 10 times per second

    @staticmethod
    def toggle_key_press(key):
        BuildAssist.key_pressed[key] = not BuildAssist.key_pressed[key]
        if BuildAssist.key_pressed[key]:
            # Start the thread if the key needs to be pressed
            BuildAssist.press_threads[key] = threading.Thread(target=BuildAssist.press_key, args=(key,))
            BuildAssist.press_threads[key].start()
        elif BuildAssist.press_threads[key] is not None:
            # Stop the thread if the key should not be pressed anymore
            BuildAssist.press_threads[key] = None

    @staticmethod
    def hook():
        mouse.on_right_click(BuildAssist.switch_hold)
        mouse.on_middle_click(lambda: pyautogui.mouseUp())

        keyboard.add_hotkey('C', BuildAssist.switch_hold)
        keyboard.add_hotkey('V', lambda: pyautogui.mouseUp())

        # Adding the new hotkeys for CAPS+R and CAPS+F
        keyboard.add_hotkey('RIGHT SHIFT+R', lambda: BuildAssist.toggle_key_press('r'))
        keyboard.add_hotkey('RIGHT SHIFT+F', lambda: BuildAssist.toggle_key_press('f'))

    @staticmethod
    def unhook():
        mouse.unhook_all()
        keyboard.remove_hotkey('C')
        keyboard.remove_hotkey('V')
        keyboard.remove_hotkey('RIGHT SHIFT+R')
        keyboard.remove_hotkey('RIGHT SHIFT+F')

        # Ensure all keys are released if we are unhooking
        for key in BuildAssist.key_pressed:
            if BuildAssist.press_threads[key] is not None:
                BuildAssist.key_pressed[key] = False
                BuildAssist.press_threads[key].join()


# Example usage
if __name__ == "__main__":
    BuildAssist.hook()
    print(
        "BuildAssist is running. Press CAPSLOCK+R or CAPSLOCK+F to toggle key presses. Press C to hold the mouse "
        "button, V to release it.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        BuildAssist.unhook()
        print("BuildAssist stopped.")
