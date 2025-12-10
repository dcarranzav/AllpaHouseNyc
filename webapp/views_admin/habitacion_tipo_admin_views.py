# webapp/views_admin/views_tipo_habitacion.py
from pprint import pprint

from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.TipoHabitacionGestionRest import TipoHabitacionGestionRest
from webapp.decorators import admin_required, admin_required_ajax


@method_decorator(admin_required, name='dispatch')
class TipoHabitacionView(View):
    template_name = "webapp/usuario/administrador/crud/tipo_habitacion/index.html"

    def get(self, request):
        return render(request, self.template_name)


@method_decorator(admin_required_ajax, name='dispatch')
class TipoHabitacionListAjaxView(View):
    def get(self, request):
        api = TipoHabitacionGestionRest()
        try:
            data = api.obtener_tipos()
            page_number = int(request.GET.get("page", 1))
            paginator = Paginator(data, 20)
            page = paginator.get_page(page_number)

            return JsonResponse({
                "status": "ok",
                "data": list(page),
                "page": page.number,
                "total_pages": paginator.num_pages
            })

        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
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


@method_decorator(admin_required_ajax, name='dispatch')
class TipoHabitacionGetAjaxView(View):
    def get(self, request, id_tipo):
        api = TipoHabitacionGestionRest()
        try:
            data = api.obtener_tipo_por_id(id_tipo)
            return JsonResponse({"status": "ok", "data": data})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo obtener el registro. Verifique que el ID sea correcto"}, status=404)


@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class TipoHabitacionCreateAjaxView(View):
    def post(self, request):
        api = TipoHabitacionGestionRest()
        try:
            dto = {
                "idTipoHabitacion": int(request.POST.get("id_tipo")),
                "nombreTipoHabitacion": request.POST.get("nombre"),
                "descripcionTipoHabitacion": request.POST.get("descripcion"),
                "estadoTipoHabitacion": request.POST.get("estado") == "true"
            }

            api.crear_tipo(dto)
            return JsonResponse({"status": "ok", "message": "Tipo de Habitación creado exitosamente"})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo crear el registro. Verifique los datos ingresados"}, status=500)


@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class TipoHabitacionUpdateAjaxView(View):
    def post(self, request, id_tipo):
        api = TipoHabitacionGestionRest()
        pprint(request.POST)
        try:
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("estado")
            if estado_enviado is not None:
                estado = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_tipo_por_id(id_tipo)
                estado = registro_actual.get("estadoTipoHabitacion", True)
            
            dto = {
                "idTipoHabitacion": id_tipo,
                "NombreHabitacion": request.POST.get("nombre"),
                "descripcionTipoHabitacion": request.POST.get("descripcion"),
                "estadoTipoHabitacion": estado
            }

            api.actualizar_tipo(id_tipo, dto)
            return JsonResponse({"status": "ok", "message": "Tipo de Habitación actualizado exitosamente"})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo actualizar el registro. Verifique los datos"}, status=500)


@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class TipoHabitacionDeleteAjaxView(View):
    def post(self, request, id_tipo):
        api = TipoHabitacionGestionRest()
        try:
            api.eliminar_tipo(id_tipo)
            return JsonResponse({"status": "ok", "message": "Tipo de Habitación eliminado exitosamente"})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)


# ============================================================
# OBTENER SIGUIENTE ID (NEXT-ID)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class TipoHabitacionNextIdAjaxView(View):
    def get(self, request):
        api = TipoHabitacionGestionRest()
        try:
            tipos = api.obtener_tipos()   # lista de dicts
            max_id = 0

            if isinstance(tipos, list):
                for t in tipos:
                    # intentamos con varias claves posibles
                    raw = (
                        t.get("IdTipoHabitacion")
                        or t.get("idTipoHabitacion")
                        or t.get("id_tipoHabitacion")
                    )
                    try:
                        val = int(raw)
                    except (TypeError, ValueError):
                        continue

                    if val > max_id:
                        max_id = val

            next_id = max_id + 1

            return JsonResponse({
                "status": "ok",
                "next": next_id,    # por compatibilidad
                "next_id": next_id  # nombre más explícito
            })

        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al calcular siguiente IdTipoHabitacion: {e}"
                },
                status=500
            )
