# habitaciones_gestion_rest.py
from pprint import pprint

import requests
from datetime import datetime


class HabitacionesGestionRest:
    """
    Cliente REST para HABITACIONES.
    Equivale a HabitacionesGestionController en C#.

    BASE:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/habitaciones"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # =====================================================================
    # GET → Obtener todas las habitaciones
    # =====================================================================
    def obtener_habitaciones(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener habitaciones: {e}")

    # =====================================================================
    # GET → Obtener habitación por ID
    # =====================================================================
    def obtener_por_id(self, id_habitacion: str):
        if not id_habitacion:
            raise ValueError("ID de la habitación es obligatorio.")

        url = f"{self.BASE_URL}/{id_habitacion}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener la habitación: {e}")

    # =====================================================================
    # POST → Crear habitación
    # =====================================================================
    def crear_habitacion(
        self,
        id_habitacion: str,
        id_tipo_habitacion: int,
        id_ciudad: int,
        id_hotel: int,
        nombre_habitacion: str = None,
        precio_normal=None,
        precio_actual=None,
        capacidad=None,
        estado=None,
        estado_activo: bool = True,
        fecha_registro=None
    ):
        if not id_habitacion:
            raise ValueError("El ID_HABITACION es obligatorio.")

        payload = {
            "idHabitacion": id_habitacion,
            "idTipoHabitacion": id_tipo_habitacion,
            "idCiudad": id_ciudad,
            "idHotel": id_hotel,
            "nombreHabitacion": nombre_habitacion,
            "precioNormalHabitacion": precio_normal,
            "precioActualHabitacion": precio_actual,
            "capacidadHabitacion": capacidad,
            "estadoHabitacion": estado,
            "estadoActivoHabitacion": estado_activo,
            "fechaRegistroHabitacion": (
                fecha_registro.isoformat() if fecha_registro else datetime.now().isoformat()
            )
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear habitación: {e}")

    # =====================================================================
    # PUT → Actualizar habitación
    # =====================================================================
    def actualizar_habitacion(
        self,
        id_habitacion: str,
        id_tipo_habitacion: int,
        id_ciudad: int,
        id_hotel: int,
        nombre_habitacion: str = None,
        precio_normal=None,
        precio_actual=None,
        capacidad=None,
        estado=None,
        estado_activo=None
    ):
        if not id_habitacion:
            raise ValueError("ID no válido.")

        payload = {
            "idHabitacion": id_habitacion,
            "idTipoHabitacion": id_tipo_habitacion,
            "idCiudad": id_ciudad,
            "idHotel": id_hotel,
            "nombreHabitacion": nombre_habitacion,
            "precioNormalHabitacion": precio_normal,
            "precioActualHabitacion": precio_actual,
            "capacidadHabitacion": capacidad,
            "estadoHabitacion": estado,
            "estadoActivoHabitacion": estado_activo
        }

        url = f"{self.BASE_URL}/{id_habitacion}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar habitación: {e}")

    # =====================================================================
    # DELETE → Eliminación lógica
    # =====================================================================
    def eliminar_habitacion(self, id_habitacion: str):
        if not id_habitacion:
            raise ValueError("El id_habitacion es obligatorio.")

        url = f"{self.BASE_URL}/{id_habitacion}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar habitación: {e}")
api = HabitacionesGestionRest()
api = api.obtener_habitaciones()
pprint(api)