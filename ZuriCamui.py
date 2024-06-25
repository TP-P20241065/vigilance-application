#!/usr/bin/python3
import pathlib
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pygubu
from email_verification import is_valid_email

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ZuriCam.ui"  # Usar el archivo actualizado
RESOURCE_PATHS = [PROJECT_PATH]


class login_windowUI:
    def __init__(self, master=None):
        self.master = master
        # Set the title of the window
        self.master.title("ZuriCam")
        self.builder = pygubu.Builder()
        self.builder.add_resource_paths(RESOURCE_PATHS)
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

    def load_background_image(self):
        self.bg_image = Image.open(PROJECT_PATH / "metropolitano-lima-bus-41.jpg")
        self.bg_image = ImageTk.PhotoImage(self.bg_image)

        # Create an image on the canvas
        self.mainwindow.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        # Center positions for text and widgets
        canvas_center_x = 320
        label_x = canvas_center_x - 100  # Position labels to the left
        input_x = canvas_center_x  # Center input fields

        # Add text to the canvas
        self.mainwindow.create_text(canvas_center_x, 40, text="Aplicación de Vigilancia",
                                    font=("Helvetica", 18, "bold"), fill="black")
        self.mainwindow.create_text(label_x+53, 120, text="Correo:", font=("Helvetica", 12), fill="black", anchor=tk.E)
        self.mainwindow.create_text(label_x+85, 170, text="Contraseña:", font=("Helvetica", 12), fill="black", anchor=tk.E)

        # Center input fields and button over the image
        self.builder.get_object('email_input').place(x=input_x, y=140, anchor=tk.CENTER, width=200)
        self.builder.get_object('password_input').place(x=input_x, y=190, anchor=tk.CENTER, width=200)
        self.builder.get_object('login_button').place(x=canvas_center_x, y=240, anchor=tk.CENTER)

    def apply_styles(self):
        style = ttk.Style()

        # Create or configure styles for Entry and Button
        style.configure('Transparent.TEntry', fieldbackground='white', background='white')
        style.configure('Transparent.TButton', background='white')

        # Apply styles to specific widgets
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


if __name__ == "__main__":
    root = tk.Tk()
    app = login_windowUI(root)
    app.run()
