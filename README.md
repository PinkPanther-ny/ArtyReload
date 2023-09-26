# AutoArtyApp

## Overview
AutoArtyApp is a Python-based application designed to automate artillery shooting in a Hell-Let-Loose. It utilizes OCR to read game screen values and simulates keypresses to control the artillery.

## Requirements
- Python 3.x
- tkinter
- pyautogui
- PIL
- pytesseract
- pyttsx3
- other required packages specified in `requirements.txt`

## Installation
1. Clone this repository.
2. Navigate to the directory and install the required Python packages by running `pip install -r requirements.txt`.

## How to Use

### General Instructions
The program simulates artillery shooting and calculates direction and levitation based on distance. Currently it only works on 1920x1080 resolution, windowed-fullscreen mode.

#### Actions
1. Press `SHIFT+number` (number from 1 to 9) to initiate reloading and shooting the specified number of times.
   - For example, `SHIFT+3` will reload and shoot three times.
  
2. Press `DELETE` to cancel the shooting action in progress.
  
3. Press `CTRL+SHIFT+X` to set artillery location.
  
4. Press `CTRL+X` to update target based on current mouse position.
  
5. Input a four-digit distance and then press `CAPSLOCK` to calculate and announce the levitation.
  
6. Press `CTRL+Q` to exit the program.

### Visibility Controls
- Press `CTRL+V` to toggle the visibility of the application.
  
### Additional Hotkeys
- Press `GRAVE+ESC` to redeploy in-game.

## Contributing
To contribute to this project, please fork the repository and create a pull request.

## Author
Alvin
