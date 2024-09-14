import datetime
import cv2
import os
import time
import tkinter as tk
from tkinter import Listbox, Label, Button, Toplevel, Entry, messagebox
import threading
from PIL import Image, ImageTk, ImageGrab
import pygame
import requests
from dotenv import load_dotenv
from ultralytics import YOLO

# Inicialización de variables globales
detecting = False
recording = False
start_time = 0
record_duration = 5
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = None
record_timer = None


def vigilance():
    # Cargar las variables de entorno del archivo .env
    load_dotenv()

    # Inicializar pygame mixer
    pygame.mixer.init()

    # Configuración inicial de YOLO
    model = YOLO('best_v2.pt')
    target_classes = ['pistola', 'cuchillo']
    class_names = model.names
    target_class_indices = [key for key, value in class_names.items() if value in target_classes]
    # Captura de video desde la cámara web
    video_path = int(os.getenv("CAMERA"))
    error_path = "nodisponible.mp4"
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap = cv2.VideoCapture(error_path)
        #messagebox.showerror("Error", "Error al abrir la cámara")
        print("Error al abrir la cámara 1")

    # Obtener la velocidad de frames del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30  # Valor predeterminado si no se puede obtener fps
    frame_delay = int(1000 / fps)

    # Crear carpeta para almacenar videos e imágenes si no existe
    os.makedirs('videos', exist_ok=True)
    os.makedirs('images', exist_ok=True)

    # Función para listar imágenes
    def list_images():
        images = [f for f in os.listdir('images') if f.endswith('.png')]
        listbox.delete(0, tk.END)
        for image in images:
            listbox.insert(tk.END, image)

    # Variables para mantener el estado del video actual
    current_video_cap = None
    stop_video = False

    # Función para manejar la selección de video
    def on_video_select(event):
        global stop_video
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            image_path = os.path.join('images', event.widget.get(index))

            def anular():
                os.remove(image_path)
                list_images()
                hide_buttons()

            def reportar():
                hide_buttons()
                open_report_window()

            # Mostrar imagen
            show_image(image_path)

            anular_button.config(command=anular)
            reportar_button.config(command=reportar)

            show_buttons()

    def show_image(image_path):
        image = Image.open(image_path)
        image.thumbnail((300, 300))  # Ajusta el tamaño de la imagen si es necesario
        image_tk = ImageTk.PhotoImage(image)
        image_label.config(image=image_tk)
        image_label.image = image_tk

    def show_buttons():
        anular_button.pack(side=tk.LEFT, padx=10, pady=10)
        reportar_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def hide_buttons():
        anular_button.pack_forget()
        reportar_button.pack_forget()

    def open_report_window():
        report_window = Toplevel(root)
        report_window.title("Reporte de incidencia")
        report_window.geometry("400x300")

        Label(report_window, text="Ingrese el reporte:").pack(pady=10)
        input_report = Entry(report_window, width=50)
        input_report.pack(pady=10)

        def send_report():
            time = str(datetime.datetime.now())
            time = time.split('.')[0]
            data = {
                "address": "Dentro del bus",
                "incident": str(input_report),
                "trackingLink": "https://maps.app.goo.gl/PsJQiVvKxLcFXiEM9",
                "image": "Imagen",
                "unitId": int(os.getenv("UNIT_ID"))
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(
                os.getenv("DATA_URL_REPORT"),
                headers=headers,
                json=data
            )
            response.raise_for_status()
            report_window.destroy()

        Button(report_window, text="Enviar reporte", command=send_report).pack(pady=10)

    # Crear ventana principal de Tkinter
    root = tk.Tk()
    root.title("Lista de imágenes")
    root.geometry("800x600")

    listbox = Listbox(root)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    listbox.bind('<<ListboxSelect>>', on_video_select)

    refresh_button = Button(root, text="Actualizar", command=list_images)
    refresh_button.pack(side=tk.LEFT, pady=10)

    record_button = Button(root, text="Grabar", command=lambda: toggle_recording())
    record_button.pack(side=tk.LEFT, pady=10)

    # Frame para mostrar la imagen seleccionada
    image_frame = tk.Frame(root)
    image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Label para mostrar la imagen
    image_label = Label(image_frame)
    image_label.pack(fill=tk.BOTH, expand=True)

    # Frame para botones
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Botones para anular y reportar
    anular_button = Button(button_frame, text="Anular")
    reportar_button = Button(button_frame, text="Reportar")

    # Ocultar botones al inicio
    hide_buttons()

    # Actualizar lista de imágenes al inicio
    list_images()

    # Crear ventana separada para detección en tiempo real
    detection_window = tk.Toplevel(root)
    detection_window.title("Detección en tiempo real")
    detection_window.geometry("1280x960")

    # Frame y label para mostrar el video en tiempo real en la ventana separada
    video_frame = tk.Frame(detection_window)
    video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    video_label = Label(video_frame)
    video_label.pack(fill=tk.BOTH, expand=True)

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

    # Función para obtener la lista de imágenes existentes
    def get_existing_detection_images():
        return [f for f in os.listdir('images') if f.endswith('.png')]

    # Función para generar un nombre de archivo único
    def generate_unique_filename(base_dir, base_name, extension, existing_files):
        counter = 0
        while True:
            filename = f"{base_name}_{counter}.{extension}"
            if filename not in existing_files:
                return os.path.join(base_dir, filename)
            counter += 1

    def save_screenshot(filename):
        # Obtener las coordenadas de la ventana de detección en tiempo real
        x = video_label.winfo_rootx()
        y = video_label.winfo_rooty()
        width = video_label.winfo_width()
        height = video_label.winfo_height()
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        screenshot.save(f"{filename}", "PNG")

    def start_recording():
        global out, video_filename, recording, record_timer
        existing_files = get_existing_detection_videos()
        time_str = str(datetime.datetime.now())
        time_str = time_str.split('.')[0]
        time_str = time_str.replace(':', '_')
        video_filename = generate_unique_filename("videos", time_str, "avi", existing_files)
        out = cv2.VideoWriter(video_filename, fourcc, 20.0,
                              (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        recording = True
        record_button.config(text="Detener")
        reset_record_timer()

    def stop_recording():
        global out, video_filename, recording, record_timer
        if out:
            out.release()
            out = None
            print(f"Video saved: {video_filename}")
        recording = False
        record_button.config(text="Grabar")
        if record_timer:
            record_timer.cancel()
            record_timer = None

    def reset_record_timer():
        global record_timer
        if record_timer:
            record_timer.cancel()
        record_timer = threading.Timer(record_duration, stop_recording)
        record_timer.start()

    # Función para alternar la grabación
    def toggle_recording():
        if recording:
            stop_recording()
        else:
            start_recording()

    # Ejecutar la detección en segundo plano
    def process_video():
        global detecting, start_time, recording

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
                    existing_files = get_existing_detection_images()
                    time_str = str(datetime.datetime.now())
                    time_str = time_str.split('.')[0]
                    time_str = time_str.replace(':', '_')
                    screenshot_filename = generate_unique_filename("images", time_str, "png", existing_files)
                    save_screenshot(screenshot_filename)

                    # Reproducir el audio en bucle
                    pygame.mixer.music.load('alert.wav')
                    pygame.mixer.music.play(-1)

                    # Iniciar grabación automática
                    start_recording()
                else:
                    start_time = time.time()
                    reset_record_timer()

            if detecting:
                elapsed_time = time.time() - start_time
                if elapsed_time > record_duration:
                    detecting = False
                    list_images()

                    # Detener el audio
                    pygame.mixer.music.stop()

            if recording and out:
                out.write(frame)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = ImageTk.PhotoImage(Image.fromarray(frame))
            video_label.config(image=frame_image)
            video_label.image = frame_image

            detection_window.update_idletasks()  # Actualizar la ventana de detección
            detection_window.update()

            if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # Iniciar la captura y detección de video en segundo plano
    thread = threading.Thread(target=process_video)
    thread.daemon = True
    thread.start()

    # Iniciar el bucle principal de Tkinter
    root.mainloop()