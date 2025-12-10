# PagoGestionRest.py
from __future__ import annotations

from datetime import datetime
import requests


class PagoGestionRest:
    """
    Cliente REST para la entidad PAGO.
    Equivalente al controlador PagoGestionController en C#.

    URL base:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/pago"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Listar pagos
    # ========================================================
    def obtener_pagos(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener pagos: {e}")

    # ========================================================
    # GET → Obtener pago por ID
    # ========================================================
    def obtener_pago_por_id(self, id_pago: int):
        if not id_pago:
            raise ValueError("ID_PAGO es obligatorio.")

        url = f"{self.BASE_URL}/{id_pago}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener pago por ID: {e}")

    # ========================================================
    # POST → Crear pago (CRUD genérico, NO usa el SP nuevo)
    # ========================================================
    def crear_pago(
        self,
        id_pago: int,
        id_metodo_pago: int,
        id_unico_usuario_externo: int | None,
        id_unico_usuario: int,
        id_factura: int | None,
        cuenta_origen: str | None,
        cuenta_destino: str | None,
        monto_total: float | None,
        fecha_emision: datetime | None,
        estado_pago: bool = True
    ):
        if not id_pago:
            raise ValueError("ID_PAGO es obligatorio.")
        if not id_metodo_pago:
            raise ValueError("ID_METODO_PAGO es obligatorio.")

        payload = {
            "idPago": id_pago,
            "idMetodoPago": id_metodo_pago,
            "idUnicoUsuarioExterno": id_unico_usuario_externo,
            "idUnicoUsuario": id_unico_usuario,
            "idFactura": id_factura,
            "cuentaOrigenPago": cuenta_origen,
            "cuentaDestinoPago": cuenta_destino,
            "montoTotalPago": monto_total,
            "fechaEmisionPago": fecha_emision.isoformat() if fecha_emision else None,
            "estadoPago": estado_pago,
            "fechaModificacionPago": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear pago: {e}")

    # ========================================================
    # PUT → Actualizar pago
    # ========================================================
    def actualizar_pago(
        self,
        id_pago: int,
        id_metodo_pago: int,
        id_unico_usuario_externo: int | None,
        id_unico_usuario: int,
        id_factura: int | None,
        cuenta_origen: str | None,
        cuenta_destino: str | None,
        monto_total: float | None,
        fecha_emision: datetime | None,
        estado_pago: bool
    ):
        if not id_pago:
            raise ValueError("ID_PAGO es obligatorio.")

        payload = {
            "idPago": id_pago,
            "idMetodoPago": id_metodo_pago,
            "idUnicoUsuarioExterno": id_unico_usuario_externo,
            "idUnicoUsuario": id_unico_usuario,
            "idFactura": id_factura,
            "cuentaOrigenPago": cuenta_origen,
            "cuentaDestinoPago": cuenta_destino,
            "montoTotalPago": monto_total,
            "fechaEmisionPago": fecha_emision.isoformat() if fecha_emision else None,
            "estadoPago": estado_pago,
            "fechaModificacionPago": datetime.now().isoformat()
        }

        url = f"{self.BASE_URL}/{id_pago}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar pago: {e}")

    # ========================================================
    # DELETE → Eliminación lógica
    # ========================================================
    def eliminar_pago(self, id_pago: int):
        if not id_pago:
            raise ValueError("ID_PAGO es obligatorio.")

        url = f"{self.BASE_URL}/{id_pago}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar pago: {e}")

    # ========================================================
    # NUEVO → Registrar pago de una reserva interna (usa SP)
    # POST: /api/gestion/pago/reserva-interna
    # ========================================================
    def registrar_pago_reserva_interna(
        self,
        id_reserva: int | None,
        id_unico_usuario: int,
        monto_total: float,
        cuenta_origen: str,
        cuenta_destino: str,
        id_unico_usuario_externo: int | None = None,
        id_metodo_pago: int = 2
    ):
        """
        Llama al endpoint C# que ejecuta el SP sp_registrarPagoReservaInterno
        y registra el pago en la tabla PAGO.

        IMPORTANTE: aquí usamos las MISMAS claves que en Swagger:
        {
          "IdReserva": 170,
          "IdUnicoUsuario": 7,
          "MontoTotalPago": 102.24,
          "CuentaOrigenPago": "0707001320",
          "CuentaDestinoPago": "0707001310",
          "IdUnicoUsuarioExterno": null,
          "IdMetodoPago": 2
        }
        """
        url = f"{self.BASE_URL}/reserva-interna"

        payload = {
            "IdReserva": id_reserva,
            "IdUnicoUsuario": id_unico_usuario,
            "MontoTotalPago": monto_total,
            "CuentaOrigenPago": cuenta_origen,
            "CuentaDestinoPago": cuenta_destino,
            "IdUnicoUsuarioExterno": id_unico_usuario_externo,
            "IdMetodoPago": id_metodo_pago
        }

        try:
            resp = requests.post(url, json=payload, headers=self.headers)

            # Debug para ver qué responde tu API
            print("[DEBUG registrar_pago_reserva_interna] status:", resp.status_code)
            print("[DEBUG registrar_pago_reserva_interna] body:", resp.text)

            resp.raise_for_status()
            # Si el SP devuelve el registro insertado, aquí lo recibes
            if resp.text.strip():
                try:
                    return resp.json()
                except ValueError:
                    # Si no es JSON (por ejemplo, vacío), devolvemos algo simbólico
                    return {"mensaje": "Pago registrado correctamente (sin cuerpo JSON)"}
            else:
                return {"mensaje": "Pago registrado correctamente (sin cuerpo JSON)"}

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al registrar pago reserva interna: {e}")


# ========================================================
# Funciones de prueba (opcional)
# ========================================================
def crear_pago_prueba():
    """
    Prueba del CRUD genérico (POST /api/gestion/pago).
    No usa el SP nuevo, solo el insert directo.
    """
    api = PagoGestionRest()

    try:
        resp = api.crear_pago(
            id_pago=122,                 # ID del pago (usa uno que no exista aún)
            id_metodo_pago=1,           # Ej: 1 = Visa
            id_unico_usuario_externo=None,  # Sin usuario externo
            id_unico_usuario=1,         # Usuario interno 1
            id_factura=None,            # Puede ir None
            cuenta_origen="1234",
            cuenta_destino="5678",
            monto_total=100.46,         # Monto de prueba
            fecha_emision=None,         # Deja que el backend maneje este campo
            estado_pago=True            # Pago completo/activo
        )
        print("✅ Pago creado correctamente (CRUD genérico):")
        print(resp)

    except Exception as e:
        print("❌ Error al crear pago (CRUD genérico):")
        print(e)


def probar_registrar_pago_reserva_interna():
    """
    Prueba específica del endpoint /reserva-interna,
    que usa el SP sp_registrarPagoReservaInterno.
    """
    api = PagoGestionRest()

    try:
        resp = api.registrar_pago_reserva_interna(
            id_reserva=170,              # Usa una reserva CONFIRMADA real
            id_unico_usuario=7,          # Usuario interno existente y activo
            monto_total=102.24,
            cuenta_origen="0707001320",
            cuenta_destino="0707001310",
            id_unico_usuario_externo=None,
            id_metodo_pago=2
        )
        print("✅ Pago reserva interna registrado correctamente:")
        print(resp)

    except Exception as e:
        print("❌ Error al registrar pago reserva interna:")
        print(e)


if __name__ == "__main__":
    # Puedes probar uno u otro:
    # crear_pago_prueba()
    probar_registrar_pago_reserva_interna()
