# habxres_gestion_rest.py
from pprint import pprint

import requests
from datetime import datetime


class HabxResGestionRest:
    """
    Cliente REST para HABXRES (Habitación por Reserva).
    Equivalente al controlador HabxResGestionController en C#.

    BASE:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/habxres"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ================================================================
    # GET → Obtener todos los registros HABXRES
    # ================================================================
    def obtener_habxres(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener HabxRes: {e}")

    # ================================================================
    # GET → Obtener por ID
    # ================================================================
    def obtener_por_id(self, id_habxres: int):
        if not id_habxres:
            raise ValueError("El ID_HABXRES es obligatorio.")

        url = f"{self.BASE_URL}/{id_habxres}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener HabxRes por ID: {e}")

    # ================================================================
    # POST → Crear vínculo Habitación-Reserva
    # ================================================================
    def crear_habxres(
        self,
        id_habxres: int,
        id_habitacion: str,
        id_reserva: int,
        capacidad: int = None,
        costo=None,
        descuento=None,
        impuestos=None,
        estado: bool = True
    ):
        if not id_habxres:
            raise ValueError("ID_HABXRES es obligatorio.")
        if not id_habitacion:
            raise ValueError("ID_HABITACION es obligatorio.")
        if not id_reserva:
            raise ValueError("ID_RESERVA es obligatorio.")

        payload = {
            "idHabxRes": id_habxres,
            "idHabitacion": id_habitacion,
            "idReserva": id_reserva,
            "capacidadReservaHabxRes": capacidad,
            "costoCalculadoHabxRes": costo,
            "descuentoHabxRes": descuento,
            "impuestosHabxRes": impuestos,
            "estadoHabxRes": estado,
            "fechaModificacionHabxRes": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear HabxRes: {e}")

    # ================================================================
    # PUT → Actualizar
    # ================================================================
    def actualizar_habxres(
        self,
        id_habxres: int,
        id_habitacion: str,
        id_reserva: int,
        capacidad=None,
        costo=None,
        descuento=None,
        impuestos=None,
        estado=None
    ):
        if not id_habxres:
            raise ValueError("ID_HABXRES es obligatorio.")

        payload = {
            "idHabxRes": id_habxres,
            "idHabitacion": id_habitacion,
            "idReserva": id_reserva,
            "capacidadReservaHabxRes": capacidad,
            "costoCalculadoHabxRes": costo,
            "descuentoHabxRes": descuento,
            "impuestosHabxRes": impuestos,
            "estadoHabxRes": estado,
        }

        url = f"{self.BASE_URL}/{id_habxres}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar HabxRes: {e}")

    # ================================================================
    # DELETE → Eliminación lógica
    # ================================================================
    def eliminar_habxres(self, id_habxres: int):
        if not id_habxres:
            raise ValueError("ID_HABXRES es obligatorio.")

        url = f"{self.BASE_URL}/{id_habxres}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False  # No existe

            resp.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar HabxRes: {e}")

i = HabxResGestionRest().obtener_habxres()
pprint(i)