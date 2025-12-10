# views_hold.py
from pprint import pprint

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.HoldGestionRest import HoldGestionRest
from webapp.decorators import admin_required, admin_required_ajax
from datetime import datetime

def parse_fecha_ymd(value):
    """
    Acepta:
      - 'YYYY-MM-DD'
      - 'YYYY-MM-DDTHH:MM:SS' (lo que suele devolver el REST)
    y devuelve un datetime.date, o None si viene vacío.
    """
    if not value:
        return None

    value = str(value).strip()

    # Intentar ISO completo primero (ej. '2025-11-29T00:00:00')
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        pass

    # Intentar solo 'YYYY-MM-DD'
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Fecha inválida: {value!r}. Formato esperado YYYY-MM-DD.")


# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class HoldView(View):
    template_name = "webapp/usuario/administrador/crud/hold/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR (20 en 20)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HoldListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = HoldGestionRest()

        try:
            data = api.obtener_hold()

            total = len(data)
            total_pages = (total + page_size - 1) // page_size

            inicio = (page - 1) * page_size
            fin = inicio + page_size

            return JsonResponse({
                "status": "ok",
                "data": data[inicio:fin],
                "page": page,
                "total_pages": total_pages
            })

        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión a internet"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente en unos momentos"}, status=504)
        except HTTPError as e:
            return JsonResponse({"status": "error", "message": f"Error en el servidor. Contacte al administrador"}, status=500)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "Error al cargar la lista. Intente nuevamente"}, status=500)


# ============================================================
# OBTENER UNO
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HoldGetAjaxView(View):
    def get(self, request, id_hold):
        api = HoldGestionRest()
        try:
            data = api.obtener_hold_por_id(id_hold)
            return JsonResponse({"status": "ok", "data": data})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo obtener el registro. Verifique que el ID sea correcto"}, status=404)


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class HoldCreateAjaxView(View):
    def post(self, request):
        api = HoldGestionRest()
        print("*****************************    EJECUCION DE CREATE POST     *****************************")
        pprint(request.POST)

        try:
            data_post = request.POST.dict()

            # ---- IdHold ----
            id_hold = data_post.get("IdHold")
            if not id_hold:
                raise ValueError("IdHold es obligatorio.")

            # ---- IdHabitacion ----
            id_habitacion = data_post.get("IdHabitacion")
            if not id_habitacion:
                raise ValueError("IdHabitacion es obligatorio.")

            # ---- IdReserva ----
            id_reserva_txt = data_post.get("IdReserva")
            if id_reserva_txt in ("", None):
                raise ValueError("IdReserva es obligatorio.")
            try:
                id_reserva = int(id_reserva_txt)
            except ValueError:
                raise ValueError(f"IdReserva inválido: {id_reserva_txt!r}")

            # ---- TiempoHold (opcional) ----
            tiempo_txt = data_post.get("TiempoHold")
            if tiempo_txt in ("", None):
                tiempo_hold = None
            else:
                try:
                    tiempo_hold = int(tiempo_txt)
                except ValueError:
                    raise ValueError(f"TiempoHold inválido: {tiempo_txt!r}")

            # ---- Fechas (opcionales) -> convertir a date ----
            fecha_inicio = parse_fecha_ymd(data_post.get("FechaInicio"))
            fecha_final  = parse_fecha_ymd(data_post.get("FechaFinal"))

            # ---- Estado ----
            estado_txt = data_post.get("EstadoHold")
            estado = str(estado_txt).lower() == "true"

            # ---- Llamada al REST (ahora con fechas como date) ----
            api.crear_hold(
                id_hold=id_hold,
                id_habitacion=id_habitacion,
                id_reserva=id_reserva,
                tiempo_hold=tiempo_hold,
                fecha_inicio=fecha_inicio,
                fecha_final=fecha_final,
                estado=estado,
            )

            return JsonResponse({"status": "ok", "message": "Hold creado exitosamente"})

        except ConnectionError:
            return JsonResponse(
                {"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión"},
                status=503,
            )
        except Timeout:
            return JsonResponse(
                {"status": "error", "message": "El servidor no responde. Intente nuevamente"},
                status=504,
            )
        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400,
            )
        except Exception as e:
            print("ERROR HoldCreateAjaxView:", repr(e))
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo crear el registro. Verifique los datos ingresados",
                },
                status=500,
            )


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class HoldUpdateAjaxView(View):
    def post(self, request, id_hold):
        api = HoldGestionRest()
        print("*****************************    EJECUCION DE UPDATE POST     *****************************")
        pprint(request.POST)

        try:
            data_post = request.POST.dict()
            actual = api.obtener_hold_por_id(id_hold) or {}

            # -------- IdHabitacion --------
            id_habitacion = data_post.get("IdHabitacion") or actual.get("IdHabitacion")
            if not id_habitacion:
                raise ValueError("IdHabitacion es obligatorio.")

            # -------- IdReserva --------
            id_reserva_txt = data_post.get("IdReserva") or actual.get("IdReserva")
            if id_reserva_txt in ("", None):
                raise ValueError("IdReserva es obligatorio.")
            try:
                id_reserva = int(id_reserva_txt)
            except ValueError:
                raise ValueError(f"IdReserva inválido: {id_reserva_txt!r}")

            # -------- TiempoHold (opcional) --------
            tiempo_txt = data_post.get("TiempoHold")
            if tiempo_txt in ("", None):
                tiempo_txt = actual.get("TiempoHold")

            if tiempo_txt in ("", None):
                tiempo_hold = None
            else:
                try:
                    tiempo_hold = int(tiempo_txt)
                except ValueError:
                    raise ValueError(f"TiempoHold inválido: {tiempo_txt!r}")

            # -------- Fechas (opcionales) --------
            # del POST (YYYY-MM-DD) o del actual (YYYY-MM-DDTHH:MM:SS)
            fecha_inicio_txt = (
                data_post.get("FechaInicio")
                or actual.get("FechaInicioHold")
                or None
            )
            fecha_final_txt = (
                data_post.get("FechaFinal")
                or actual.get("FechaFinalHold")
                or None
            )

            fecha_inicio = parse_fecha_ymd(fecha_inicio_txt)
            fecha_final  = parse_fecha_ymd(fecha_final_txt)

            # -------- EstadoHold --------
            estado_txt = data_post.get("EstadoHold")
            if estado_txt is not None and estado_txt != "":
                estado = str(estado_txt).lower() == "true"
            else:
                estado = actual.get("EstadoHold", True)

            # -------- Llamada al REST --------
            api.actualizar_hold(
                id_hold=id_hold,
                id_habitacion=id_habitacion,
                id_reserva=id_reserva,
                tiempo_hold=tiempo_hold,
                fecha_inicio=fecha_inicio,
                fecha_final=fecha_final,
                estado=estado,
            )

            return JsonResponse(
                {"status": "ok", "message": "Hold actualizado exitosamente"}
            )

        except ConnectionError:
            return JsonResponse(
                {"status": "error", "message": "No se pudo conectar con el servidor"},
                status=503,
            )
        except Timeout:
            return JsonResponse(
                {"status": "error", "message": "El servidor no responde. Intente nuevamente"},
                status=504,
            )
        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400,
            )
        except Exception as e:
            print("ERROR HoldUpdateAjaxView:", repr(e))
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo actualizar el registro. Verifique los datos",
                },
                status=500,
            )

# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class HoldDeleteAjaxView(View):
    def post(self, request, id_hold):

        api = HoldGestionRest()
        try:
            api.eliminar_hold(id_hold)
            return JsonResponse({"status": "ok", "message": "Hold eliminado exitosamente"})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)
# ============================================================
# OBTENER SIGUIENTE ID HOLD (prefijo de 4 caracteres)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HoldNextIdAjaxView(View):
    """
    Calcula el siguiente IdHold basado en el IdHold numérico más alto
    encontrado, manteniendo su prefijo de 4 caracteres.
    Ejemplos válidos: HOCA000001, HLD-2025001, HXYZ12, etc.
    """

    def get(self, request):
        api = HoldGestionRest()

        try:
            data = api.obtener_hold()

            if not isinstance(data, list):
                data = []

            max_number = 0
            best_prefix = ""
            suffix_length = 6   # longitud por defecto del sufijo

            for hold in data:
                id_hold = hold.get("IdHold")

                # ignorar si no es string o es demasiado corto
                if not isinstance(id_hold, str) or len(id_hold) < 5:
                    continue

                # tomamos SIEMPRE los primeros 4 caracteres como prefijo
                prefix = id_hold[:4]
                num_str = id_hold[4:]

                try:
                    current_number = int(num_str)

                    if current_number > max_number:
                        max_number = current_number
                        best_prefix = prefix
                        suffix_length = len(num_str)

                except ValueError:
                    # si el sufijo no es numérico, lo ignoramos
                    continue

            # calculamos el siguiente número
            next_number = max_number + 1

            if not best_prefix:
                # prefijo por defecto si no hay registros válidos
                best_prefix = "HOCA"
                suffix_length = 6

            next_suffix = str(next_number).zfill(suffix_length)
            next_id = f"{best_prefix}{next_suffix}"

            return JsonResponse({
                "status": "ok",
                "next_id": next_id
            })

        except ConnectionError:
            return JsonResponse(
                {"status": "error",
                 "message": "No se pudo conectar para generar el ID"},
                status=503
            )
        except Exception as e:
            # en caso de error, devolvemos un mensaje y un ID sugerido
            return JsonResponse(
                {"status": "error",
                 "message": f"Error al generar ID: {e}"},
                status=500
            )

