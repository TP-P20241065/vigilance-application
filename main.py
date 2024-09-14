#!/usr/bin/python3
import datetime
import os
import tkinter as tk
from tkinter import messagebox
import requests
from dotenv import load_dotenv
from ZuriCamui import login_windowUI
from email_verification import is_valid_email
from vigilance import vigilance
import jwt
import torch

# Cargar las variables de entorno del archivo .env
load_dotenv()


class login_window(login_windowUI):
    def __init__(self, master=None):
        if master is None:
            master = tk.Tk()
        super().__init__(master)
        self.master = master

    def callback(self, event=None):
        # Obtener los objetos de entrada de texto
        email_input = self.builder.get_object('email_input')
        password_input = self.builder.get_object('password_input')

        # Obtener los valores ingresados
        email = email_input.get()
        password = password_input.get()

        if is_valid_email(email) and password != "" and len(password) > 6:
            # Desactivar campos y botón
            email_input.configure(state='disabled')
            password_input.configure(state='disabled')
            self.builder.get_object('login_button').configure(state='disabled')
            try:
                # Realizar la solicitud POST para obtener el token
                response = requests.post(
                    os.getenv("DATA_URL_TOKEN"),
                    json={
                        'email': email,
                        'password': password
                    },
                    headers={
                        'Content-Type': 'application/json'
                    }
                )
                response.raise_for_status()
                token_data = response.json()
                access_token = token_data.get('access_token')
                print("access token")
                print(access_token)

                user_data = jwt.decode(access_token, options={"verify_signature": False})
                print("User data")
                print(user_data)
                if 4 not in user_data.get('permissions', []):
                    email_input.configure(state='enabled')
                    password_input.configure(state='enabled')
                    self.builder.get_object('login_button').configure(state='enabled')
                    messagebox.showerror("Acceso Denegado", "No tienes permiso para el acceso a la vigilancia.")
                    return

                # Cerrar la ventana actual
                self.master.destroy()

                #Llamar a la función vigilance
                vigilance()

            except requests.exceptions.RequestException as e:
                email_input.configure(state='enabled')
                password_input.configure(state='enabled')
                self.builder.get_object('login_button').configure(state='enabled')
                messagebox.showerror("Error", f"Error en la solicitud: {e}")
            except ValueError as e:
                email_input.configure(state='enabled')
                password_input.configure(state='enabled')
                self.builder.get_object('login_button').configure(state='enabled')
                messagebox.showerror("Error", f"Error en la autenticación: {e}")
        else:
            errorMesssage = ""
            if not is_valid_email(email):
                errorMesssage += "- Correo inválido"
            if password == "" or len(password) <= 6:
                errorMesssage += "\n- Contraseña inválida (Debe tener más de 6 caracteres)"
            messagebox.showerror("Error", errorMesssage)


if __name__ == "__main__":
    #vigilance()
    app = login_window()
    app.run()
