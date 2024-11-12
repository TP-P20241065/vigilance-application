import os
import dotenv
import requests
from dotenv import load_dotenv

load_dotenv()
def login(email, password):
    return requests.post(os.getenv('DATA_URL')
                                 + "/auth/login/portal-desktop",
        json={
            'email': email.upper(),
            'password': password
        },
        headers={
            'Content-Type': 'application/json'
        }
    )

def get_all_cameras():
    response = requests.get(os.getenv('DATA_URL')
                            + "/camera")
    return response.json() if response.status_code == 200 else {}

def report_incident(address, incident, tracking_link, unit_id, img_data):
    data = {
        "address": address,
        "incident": incident,
        "tracking_link": tracking_link,
        "unit_id": unit_id
    }
    with open(img_data, "rb") as image_file:
        file = {
            'image': image_file  # El backend lo recibe como archivo
        }
        return requests.post(os.getenv('DATA_URL')
                            + "/report/upload/",
             data=data,
             files=file
        )