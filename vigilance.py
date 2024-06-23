import cv2
import os
import time
import tkinter as tk
from tkinter import Listbox, Label, Button, Toplevel
from ultralytics import YOLO
import threading
from PIL import Image, ImageTk
from cryptography.fernet import Fernet
import pygame  # Biblioteca para manejar el sonido

# Inicializar pygame mixer
pygame.mixer.init()

# Leer la clave desde el archivo
key_file = 'key.txt'
if os.path.exists(key_file):
    with open(key_file, 'rb') as f:
        key = f.read().strip()
    cipher_suite = Fernet(key)
    os.remove(key_file)
else:
    print("No se encontró el archivo de clave.")
    key = None

# Leer el token cifrado desde el archivo
token_file = 'encrypted_token.txt'
if os.path.exists(token_file) and key:
    with open(token_file, 'rb') as f:
        encrypted_token = f.read().strip()
    print("Token cifrado leído:", encrypted_token)

    # Descifrar el token
    access_token = cipher_suite.decrypt(encrypted_token).decode()
    print("Token descifrado:", access_token)
    os.remove(token_file)
else:
    print("No se encontró el archivo de token cifrado o la clave.")
    access_token = None

# Configuración inicial de YOLO
model = YOLO('best.pt')
target_classes = ['gun', 'knife']
class_names = model.names
target_class_indices = [key for key, value in class_names.items() if value in target_classes]

# Captura de video desde la cámara web
video_path = 3  # Usar 0 para la cámara integrada, 1 para la primera cámara USB, etc.
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error al abrir la cámara")
    exit()

# Obtener la velocidad de frames del video
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30  # Valor predeterminado si no se puede obtener fps
frame_delay = int(1000 / fps)

# Variables para grabación y detección
detecting = False
start_time = 0
record_duration = 5
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = None

# Crear carpeta para almacenar videos si no existe
os.makedirs('videos', exist_ok=True)


# Función para listar videos
def list_videos():
    videos = [f for f in os.listdir('videos') if f.startswith('deteccion')]
    listbox.delete(0, tk.END)
    for video in videos:
        listbox.insert(tk.END, video)


# Variables para mantener el estado del video actual
current_video_cap = None
current_video_thread = None
stop_video = False


# Función para reproducir video en Tkinter
def play_video(video_path):
    global current_video_cap, stop_video, current_video_thread

    if current_video_thread and current_video_thread.is_alive():
        stop_video = True
        current_video_thread.join()

    current_video_cap = cv2.VideoCapture(video_path)
    stop_video = False

    def update_frame():
        while not stop_video:
            ret, frame = current_video_cap.read()
            if not ret:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = ImageTk.PhotoImage(Image.fromarray(frame))

            video_label.config(image=frame_image)
            video_label.image = frame_image

            time.sleep(1 / fps)

    current_video_thread = threading.Thread(target=update_frame)
    current_video_thread.start()


# Función para manejar la selección de video
def on_video_select(event):
    global stop_video
    selection = event.widget.curselection()
    if selection:
        index = selection[0]
        video_path = os.path.join('videos', event.widget.get(index))

        def anular():
            os.remove(video_path)
            list_videos()
            hide_buttons()
            stop_video_playback()

        def reportar():
            hide_buttons()
            stop_video_playback()

        # Reproducir video
        play_video(video_path)

        anular_button.config(command=anular)
        reportar_button.config(command=reportar)

        show_buttons()


def show_buttons():
    anular_button.pack(side=tk.LEFT, padx=10, pady=10)
    reportar_button.pack(side=tk.RIGHT, padx=10, pady=10)


def hide_buttons():
    anular_button.pack_forget()
    reportar_button.pack_forget()


# Crear ventana principal de Tkinter
root = tk.Tk()
root.title("Lista de Videos")
root.geometry("800x600")

listbox = Listbox(root)
listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
listbox.bind('<<ListboxSelect>>', on_video_select)

refresh_button = Button(root, text="Actualizar", command=list_videos)
refresh_button.pack(side=tk.LEFT, pady=10)

# Frame para mostrar el video
video_frame = tk.Frame(root)
video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Label para mostrar el video
video_label = Label(video_frame)
video_label.pack(fill=tk.BOTH, expand=True)

# Frame para botones
button_frame = tk.Frame(root)
button_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Botones para anular y reportar
anular_button = Button(button_frame, text="Anular")
reportar_button = Button(button_frame, text="Reportar")

# Ocultar botones al inicio
hide_buttons()

# Actualizar lista de videos al inicio
list_videos()


# Función para redimensionar el video manteniendo la relación de aspecto
def resize_video_label(event):
    if hasattr(video_label, 'image') and video_label.image:
        width, height = event.width, event.height
        img_width, img_height = video_label.image.width(), video_label.image.height()

        if width / img_width < height / img_height:
            new_width = width
            new_height = int(img_height * (width / img_width))
        else:
            new_height = height
            new_width = int(img_width * (height / img_height))

        video_label.config(width=new_width, height=new_height)


video_label.bind('<Configure>', resize_video_label)


# Función para detener la reproducción del video actual
def stop_video_playback():
    global stop_video, current_video_cap
    stop_video = True
    if current_video_cap:
        current_video_cap.release()
    video_label.config(image='')


# Función para obtener la lista de videos existentes
def get_existing_detection_videos():
    return [f for f in os.listdir('videos') if f.startswith('deteccion')]


# Función para generar un nombre de archivo único
def generate_unique_filename(base_dir, base_name, extension, existing_files):
    counter = 0
    while True:
        filename = f"{base_name}_{counter}.{extension}"
        if filename not in existing_files:
            return os.path.join(base_dir, filename)
        counter += 1


# Ejecutar la detección en segundo plano
def process_video():
    global detecting, start_time, out

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Fin del video")
            break

        results = model(frame)
        detection_made = False

        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls)
                confidence = box.conf.item()

                if class_id in target_class_indices and confidence > 0.5:
                    detection_made = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = f"{class_names[class_id]}: {confidence:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        if detection_made:
            if not detecting:
                start_time = time.time()
                detecting = True
                existing_files = get_existing_detection_videos()
                video_filename = generate_unique_filename('videos', 'deteccion', 'avi', existing_files)
                out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))

                # Reproducir el audio en bucle
                pygame.mixer.music.load('alert.wav')
                pygame.mixer.music.play(-1)
            else:
                start_time = time.time()

        if detecting:
            out.write(frame)
            elapsed_time = time.time() - start_time
            if elapsed_time > record_duration:
                detecting = False
                out.release()
                out = None
                list_videos()

                # Detener el audio
                pygame.mixer.music.stop()

        cv2.imshow('Detección en tiempo real', frame)

        if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
            break

    if detecting and out is not None:
        out.release()
    cap.release()
    cv2.destroyAllWindows()


# Iniciar la captura y detección de video en segundo plano
thread = threading.Thread(target=process_video)
thread.daemon = True
thread.start()

# Iniciar el bucle principal de Tkinter
root.mainloop()
