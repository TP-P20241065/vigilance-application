#!/usr/bin/python3
import os
import tkinter as tk
from tkinter import messagebox
import requests
import subprocess
from cryptography.fernet import Fernet
from dotenv import load_dotenv

from ZuriCamui import login_windowUI
from email_verification import is_valid_email

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

        email = "user11@example.com"
        password = "password"

        # Obtener los valores ingresados
        #email = email_input.get()
        #password = password_input.get()

        if is_valid_email(email) and password != "" and len(password) > 6:
            # Desactivar campos y botón
            email_input.configure(state='disabled')
            password_input.configure(state='disabled')
            self.builder.get_object('login_button').configure(state='disabled')
            try:
                # Realizar la solicitud POST para obtener el token
                response = requests.post(
                    os.getenv("DATA_URL_TOKEN"),
                    data={'username': email, 'password': password}
                )
                response.raise_for_status()

                token_data = response.json()
                access_token = token_data.get('access_token')

                # Realizar la solicitud GET usando el token
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'accept': 'application/json'
                }

                user_response = requests.get(
                    os.getenv("DATA_URL_ME"),
                    headers=headers
                )
                user_response.raise_for_status()

                user_data = user_response.json()
                if 1 not in user_data.get('Permissions', []):
                    email_input.configure(state='enabled')
                    password_input.configure(state='enabled')
                    self.builder.get_object('login_button').configure(state='enabled')
                    messagebox.showerror("Acceso Denegado", "No tienes permiso para el acceso a la vigilancia.")
                    return

                # Cifrar el token
                key = Fernet.generate_key()
                cipher_suite = Fernet(key)
                encrypted_token = cipher_suite.encrypt(access_token.encode())

                # Guardar el token cifrado y la clave en archivos temporales
                with open('encrypted_token.txt', 'wb') as f:
                    f.write(encrypted_token)
                with open('key.txt', 'wb') as f:
                    f.write(key)

                # Ejecutar vigilance.py y cerrar la ventana
                subprocess.Popen(['python', 'vigilance.py'])

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
    app = login_window()
    app.run()
