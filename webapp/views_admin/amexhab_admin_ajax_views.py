from pprint import pprint

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from reportlab.lib.randomtext import PRINTING
from requests.exceptions import ConnectionError, Timeout, HTTPError

from servicios.rest.gestion.AmexHabGestionRest import AmexHabGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class AmexHabView(View):
    template_name = "webapp/usuario/administrador/crud/amexhab/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# OBTENER LISTA
# ============================================================
from math import ceil

@method_decorator(admin_required_ajax, name='dispatch')
class AmexHabListAjaxView(View):
    def get(self, request):

        api = AmexHabGestionRest()
        try:
            data = api.obtener_amexhab()

            # ------------------------------------
            # PAGINACIÓN MANUAL (20 POR PÁGINA)
            # ------------------------------------
            page = int(request.GET.get("page", 1))
            per_page = 20

            total_items = len(data)
            total_pages = ceil(total_items / per_page)

            # Cálculo de rango
            start = (page - 1) * per_page
            end = start + per_page

            paginated_data = data[start:end]

            return JsonResponse({
                "status": "ok",
                "data": paginated_data,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items
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
class AmexHabGetAjaxView(View):
    def get(self, request, id_habitacion, id_amenidad):
        api = AmexHabGestionRest()
        try:
            data = api.obtener_amexhab_por_id(id_habitacion, id_amenidad)
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
class AmexHabCreateAjaxView(View):
    def post(self, request):
        try:
            idHabitacion = request.POST.get("IdHabitacion")
            idAmenidad = request.POST.get("IdAmenidad")
            estado = request.POST.get("EstadoAmexHab") == "true"

            if not idHabitacion:
                return JsonResponse({"status": "error", "message": "ID Habitación es requerido"}, status=400)
            
            if not idAmenidad:
                return JsonResponse({"status": "error", "message": "ID Amenidad es requerido"}, status=400)

            api = AmexHabGestionRest()
            api.crear_amexhab(idHabitacion, int(idAmenidad), estado)
            return JsonResponse({"status": "ok", "message": "Amenidad por Habitación creada exitosamente"})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo crear el registro. Verifique los datos ingresados"}, status=500)


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class AmexHabUpdateAjaxView(View):
    def post(self, request, id_habitacion, id_amenidad):
        try:
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoAmexHab")
            if estado_enviado is not None:
                estado = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                api = AmexHabGestionRest()
                registro_actual = api.obtener_amexhab_por_id(id_habitacion, int(id_amenidad))
                estado = registro_actual.get("EstadoAmexHab", True) if registro_actual else True

            api = AmexHabGestionRest()
            api.actualizar_amexhab(id_habitacion, int(id_amenidad), estado)
            return JsonResponse({"status": "ok", "message": "Amenidad por Habitación actualizada exitosamente"})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo actualizar el registro. Verifique los datos"}, status=500)


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class AmexHabDeleteAjaxView(View):
    def post(self, request, id_habitacion, id_amenidad):

        api = AmexHabGestionRest()
        try:
            api.eliminar_amexhab(id_habitacion, int(id_amenidad))
            return JsonResponse({"status": "ok", "message": "Amenidad por Habitación eliminada exitosamente"})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)


# ================================
# BUSCADOR AJAX PARA SELECT2
# ================================
from servicios.rest.gestion.HabitacionesGestionRest import HabitacionesGestionRest
from django.http import JsonResponse
from django.views import View
class HabitacionSearchAjaxView(View):
    def get(self, request):
        q = request.GET.get("q", "").strip().upper()

        api = HabitacionesGestionRest()

        try:
            habitaciones = api.obtener_habitaciones()  # ← aquí ya funciona

            if q:
                habitaciones = [
                    h for h in habitaciones
                    if q in h["IdHabitacion"].upper()
                    or q in h["NombreHabitacion"].upper()
                ]

            return JsonResponse({
                "status": "ok",
                "data": habitaciones[:20]   # máximo 20 resultados
            })

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al buscar habitaciones: {e}"},
                status=500
            )
