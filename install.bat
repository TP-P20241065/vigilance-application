if exist "dist" rd /q /s "dist"
pyinstaller.exe main.py --add-binary "<TU RUTA>\Python\Python310\Lib\site-packages\cv2\opencv_videoio_ffmpeg480_64.dll;." --add-data=".env;." --collect-data=ultralytics
copy "alert.wav" "dist/main/_internal"
copy "best.pt" "dist/main"
copy "metropolitano-lima-bus-41.jpg" "dist/main/_internal"
copy "ZuriCam.ui" "dist/main/_internal"