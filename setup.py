# setup.py
from cx_Freeze import setup, Executable
import sys

# Límite de recursión
sys.setrecursionlimit(1500)

# Verificar si es Windows para definir el tipo de base correctamente
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Configuración de la aplicación
setup(
    name="ZuriCam",
    version="1.0",
    description="Monitoreo en tiempo real",
    options={
        "build_exe": {
            "packages": [
                "numpy",
                "cv2",
                "PIL",
                "pygame",
                "pygubu",
                "dotenv",
                "requests",
                "skimage",
                "ultralytics",
                "yt_dlp"
            ],
            "include_files": ["best_v2.pt", ".env", "ZuriCam.ui", "metropolitano-lima-bus-41.jpg", "alert.wav"],
            "build_exe": "dist"
        }
    },
    executables=[Executable("main.py", base=base)]

)
