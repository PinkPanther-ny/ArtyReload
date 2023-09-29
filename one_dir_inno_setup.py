import os
os.system('rmdir /s /q '
          '.\\dist\\Auto-Arty\\_internal\\tcl\\http1.0 '
          '.\\dist\\Auto-Arty\\_internal\\tcl\\opt0.4 '
          '.\\dist\\Auto-Arty\\_internal\\tcl\\tzdata'
          )

os.system("ISCC Auto-Arty_onedir.iss")
os.system("dist\\Auto-Arty_setup_onedir.exe")