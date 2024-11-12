#!/usr/bin/python3
import datetime
import importlib
import logging
import os
import time
import tkinter as tk
from tkinter import Listbox, Label, Button, Toplevel, Entry, messagebox
import threading

import requests
from utilities import replace_text
from stream import capture_data, link_check, get_url
from endpoints import report_incident
from ultralytics import YOLO

# Inicialización de variables globales
detecting = False
recording = False
start_time = 0
record_duration = 5
fourcc = None
out = None
record_timer = None
img_data = None
cap = None
logging.getLogger("ultralytics").setLevel(logging.WARNING)
camera_instance = 0
last_camera_instance = 0
camera_data = None
url = None
cameras = None
units = None
time_str = datetime.datetime.now()
unlimited_recording = False

def load_cv2():
    global cv2, fourcc
    if 'cv2' not in globals():
        cv2 = importlib.import_module('cv2')
        fourcc = cv2.VideoWriter_fourcc(*'XVID')

def load_pygame():
    global pygame
    if 'pygame' not in globals():
        pygame = importlib.import_module('pygame')
        pygame.mixer.init()

def load_yolo():
    global YOLO
    if 'YOLO' not in globals():
        ultralytics = importlib.import_module('ultralytics')
        YOLO = ultralytics.YOLO

def load_torch():
    if 'torch' not in globals():
        importlib.import_module('torch')

def load_pillow():
    global Image, ImageTk
    if 'Image' not in globals():
        Image = importlib.import_module('PIL.Image')
        ImageTk = importlib.import_module('PIL.ImageTk')

def change_camera(move):
    load_cv2()
    global camera_instance, last_camera_instance, camera_data, url, cap

    print("Instancia antes")
    print(camera_instance)
    camera_instance+=move
    if camera_instance >= last_camera_instance:
        camera_instance = 0
    elif camera_instance < 0:
        camera_instance = last_camera_instance -1

    print("Instancia ahora")
    print(camera_instance)
    camera_instance += move

    camera_data = capture_data(cameras, units)
    url = get_url(camera_data, camera_instance)
    cap = link_check(url)

    while not cap.isOpened():
        messagebox.showinfo("Error", "Error al cargar la cámara. Se pasa a la siguiente.")  # Indicador de éxito
        camera_instance+=move
        if camera_instance >= last_camera_instance:
            camera_instance = 0
        elif camera_instance < 0:
            camera_instance = last_camera_instance -1
        url = get_url(camera_data, camera_instance)
        cap = link_check(url)


def vigilance(access_token, extracted_cameras, extracted_units, time_set, master):
    load_pygame()
    load_yolo()
    load_cv2()

    def unlimited_recording():
        global unlimited_recording
        if record_button.cget("text") == "Grabar":
            unlimited_recording = True
        else:
            unlimited_recording = False

    global camera_instance, last_camera_instance, camera_data, url, cap, cameras, units, time_str
    if time_set != "0":
        hour, minute = map(int, time_set.split(':'))
        new_time = time_str.replace(hour=hour, minute=minute)
        time_str = new_time

    def update_time():
        global time_str
        time_str += datetime.timedelta(seconds=1)  # Incrementa la hora en 1 segundo
        update_time_label()
        root.after(1000, update_time)  # Llama a esta función nuevamente después de 1000 ms (1 segundo)

    def update_time_label():
        time_label.config(text=time_str.strftime("%H:%M:%S"))  # Actualiza el texto del Label

    cameras = extracted_cameras
    units = extracted_units

    last_camera_instance = len(cameras)

    # Configuración inicial de YOLO
    model = YOLO('best_v2.pt', verbose=False)
    target_classes = ['pistola', 'cuchillo']
    class_names = model.names
    target_class_indices = [key for key, value in class_names.items() if value in target_classes]
    camera_data = capture_data(cameras, units)
    url = get_url(camera_data, camera_instance)
    cap = link_check(url)
    # Obtener la velocidad de frames del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30  # Valor predeterminado si no se puede obtener fps
    frame_delay = int(1000 / fps)

    # Crear carpeta para almacenar videos e imágenes si no existe
    os.makedirs('Videos', exist_ok=True)
    os.makedirs('Imágenes', exist_ok=True)

    # Función para listar imágenes
    def list_images():
        images = [f for f in os.listdir('Imágenes') if f.endswith('.jpg')]
        listbox.delete(0, tk.END)
        for image in images:
            listbox.insert(tk.END, image)

    # Estado de video
    stop_video = False

    # Función para manejar la selección de video
    def on_video_select(event):
        global stop_video
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            image_path = os.path.join('Imágenes', event.widget.get(index))
            video_path = image_path[:-3] + "avi"
            video_path = video_path.replace("Imágenes", "Videos")

            def anular():
                os.remove(image_path)
                os.remove(video_path)
                list_images()
                hide_buttons()

            def reportar():
                hide_buttons()
                open_report_window()

            # Mostrar imagen
            show_image(image_path)
            global img_data
            img_data = image_path

            anular_button.config(command=anular)
            reportar_button.config(command=reportar)

            show_buttons()

    def show_image(image_path):
        load_pillow()
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
            global img_data

            # Obtener solo el nombre del archivo (sin ruta y formato)
            file_name = os.path.splitext(os.path.basename(str(img_data)))[0]
            file_name = file_name[:-2]
            # Obtener tracking_url a partir de file_name
            tracking_link = file_name

            # Obtener tracking_link y limpiar caracteres antes de "http"
            tracking_link = tracking_link[tracking_link.find("http"):].strip()

            # Limpiar tracking_url eliminando todos los caracteres a partir del primer espacio
            tracking_link = tracking_link.split(' ')[0]

            # Reemplazo de texto en tracking_link
            tracking_link = replace_text(tracking_link, swapped=True)

            # Obtener unit_id a partir de file_name y eliminar caracteres hasta el último espacio
            unit_id = file_name.rsplit(' ', 1)[-1]

            try:
                # Envía la solicitud POST
                response = report_incident("DENTRO DEL BUS", str(input_report.get()).upper(), tracking_link,
                                           unit_id,
                                           img_data)
                response.raise_for_status()
                report_window.destroy()
                os.remove(str(img_data))
                list_images()
                messagebox.showinfo("Éxito", "Incidencia reportada")  # Indicador de éxito


            except requests.exceptions.HTTPError as e:
                if response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get("detail", "Error desconocido")
                    messagebox.showerror("Error", error_message)
                else:
                    messagebox.showerror("Error", "Error de servidor, por favor intenta más tarde.")

            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", "Hubo un error al intentar conectar al servidor.")

        # Función para actualizar el botón "Enviar reporte"
        def update_send_button_state(*args):
            # Habilita o deshabilita el botón según el contenido de input_report
            send_button.config(state=tk.NORMAL if input_report.get() else tk.DISABLED)

        # Función para convertir el texto a mayúsculas y restringir caracteres
        def validate_input(event):
            text = input_report.get().upper()
            # Filtrar caracteres permitidos (letras, números, espacios y acentos)
            filtered_text = ''.join([c for c in text if c.isalnum() or c.isspace() or c in "ÁÉÍÓÚáéíóú"])
            input_report.delete(0, tk.END)
            input_report.insert(0, filtered_text)

        # Asociar la actualización del botón con cualquier cambio en input_report
        input_report.bind("<KeyRelease>", lambda e: validate_input)
        input_report.bind("<KeyRelease>", lambda e: update_send_button_state())

        # Crear el botón "Enviar reporte" inicialmente deshabilitado
        send_button = Button(report_window, text="Enviar reporte", state=tk.DISABLED, command=send_report)
        send_button.pack(pady=10)

        update_send_button_state()  # Llama a la función al inicio para establecer el estado inicial del botón

    master.destroy()
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

    previous_camera_button = Button(root, text="Cámara anterior",
                                    command=lambda: change_camera(-1) and stop_recording())
    previous_camera_button.pack(side=tk.LEFT, pady=10)

    next_camera_button = Button(root, text="Siguiente cámara",
                                command=lambda: change_camera(1) and stop_recording())
    next_camera_button.pack(side=tk.LEFT, pady=10)

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
    detection_window.geometry("855x480")

    # Frame y label para mostrar el video en tiempo real en la ventana separada
    video_frame = tk.Frame(detection_window)
    video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    video_label = Label(video_frame)
    video_label.pack(fill=tk.BOTH, expand=True)

    # Después de crear el root
    time_label = Label(root, text=time_str.strftime("%H:%M:%S"), font=("Arial", 24))
    time_label.pack(side=tk.TOP, pady=10)

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

    # Función para obtener la lista de videos existentes
    def get_existing_detection_videos():
        return [f for f in os.listdir('Videos') if f.startswith('deteccion')]

    # Función para generar un nombre de archivo único
    def generate_unique_filename(base_dir, base_name, extension, existing_files):
        counter = 0
        while True:
            filename = f"{base_name}_{counter}.{extension}"
            if filename not in existing_files:
                return os.path.join(base_dir, filename)
            counter += 1

    def start_recording():
        global out, recording, video_filename, record_timer, time_str
        try:
            existing_files = get_existing_detection_videos()
            current_time = str(time_str)
            current_time = current_time.split('.')[0]
            current_time = current_time.replace(':', '_')
            video_filename = generate_unique_filename("Videos", current_time + " " + str(
                replace_text(camera_data[camera_instance]['location'])) + " " + str(
                camera_data[camera_instance]['unitId']), "avi", existing_files)
            out = cv2.VideoWriter(video_filename, fourcc, 20.0,
                                  (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
            recording = True
            image = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)
            cv2.imwrite(f"Imágenes/" + current_time + " " + str(
                replace_text(camera_data[camera_instance]['location'])) + " " + str(
                camera_data[camera_instance]['unitId']) + "_0.jpg", image)

            record_button.config(text="Detener")
            reset_record_timer()
        except Exception:
            messagebox.showinfo("Error", "Error al intentar grabar.")  # Indicador de éxito


    def stop_recording():
        global out, recording, record_timer, unlimited_recording
        if not unlimited_recording:
            if out:
                out.release()
                out = None

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
        unlimited_recording()
        load_cv2()
        if recording:
            stop_recording()
        else:
            start_recording()

    # Ejecutar la detección en segundo plano
    def process_video():
        load_cv2()
        load_pillow()
        global detecting, start_time, recording

        # Intervalo de detección en segundos
        detection_interval = 0.5
        last_detection_time = time.time()  # Tiempo de la última detección

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Comprueba si ha pasado el intervalo de detección
            current_time = time.time()
            if current_time - last_detection_time >= detection_interval:
                last_detection_time = current_time  # Actualiza el tiempo de detección

                # Procesa el cuadro actual para detectar objetos
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
                        pygame.mixer.music.load('alert.wav')
                        pygame.mixer.music.play(-1)
                        start_recording()
                    else:
                        start_time = time.time()
                        reset_record_timer()

                if detecting:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > record_duration:
                        detecting = False
                        list_images()
                        pygame.mixer.music.stop()

            if recording and out:
                out.write(frame)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = ImageTk.PhotoImage(Image.fromarray(frame))
            video_label.config(image=frame_image)
            video_label.image = frame_image

            detection_window.update_idletasks()
            detection_window.update()

            if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


    # Iniciar la captura y detección de video en segundo plano
    thread = threading.Thread(target=process_video)
    thread.daemon = True
    thread.start()

    # Iniciar el hilo para actualizar la hora
    time_thread = threading.Thread(target=update_time)
    time_thread.daemon = True
    time_thread.start()


    # Iniciar el bucle principal de Tkinter
    root.mainloop()