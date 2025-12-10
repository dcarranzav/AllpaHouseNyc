# PaisGestionRest.py
import requests
from datetime import datetime


class PaisGestionRest:
    """
    Cliente REST para la entidad PAIS.
    Equivalente al controlador PaisGestionController en C#.

    URL base:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/pais"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Lista de países
    # ========================================================
    def obtener_paises(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener países: {e}")

    # ========================================================
    # GET → País por ID
    # ========================================================
    def obtener_pais_por_id(self, id_pais: int):
        if not id_pais:
            raise ValueError("ID_PAIS es obligatorio.")

        url = f"{self.BASE_URL}/{id_pais}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener país por ID: {e}")

    # ========================================================
    # POST → Crear país
    # ========================================================
    def crear_pais(self, id_pais: int, nombre_pais: str, estado_pais: bool = True):
        if not id_pais:
            raise ValueError("ID_PAIS es obligatorio.")
        if not nombre_pais:
            raise ValueError("NOMBRE_PAIS es obligatorio.")

        payload = {
            "idPais": id_pais,
            "nombrePais": nombre_pais,
            "estadoPais": estado_pais,
            "fechaModificacionPais": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear país: {e}")

    # ========================================================
    # PUT → Actualizar país
    # ========================================================
    def actualizar_pais(self, id_pais: int, nombre_pais: str, estado_pais: bool):
        if not id_pais:
            raise ValueError("ID_PAIS es obligatorio.")

        payload = {
            "idPais": id_pais,
            "nombrePais": nombre_pais,
            "estadoPais": estado_pais,
            "fechaModificacionPais": datetime.now().isoformat()
        }

        url = f"{self.BASE_URL}/{id_pais}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar país: {e}")

    # ========================================================
    # DELETE → Eliminación lógica
    # ========================================================
    def eliminar_pais(self, id_pais: int):
        if not id_pais:
            raise ValueError("ID_PAIS es obligatorio.")

        url = f"{self.BASE_URL}/{id_pais}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar país: {e}")

client = PaisGestionRest()

print(client.obtener_paises())
