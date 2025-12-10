# MetodoPagoGestionRest.py
from pprint import pprint

import requests
from datetime import datetime


class MetodoPagoGestionRest:
    """
    Cliente REST para la entidad METODO_PAGO.
    Equivalente al controlador MetodoPagoGestionController en C#.

    URL base:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/metodo-pago"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Obtener todos los métodos de pago
    # ========================================================
    def obtener_metodos_pago(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener métodos de pago: {e}")

    # ========================================================
    # GET → Obtener método de pago por ID
    # ========================================================
    def obtener_metodo_pago_por_id(self, id_metodo: int):
        if not id_metodo:
            raise ValueError("ID_METODO_PAGO es obligatorio.")

        url = f"{self.BASE_URL}/{id_metodo}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener método de pago por ID: {e}")

    # ========================================================
    # POST → Crear método de pago
    # ========================================================
    def crear_metodo_pago(self, id_metodo: int, nombre_metodo: str, estado_metodo: bool = True):
        if not id_metodo:
            raise ValueError("ID_METODO_PAGO es obligatorio.")
        if not nombre_metodo:
            raise ValueError("NOMBRE_METODO_PAGO es obligatorio.")

        payload = {
            "idMetodoPago": id_metodo,
            "nombreMetodoPago": nombre_metodo,
            "estadoMetodoPago": estado_metodo,
            "fechaModificacionMetodoPago": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear método de pago: {e}")

    # ========================================================
    # PUT → Actualizar método de pago
    # ========================================================
    def actualizar_metodo_pago(self, id_metodo: int, nombre_metodo: str, estado_metodo: bool):
        if not id_metodo:
            raise ValueError("ID_METODO_PAGO es obligatorio.")

        payload = {
            "idMetodoPago": id_metodo,
            "nombreMetodoPago": nombre_metodo,
            "estadoMetodoPago": estado_metodo,
            "fechaModificacionMetodoPago": datetime.now().isoformat()
        }

        url = f"{self.BASE_URL}/{id_metodo}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar método de pago: {e}")

    # ========================================================
    # DELETE → Eliminación lógica
    # ========================================================
    def eliminar_metodo_pago(self, id_metodo: int):
        if not id_metodo:
            raise ValueError("ID_METODO_PAGO es obligatorio.")

        url = f"{self.BASE_URL}/{id_metodo}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar método de pago: {e}")

client = MetodoPagoGestionRest()

# Listar métodos de pago
pprint(client.obtener_metodos_pago())