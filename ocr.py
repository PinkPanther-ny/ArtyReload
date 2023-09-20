import pyscreenshot as ImageGrab
import pytesseract


class AngleDetector:
    def __init__(self):
        self._current_angle = -1
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

    def get_angle(self):
        im = ImageGrab.grab(bbox=(950, 1030, 970, 1045))
        width, height = im.size
        im = im.resize((width * 5, height * 5))
        result = pytesseract.image_to_string(im, config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789')

        if result != '' and 0 <= int(result) <= 360:
            self._current_angle = int(result)
        else:
            self._current_angle = -1
        return self._current_angle
