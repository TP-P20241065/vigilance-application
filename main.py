#!/usr/bin/python3
import tkinter as tk
from tkinter import messagebox
import requests
from endpoints import login
from ZuriCamui import login_windowUI
from email_verification import is_valid_email

def lazy_get_all_cameras():
    from endpoints import get_all_cameras  # Importación diferida
    return get_all_cameras()


def lazy_vigilance(access_token, cameras, units, time, master):
    from vigilance import vigilance  # Importación diferida
    vigilance(access_token, cameras, units, time, master)



class login_window(login_windowUI):
    def __init__(self, master=None):
        if master is None:
            master = tk.Tk()
        super().__init__(master)
        self.master = master

    def callback(self, event=None):
        self.disable_interactions()

        # Obtener los valores ingresados
        email = self.builder.get_object('email_input').get()
        password = self.builder.get_object('password_input').get()

        if is_valid_email(email) and password != "" and len(password) > 6:
            # Realizar la solicitud POST para obtener el token
            try:
                response = login(email, password)
                response.raise_for_status()
                token_data = response.json()
                access_token = token_data.get('access_token')

                # Realizar la solicitud de cámaras
                data = lazy_get_all_cameras()

                # Extraer la lista de cámaras del campo `result` si existe
                cameras = data.get('result', [])

                # Filtrar y obtener los unitid de cámaras sin ubicación en tiempo real
                units = list({camera['unitId'] for camera in cameras if camera.get('location') != 'No tiene ubicación en tiempo real'})

                # Verificar si units está vacío
                if not units:
                    self.enable_interactions()
                    messagebox.showerror("Error",
                    "Necesita al menos 1 unidad de transporte indexada con al menos 1 cámara de seguridad con ubicación en tiempo real.")
                else:
                    time = self.validated_time if self.validated_time != 0 else "0"
                    #self.master.destroy()
                    lazy_vigilance(access_token, cameras, units, time, self.master)


            except requests.exceptions.HTTPError as e:
                self.enable_interactions()
                if response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get("detail", "Error desconocido")
                    messagebox.showerror("Error", error_message)
                else:
                    messagebox.showerror("Error", "Error de servidor, por favor intenta más tarde.")
            except requests.exceptions.RequestException as e:
                self.enable_interactions()
                messagebox.showerror("Error", "Hubo un error al intentar conectar al servidor.")

        else:
            self.enable_interactions()
            error_messsage = ""
            if not is_valid_email(email):
                error_messsage += "- Correo inválido"
            if password == "" or len(password) <= 6:
                error_messsage += "\n- Contraseña inválida (Debe tener más de 6 caracteres)"
            messagebox.showerror("Error", error_messsage)


if __name__ == "__main__":
    app = login_window()
    app.run()
