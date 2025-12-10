# funciones_especiales_gestion_rest.py

import requests
from datetime import datetime


class FuncionesEspecialesGestionRest:
    """
    Cliente REST para los servicios:
    - Crear pre-reserva con HOLD
    - Confirmar reserva para usuario interno
    - Emitir factura para usuario interno

    Base URL:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/v1/hoteles/funciones-especiales"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ============================================================
    # UTILERÍA
    # ============================================================
    @staticmethod
    def _to_iso(dt):
        """Convierte string o datetime → ISO 8601"""
        if isinstance(dt, datetime):
            return dt.isoformat()
        if isinstance(dt, str):
            return dt
        raise ValueError("Fecha inválida: debe ser string ISO o datetime.")

    # ============================================================
    # POST → Crear PRE-RESERVA
    # ============================================================
    def crear_prereserva(
        self,
        id_habitacion: str,
        fecha_inicio,
        fecha_fin,
        numero_huespedes: int,
        nombre: str = None,
        apellido: str = None,
        correo: str = None,
        tipo_documento: str = None,
        documento: str = None,
        duracion_hold_seg: int = None,
        precio_actual: float = None,
        id_usuario: int = None
    ):
        url = f"{self.BASE_URL}/prereserva"

        payload = {
            "idHabitacion": id_habitacion,
            "fechaInicio": self._to_iso(fecha_inicio),
            "fechaFin": self._to_iso(fecha_fin),
            "numeroHuespedes": numero_huespedes,
            "nombre": nombre,
            "apellido": apellido,
            "correo": correo,
            "tipoDocumento": tipo_documento,
            "documento": documento,
            "duracionHoldSeg": duracion_hold_seg,
            "precioActual": precio_actual,
            "idUsuario": id_usuario
        }

        try:
            # Registrar payload y endpoint para debugging
            try:
                # Añadimos timeout para evitar esperas largas
                resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
            except requests.exceptions.RequestException as e:
                # Error de conexión (DNS, timeout, etc.)
                raise ConnectionError(f"Error al conectar con el servicio de pre-reserva: {e}")

            # Si el servidor respondió con código de error, intentar incluir el body en la excepción
            if not resp.ok:
                body = None
                try:
                    body = resp.text
                except Exception:
                    body = '<no body>'
                raise ConnectionError(f"Error al crear la pre-reserva: {resp.status_code} {resp.reason}. Body: {body}")

            # Respuesta exitosa
            try:
                return resp.json()
            except ValueError:
                # Respuesta no es JSON
                return {"mensaje": resp.text}

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error inesperado al crear la pre-reserva: {e}")

    # ============================================================
    # POST → Confirmar reserva de usuario interno
    # ============================================================
    def confirmar_reserva_interna(
        self,
        id_habitacion: str,
        id_hold: str,
        nombre: str = None,
        apellido: str = None,
        correo: str = None,
        tipo_documento: str = None,
        documento: str = None,
        fecha_inicio = None,
        fecha_fin = None,
        numero_huespedes: int = None
    ):
        url = f"{self.BASE_URL}/confirmar-usuario-interno"

        # Convertir documento a int si es posible
        documento_int = None
        if documento:
            try:
                documento_int = int(documento)
            except (ValueError, TypeError):
                documento_int = documento

        # Normalizar fechas: eliminar milisegundos para que coincidan con SQL Server
        # SQL Server compara a nivel de SEGUNDO
        fecha_inicio_norm = None
        fecha_fin_norm = None
        if fecha_inicio:
            if isinstance(fecha_inicio, str):
                # Remover milisegundos si existen (ej: "2025-12-04T15:00:00.000" -> "2025-12-04T15:00:00")
                fecha_inicio_norm = fecha_inicio.split('.')[0] if '.' in fecha_inicio else fecha_inicio
            else:
                fecha_inicio_norm = self._to_iso(fecha_inicio).split('.')[0]
        
        if fecha_fin:
            if isinstance(fecha_fin, str):
                fecha_fin_norm = fecha_fin.split('.')[0] if '.' in fecha_fin else fecha_fin
            else:
                fecha_fin_norm = self._to_iso(fecha_fin).split('.')[0]

        payload = {
            "idHabitacion": id_habitacion,
            "idHold": id_hold,
            "nombre": nombre,
            "apellido": apellido,
            "correo": correo,
            "tipoDocumento": tipo_documento,
            "documento": documento_int,
            "fechaInicio": fecha_inicio_norm,
            "fechaFin": fecha_fin_norm,
            "numeroHuespedes": numero_huespedes
        }

        try:
            print(f"[DEBUG confirmar_reserva_interna] URL: {url}")
            print(f"[DEBUG confirmar_reserva_interna] Payload: {payload}")
            
            resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            print(f"[DEBUG confirmar_reserva_interna] Status Code: {resp.status_code}")
            print(f"[DEBUG confirmar_reserva_interna] Response Headers: {dict(resp.headers)}")
            print(f"[DEBUG confirmar_reserva_interna] Response Text: {resp.text}")
            
            # Validar que la respuesta sea exitosa (2xx)
            if not resp.ok:
                body = resp.text if resp.text else '<sin contenido>'
                print(f"[ERROR confirmar_reserva_interna] Status {resp.status_code}: {body}")
                raise ConnectionError(f"Error al confirmar la reserva interna: {resp.status_code} {resp.reason}. Body: {body}")
            
            # Parsear JSON de la respuesta exitosa
            try:
                return resp.json()
            except ValueError as json_err:
                print(f"[ERROR confirmar_reserva_interna] No se pudo parsear JSON: {json_err}")
                return {"mensaje": resp.text}

        except requests.exceptions.RequestException as e:
            print(f"[ERROR confirmar_reserva_interna] RequestException: {str(e)}")
            raise ConnectionError(f"Error al confirmar la reserva interna: {e}")

    # ============================================================
    # POST → Emitir factura (usuario interno)
    # ============================================================

    def emitir_factura_interna(
            self,
            id_reserva: int,
            correo: str = None,
            url_factura: str = None,
            cuenta_origen: str = None,
            cuenta_destino: str = None,
            nombre: str = None,
            apellido: str = None,
            tipo_documento: str = None,
            documento: str = None
    ):
        # El endpoint C# usa query parameters según el controlador (FromUri)
        url = f"{self.BASE_URL}/emitir-interno"
        
        # Construir query parameters
        params = {
            "idReserva": id_reserva
        }
        
        if correo:
            params["correo"] = correo
        if nombre:
            params["nombre"] = nombre
        if apellido:
            params["apellido"] = apellido
        if tipo_documento:
            params["tipoDocumento"] = tipo_documento
        if documento:
            params["documento"] = documento

        try:
            print(f"[DEBUG emitir_factura_interna] URL: {url}")
            print(f"[DEBUG emitir_factura_interna] Params: {params}")
            
            # El endpoint C# usa query parameters según el controlador
            resp = requests.post(url, params=params, headers=self.headers, timeout=30)
            
            print(f"[DEBUG emitir_factura_interna] Status Code: {resp.status_code}")
            print(f"[DEBUG emitir_factura_interna] Response Text: {resp.text}")
            
            if not resp.ok:
                body = resp.text if resp.text else '<sin contenido>'
                print(f"[ERROR emitir_factura_interna] Status {resp.status_code}: {body}")
                raise ConnectionError(f"Error al emitir la factura interna: {resp.status_code} {resp.reason}. Body: {body}")
            
            # Parsear JSON
            try:
                resultado = resp.json()
                print(f"[DEBUG emitir_factura_interna] JSON parseado correctamente")
                return resultado
            except ValueError as json_err:
                print(f"[ERROR emitir_factura_interna] No se pudo parsear JSON: {json_err}")
                raise ConnectionError(f"Respuesta no es JSON válido: {resp.text}")

        except requests.exceptions.RequestException as e:
            print(f"[ERROR emitir_factura_interna] RequestException: {str(e)}")
            raise ConnectionError(f"Error al emitir la factura interna: {e}")

    def cancelar_prereserva(self, id_hold: str):
        """
        Cancela una pre-reserva (HOLD activo) usando el endpoint:
        DELETE /prereserva/{idHold}
        """
        if not id_hold:
            raise ValueError("id_hold es obligatorio.")

        url = f"{self.BASE_URL}/prereserva/{id_hold}"

        try:
            resp = requests.delete(url, headers=self.headers)
            resp.raise_for_status()
            # DELETE puede no devolver contenido, así que manejamos ambos casos
            if resp.content:
                return resp.json()
            return {"mensaje": "Pre-reserva cancelada correctamente"}

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al cancelar la pre-reserva: {e}")
# ============================================================
# PRUEBA RÁPIDA (Sólo si se ejecuta este archivo directamente)
# ============================================================
if __name__ == "__main__":
    api = FuncionesEspecialesGestionRest()

    try:
        resultado = api.emitir_factura_interna(
            id_reserva=113,
            correo="dancarranza@outlook.com",
        )

        print("=== RESPUESTA API ===")
        print(resultado)

    except Exception as e:
        print("ERROR EJECUTANDO CONFIRMAR RESERVA:", e)