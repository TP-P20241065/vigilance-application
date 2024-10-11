if exist "dist" rd /q /s "dist"
pyinstaller --noconsole --hiddenimport=requests --hiddenimport=opencv-python --collect-data=ultralytics main.py
copy "alert.wav" "dist/main/_internal"
copy "best_V2.pt" "dist/main"
copy "metropolitano-lima-bus-41.jpg" "dist/main/_internal"
copy "ZuriCam.ui" "dist/main/_internal"
rename "dist\main\main.exe" "ZuriCam.exe"