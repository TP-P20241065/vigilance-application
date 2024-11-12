import pathlib
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import pygubu
from email_verification import is_valid_email

# Función para localizar archivos en modo desarrollo y en ejecutable
def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # La aplicación está congelada (ejecutable)
        datadir = os.path.dirname(sys.executable)
    else:
        # La aplicación no está congelada (modo desarrollo)
        datadir = os.path.dirname(__file__)
    return os.path.join(datadir, filename)

# Usar find_data_file para obtener la ruta de ZuriCam.ui y otros archivos
PROJECT_UI = find_data_file("ZuriCam.ui")
BACKGROUND_IMAGE = find_data_file("metropolitano-lima-bus-41.jpg")

class login_windowUI:
    def __init__(self, master=None):
        self.master = master
        self.master.title("ZuriCam")
        self.builder = pygubu.Builder()
        self.builder.add_from_file(PROJECT_UI)

        # Main widget as Canvas
        self.mainwindow: tk.Canvas = tk.Canvas(master, width=640, height=360)
        self.mainwindow.pack(fill="both", expand=True)

        # Set fixed size and prevent the window from being resizable
        self.master.geometry("640x360")
        self.master.resizable(False, False)

        # Load the background image
        self.load_background_image()

        self.builder.connect_callbacks(self)

        # Apply styles to widgets
        self.apply_styles()

        # Set default time in HH:MM format
        self.set_default_time()

        # Bind the validation method to the time input
        self.builder.get_object('time_input').bind('<KeyRelease>', self.validate_time_input)

        self.builder.get_object('validate_button').configure(state='disabled')
        self.validated_time = 0

    def enable_interactions(self):
        self.builder.get_object('email_input').configure(state='enabled')
        self.builder.get_object('password_input').configure(state='enabled')
        self.builder.get_object('login_button').configure(state='enabled')
        self.builder.get_object('time_input').configure(state='enabled')
        login_windowUI.validate_time_input(self)

    def disable_interactions(self):
        self.builder.get_object('email_input').configure(state='disabled')
        self.builder.get_object('password_input').configure(state='disabled')
        self.builder.get_object('login_button').configure(state='disabled')
        self.builder.get_object('time_input').configure(state='disabled')
        self.builder.get_object('validate_button').configure(state='disabled')

    def set_default_time(self):
        current_time = ""
        time_input = self.builder.get_object('time_input')
        time_input.insert(0, current_time)

    def load_background_image(self):
        self.bg_image = Image.open(BACKGROUND_IMAGE)
        self.bg_image = ImageTk.PhotoImage(self.bg_image)
        self.mainwindow.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        # Center positions for text and widgets
        canvas_center_x = 320
        label_x = canvas_center_x - 100  # Position labels to the left
        input_x = canvas_center_x  # Center input fields

        # Add text to the canvas
        self.mainwindow.create_text(canvas_center_x, 40, text="Aplicación de Vigilancia",
                                    font=("Helvetica", 18, "bold"), fill="black")
        self.mainwindow.create_text(label_x + 53, 120-30, text="Correo:", font=("Helvetica", 12), fill="black",
                                    anchor=tk.E)
        self.mainwindow.create_text(label_x + 85, 170-30, text="Contraseña:", font=("Helvetica", 12), fill="black",
                                    anchor=tk.E)
        self.mainwindow.create_text(canvas_center_x, 260, text="Hora actual",
                                    font=("Helvetica", 12), fill="black")

        # Center input fields and button over the image
        self.builder.get_object('email_input').place(x=input_x, y=140-30, anchor=tk.CENTER, width=200)
        self.builder.get_object('password_input').place(x=input_x, y=190-30, anchor=tk.CENTER, width=200)
        self.builder.get_object('login_button').place(x=canvas_center_x, y=240-30, anchor=tk.CENTER)

        self.builder.get_object('time_input').place(x=input_x, y=290, anchor=tk.CENTER, width=40)
        # Button for validating time
        self.builder.get_object('validate_button').place(x=canvas_center_x, y=320, anchor=tk.CENTER)

    def apply_styles(self):
        style = ttk.Style()
        style.configure('Transparent.TEntry', fieldbackground='white', background='white')
        style.configure('Transparent.TButton', background='white')
        self.builder.get_object('email_input').configure(style='Transparent.TEntry')
        self.builder.get_object('password_input').configure(style='Transparent.TEntry')
        self.builder.get_object('login_button').configure(style='Transparent.TButton')

    def run(self):
        self.master.mainloop()

    def callback(self, event=None):
        email_input = self.builder.get_object('email_input')
        password_input = self.builder.get_object('password_input')

        email = email_input.get()
        password = password_input.get()

        if is_valid_email(email):
            email_input.configure(state='disabled')
            password_input.configure(state='disabled')
            self.builder.get_object('login_button').configure(state='disabled')
        else:
            print("Invalid email")

    def validate_time_input(self, event=None):
        time_input = self.builder.get_object('time_input')
        time = time_input.get()

        # Filtrar caracteres permitidos
        filtered_time = ''.join(char for char in time if char.isdigit() or char == ':')

        # Comprobar cuántos ':' hay y eliminar el último si hay más de uno
        while filtered_time.count(':') > 1:
            last_colon_index = filtered_time.rfind(':')
            filtered_time = filtered_time[:last_colon_index] + filtered_time[last_colon_index + 1:]

        # Restringir la longitud a 5 caracteres
        if len(filtered_time) > 5:
            filtered_time = filtered_time[:5]

        # Actualizar el campo de entrada
        time_input.delete(0, tk.END)
        time_input.insert(0, filtered_time)

        # Validar el formato de la hora
        if self.is_valid_time_format(filtered_time):
            hour, minute = filtered_time.split(':')

            # Convertir a enteros y validar
            if len(hour) == 0:
                hour = "0"
            if len(minute) == 0:
                minute = "0"

            hour = int(hour)
            minute = int(minute)

            if 0 <= hour < 24 and 0 <= minute < 60:
                self.builder.get_object('validate_button').configure(state='normal')
                return

        # Deshabilitar el botón de validar si no se cumplen las condiciones
        self.builder.get_object('validate_button').configure(state='disabled')

    def is_valid_time_format(self, time):
        if len(time) < 4 or len(time) > 5:
            return False
        if time[2] != ':':
            return False
        if not time.replace(':', '').isdigit():
            return False

        hour, minute = time.split(':')

        # Validar que la hora tenga un dígito (1 o 2) y los minutos tengan exactamente 2 dígitos
        if not (1 <= len(hour) <= 2) or len(minute) != 2:
            return False

        # Convertir y validar el rango de la hora y los minutos
        if not (0 <= int(hour) < 24) or not (0 <= int(minute) < 60):
            return False

        return True

    def validate_callback(self, event=None):
        time_input = self.builder.get_object('time_input')
        time = time_input.get()
        self.validated_time = time

        messagebox.showinfo("Éxito", f"Hora validada: {time}")


if __name__ == "__main__":
    root = tk.Tk()
    app = login_windowUI(root)
    app.run()
