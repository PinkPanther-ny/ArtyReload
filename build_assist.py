import keyboard
import mouse
import pyautogui

pyautogui.FAILSAFE = False


class BuildAssist:
    @staticmethod
    def switch_hold():
        pyautogui.mouseUp()
        pyautogui.mouseDown()

    @staticmethod
    def hook():
        mouse.on_right_click(BuildAssist.switch_hold)
        mouse.on_middle_click(lambda: pyautogui.mouseUp())

        keyboard.add_hotkey('C', BuildAssist.switch_hold)
        keyboard.add_hotkey('V', lambda: pyautogui.mouseUp())

    @staticmethod
    def unhook():
        mouse.unhook_all()
        keyboard.remove_hotkey('C')
        keyboard.remove_hotkey('V')
