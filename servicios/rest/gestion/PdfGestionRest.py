# PdfGestionRest.py
from __future__ import annotations

from pprint import pprint

import requests
from datetime import datetime


class PdfGestionRest:
    """
    Cliente REST para la entidad PDF.
    Equivalente al controlador PdfGestionController en C#.

    URL base:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/pdf"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Obtener lista de PDFs
    # ========================================================
    def obtener_pdfs(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener PDFs: {e}")

    # ========================================================
    # GET → Obtener PDF por ID
    # ========================================================
    def obtener_pdf_por_id(self, id_pdf: int):
        if not id_pdf:
            raise ValueError("ID_PDF es obligatorio.")

        url = f"{self.BASE_URL}/{id_pdf}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener PDF por ID: {e}")

    # ========================================================
    # POST → Crear PDF
    # ========================================================
    def crear_pdf(self, id_pdf: int, id_factura: int | None, url_pdf: str, estado_pdf: bool = True):
        if not id_pdf:
            raise ValueError("ID_PDF es obligatorio.")

        payload = {
            "idPdf": id_pdf,
            "idFactura": id_factura,
            "urlPdf": url_pdf,
            "estadoPdf": estado_pdf,
            "fechaModificacionPdf": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            
            # Si el servidor devuelve 500, puede ser que el PDF ya exista
            if resp.status_code == 500:
                raise ConnectionError(f"Error al crear PDF: El servidor devolvió un error 500. Puede que el PDF ya exista. Status: {resp.status_code}, Response: {resp.text[:200]}")
            
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear PDF: {e}")

    # ========================================================
    # PUT → Actualizar PDF
    # ========================================================
    def actualizar_pdf(self, id_pdf: int, id_factura: int | None, url_pdf: str, estado_pdf: bool):
        if not id_pdf:
            raise ValueError("ID_PDF es obligatorio.")

        payload = {
            "idPdf": id_pdf,
            "idFactura": id_factura,
            "urlPdf": url_pdf,
            "estadoPdf": estado_pdf,
            "fechaModificacionPdf": datetime.now().isoformat()
        }

        url = f"{self.BASE_URL}/{id_pdf}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar PDF: {e}")

    # ========================================================
    # DELETE → Eliminación lógica
    # ========================================================
    def eliminar_pdf(self, id_pdf: int):
        if not id_pdf:
            raise ValueError("ID_PDF es obligatorio.")

        url = f"{self.BASE_URL}/{id_pdf}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar PDF: {e}")


client = PdfGestionRest()

# Listar PDFs
pprint(client.obtener_pdfs())