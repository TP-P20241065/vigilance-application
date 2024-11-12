import cv2
import yt_dlp as youtube_dl

def youtube_stream(current_view):
    youtube_url = current_view

    # Configuración para seleccionar la calidad en 480p o la mejor calidad inferior disponible
    ydl_opts = {
        'format': 'best[height<=480]/best',  # 480p o la mejor calidad inferior posible
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        live_url = info['url']

    return cv2.VideoCapture(live_url)

def ip_stream(current_view):
    return cv2.VideoCapture(current_view)

def link_check(current_view):
    if current_view == '0':
        return cv2.VideoCapture(0)
    elif 'youtube.com' in current_view or 'youtu.be' in current_view:
        return youtube_stream(current_view)
    else:
        return ip_stream(current_view)

def capture_data(cameras, units):
    # Crear un nuevo arreglo para almacenar los valores filtrados
    viewing = []

    # Filtrar las cámaras según el unitId y extraer los atributos deseados
    for camera in cameras:
        if camera.get('unitId') in units:
            viewing.append({
                'name': camera.get('name'),
                'location': camera.get('location'),
                'url': camera.get('url'),
                'unitId': camera.get('unitId')
            })

    # Recorrer la lista 'viewing' para asignar el valor de 'location' si está vacío
    for i in range(len(viewing)):
        if viewing[i]['location'] == "No tiene ubicación en tiempo real":  # Verifica si no hay 'location'
            # Buscar otra cámara con el mismo unitId que tenga un location válido
            for camera in viewing:
                if camera['unitId'] == viewing[i]['unitId'] and camera['location']:
                    viewing[i]['location'] = camera['location']
                    break  # Salir del bucle una vez que se encuentra el valor

    return viewing


def get_url(viewing, camera_instance):
    return viewing[camera_instance]['url']