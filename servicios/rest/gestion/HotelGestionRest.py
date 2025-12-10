# hotel_gestion_rest.py
import requests
from datetime import datetime


class HotelGestionRest:
    """
    Cliente REST para la entidad HOTEL.
    Equivalente al controlador HotelGestionController en C#.

    URL base:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/hotel"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Obtener lista de hoteles
    # ========================================================
    def obtener_hoteles(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener hoteles: {e}")

    # ========================================================
    # GET → Obtener hotel por ID
    # ========================================================
    def obtener_hotel_por_id(self, id_hotel: int):
        if not id_hotel:
            raise ValueError("ID_HOTEL es obligatorio.")

        url = f"{self.BASE_URL}/{id_hotel}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener hotel por ID: {e}")

    # ========================================================
    # POST → Crear hotel
    # ========================================================
    def crear_hotel(self, id_hotel: int, nombre_hotel: str, estado_hotel: bool = True):
        if not id_hotel:
            raise ValueError("ID_HOTEL es obligatorio.")
        if not nombre_hotel:
            raise ValueError("NOMBRE_HOTEL es obligatorio.")

        payload = {
            "idHotel": id_hotel,
            "nombreHotel": nombre_hotel,
            "estadoHotel": estado_hotel,
            "fechaModificacionHotel": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear hotel: {e}")

    # ========================================================
    # PUT → Actualizar hotel
    # ========================================================
    def actualizar_hotel(self, id_hotel: int, nombre_hotel: str, estado_hotel: bool):
        if not id_hotel:
            raise ValueError("ID_HOTEL es obligatorio.")

        payload = {
            "idHotel": id_hotel,
            "nombreHotel": nombre_hotel,
            "estadoHotel": estado_hotel,
            "fechaModificacionHotel": datetime.now().isoformat()
        }

        url = f"{self.BASE_URL}/{id_hotel}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar hotel: {e}")

    # ========================================================
    # DELETE → Eliminación lógica
    # ========================================================
    def eliminar_hotel(self, id_hotel: int):
        if not id_hotel:
            raise ValueError("ID_HOTEL es obligatorio.")

        url = f"{self.BASE_URL}/{id_hotel}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar hotel: {e}")
