# ImagenHabitacionGestionRest.py
from pprint import pprint

import requests
from datetime import datetime


class ImagenHabitacionGestionRest:
    """
    Cliente REST para la entidad IMAGEN_HABITACION.
    Equivalente al controlador ImagenesHabitacionGestionController en C#.

    URL base:
   
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/imagenes-habitacion"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Obtener todas las imágenes
    # ========================================================
    def obtener_imagenes(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener imágenes: {e}")

    # ========================================================
    # GET → Obtener imagen por ID
    # ========================================================
    def obtener_imagen_por_id(self, id_imagen: int):
        if not id_imagen:
            raise ValueError("ID_IMAGEN_HABITACION es obligatorio.")

        url = f"{self.BASE_URL}/{id_imagen}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener imagen por ID: {e}")

    # ========================================================
    # POST → Crear nueva imagen
    # ========================================================
    def crear_imagen(self, id_habitacion: str, url_imagen: str, estado_imagen: bool = True):
        if not id_habitacion:
            raise ValueError("ID_HABITACION es obligatorio.")

        payload = {
            "idHabitacion": id_habitacion,
            "urlImagen": url_imagen,
            "estadoImagen": estado_imagen,
            "fechaModificacionImagenHabitacion": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear imagen: {e}")

    # ========================================================
    # PUT → Actualizar imagen
    # ========================================================
    def actualizar_imagen(self, id_imagen: int, id_habitacion: str, url_imagen: str, estado_imagen: bool):
        if not id_imagen:
            raise ValueError("ID_IMAGEN_HABITACION es obligatorio.")

        payload = {
            "idImagenHabitacion": id_imagen,
            "idHabitacion": id_habitacion,
            "urlImagen": url_imagen,
            "estadoImagen": estado_imagen,
            "fechaModificacionImagenHabitacion": datetime.now().isoformat()
        }

        url = f"{self.BASE_URL}/{id_imagen}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar imagen: {e}")

    # ========================================================
    # DELETE → Eliminación lógica
    # ========================================================
    def eliminar_imagen(self, id_imagen: int):
        if not id_imagen:
            raise ValueError("ID_IMAGEN_HABITACION es obligatorio.")

        url = f"{self.BASE_URL}/{id_imagen}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar imagen: {e}")

o = ImagenHabitacionGestionRest()
o.obtener_imagenes()
pprint(o.obtener_imagenes())