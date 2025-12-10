# hold_gestion_rest.py
from pprint import pprint

import requests
from datetime import datetime


class HoldGestionRest:
    """
    Cliente REST para la entidad HOLD.
    Equivalente al controlador HoldGestionController en C#.

    URL base:
    
    """

    BASE_URL = "http://allphahousenycrg.runasp.net/api/gestion/hold"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    # ========================================================
    # GET → Obtener todos los HOLDs
    # ========================================================
    def obtener_hold(self):
        try:
            resp = requests.get(self.BASE_URL, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener HOLD: {e}")

    # ========================================================
    # GET → Obtener HOLD por ID
    # ========================================================
    def obtener_hold_por_id(self, id_hold: str):
        if not id_hold:
            raise ValueError("ID_HOLD es obligatorio.")

        url = f"{self.BASE_URL}/{id_hold}"

        try:
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al obtener HOLD por ID: {e}")

    # ========================================================
    # POST → Crear HOLD
    # ========================================================
    def crear_hold(
        self,
        id_hold: str,
        id_habitacion: str,
        id_reserva: int,
        tiempo_hold: int = None,
        fecha_inicio: datetime = None,
        fecha_final: datetime = None,
        estado: bool = True
    ):
        # Validaciones
        if not id_hold:
            raise ValueError("ID_HOLD es obligatorio.")
        if not id_habitacion:
            raise ValueError("ID_HABITACION es obligatorio.")
        if not id_reserva:
            raise ValueError("ID_RESERVA es obligatorio.")

        payload = {
            "idHold": id_hold,
            "idHabitacion": id_habitacion,
            "idReserva": id_reserva,
            "tiempoHold": tiempo_hold,
            "fechaInicioHold": fecha_inicio.isoformat() if fecha_inicio else None,
            "fechaFinalHold": fecha_final.isoformat() if fecha_final else None,
            "estadoHold": estado
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al crear HOLD: {e}")

    # ========================================================
    # PUT → Actualizar HOLD
    # ========================================================
    def actualizar_hold(
        self,
        id_hold: str,
        id_habitacion: str,
        id_reserva: int,
        tiempo_hold=None,
        fecha_inicio: datetime = None,
        fecha_final: datetime = None,
        estado=None
    ):
        if not id_hold:
            raise ValueError("ID_HOLD es obligatorio.")

        payload = {
            "idHold": id_hold,
            "idHabitacion": id_habitacion,
            "idReserva": id_reserva,
            "tiempoHold": tiempo_hold,
            "fechaInicioHold": fecha_inicio.isoformat() if fecha_inicio else None,
            "fechaFinalHold": fecha_final.isoformat() if fecha_final else None,
            "estadoHold": estado
        }

        url = f"{self.BASE_URL}/{id_hold}"

        try:
            resp = requests.put(url, json=payload, headers=self.headers)

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al actualizar HOLD: {e}")

    # ========================================================
    # DELETE → Eliminación lógica del HOLD
    # ========================================================
    def eliminar_hold(self, id_hold: str):
        if not id_hold:
            raise ValueError("ID_HOLD es obligatorio.")

        url = f"{self.BASE_URL}/{id_hold}"

        try:
            resp = requests.delete(url, headers=self.headers)

            if resp.status_code == 404:
                return False

            resp.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al eliminar HOLD: {e}")

    # ========================================================
    # POST → Expirar HOLDs vencidos automáticamente
    # ========================================================
    def expirar_holds_vencidos(self):
        """
        Expira automáticamente todos los HOLDs cuyo TIEMPO_HOLD haya vencido.
        
        LÓGICA:
        - Busca todos los HOLDs con ESTADO_HOLD = 1 (activos)
        - Que tengan RESERVA con ESTADO_GENERAL_RESERVA = 'PRE-RESERVA'
        - Donde FECHA_REGISTRO + TIEMPO_HOLD (segundos) <= AHORA
        - Los marca como ESTADO_HOLD = 0 (inactivos)
        - Marca la RESERVA como 'EXPIRADO'
        
        Returns:
            dict: Respuesta del servidor con datos de la operación
            
        Raises:
            ConnectionError: Si hay error de conexión
            
        Example:
            >>> hold_api = HoldGestionRest()
            >>> resultado = hold_api.expirar_holds_vencidos()
            >>> print(resultado)
            {'mensaje': 'Holds vencidos expirados correctamente.', 'totalExpirados': 2}
        """
        url = f"{self.BASE_URL}/expirar-vencidos"
        
        try:
            print(f"[DEBUG HoldGestionRest] POST {url} - Expirando HOLDs vencidos...")
            resp = requests.post(url, headers=self.headers, timeout=30)
            
            if not resp.ok:
                print(f"[ERROR HoldGestionRest] Error al expirar HOLDs: {resp.status_code}")
                raise ConnectionError(f"Error al expirar HOLDs: {resp.status_code} {resp.reason}")
            
            resultado = resp.json()
            print(f"[DEBUG HoldGestionRest] ✓ HOLDs expirados correctamente")
            print(f"[DEBUG HoldGestionRest] Respuesta: {resultado}")
            return resultado
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR HoldGestionRest] RequestException: {e}")
            raise ConnectionError(f"Error al expirar HOLDs: {e}")

    # ========================================================
    # UTILIDADES
    # ========================================================
    def obtener_holds_activos(self):
        """
        Obtiene solo los HOLDs activos (ESTADO_HOLD = 1 / True)
        
        Returns:
            list: Lista de HOLDs activos
        """
        try:
            todos_holds = self.obtener_hold()
            activos = [h for h in todos_holds if h.get('EstadoHold') == True]
            print(f"[DEBUG HoldGestionRest] {len(activos)} HOLDs activos de {len(todos_holds)} totales")
            return activos
        except Exception as e:
            print(f"[ERROR HoldGestionRest] Error al obtener HOLDs activos: {e}")
            return []

    def obtener_holds_por_reserva(self, id_reserva: int):
        """
        Obtiene todos los HOLDs asociados a una reserva específica
        
        Args:
            id_reserva (int): ID de la reserva
            
        Returns:
            list: HOLDs de esa reserva
        """
        try:
            todos_holds = self.obtener_hold()
            holds_reserva = [h for h in todos_holds if h.get('IdReserva') == id_reserva]
            print(f"[DEBUG HoldGestionRest] {len(holds_reserva)} HOLDs para reserva {id_reserva}")
            return holds_reserva
        except Exception as e:
            print(f"[ERROR HoldGestionRest] Error al obtener HOLDs por reserva: {e}")
            return []

    def tiempo_hold_restante(self, hold_dict: dict) -> int:
        """
        Calcula cuántos segundos quedan para que un HOLD venza.
        
        Args:
            hold_dict (dict): Datos del HOLD con FechaInicioHold y TiempoHold
            
        Returns:
            int: Segundos restantes (0 si ya venció, -1 si datos inválidos)
            
        Example:
            >>> hold = cliente.obtener_hold_por_id('HODA000001')
            >>> segundos_restantes = cliente.tiempo_hold_restante(hold)
            >>> if segundos_restantes > 0:
            ...     minutos = segundos_restantes // 60
            ...     print(f"Quedan {minutos} minutos")
        """
        try:
            fecha_inicio_str = hold_dict.get('FechaInicioHold')
            tiempo_hold_seg = hold_dict.get('TiempoHold', 0)
            
            if not fecha_inicio_str:
                print(f"[WARN HoldGestionRest] FechaInicioHold no disponible en HOLD")
                return -1
            
            # Parsear fecha (formato ISO: "2025-12-06T15:00:00")
            fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', '+00:00'))
            ahora = datetime.now()
            
            # Tiempo transcurrido en segundos
            tiempo_transcurrido = (ahora - fecha_inicio.replace(tzinfo=None)).total_seconds()
            
            # Tiempo restante
            restante = int(tiempo_hold_seg - tiempo_transcurrido)
            
            print(f"[DEBUG HoldGestionRest] HOLD {hold_dict.get('IdHold')}: "
                  f"Transcurridos={int(tiempo_transcurrido)}s, Restantes={restante}s, TiempoTotal={tiempo_hold_seg}s")
            
            return max(restante, 0)  # Retorna 0 si ya pasó
            
        except Exception as e:
            print(f"[ERROR HoldGestionRest] Error al calcular tiempo restante: {e}")
            return -1



# Script de prueba (comentado para producción)
# c = HoldGestionRest()
# c = c.obtener_hold()
# pprint(c)