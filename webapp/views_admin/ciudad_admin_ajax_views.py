from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from servicios.rest.gestion.CiudadGestionRest import CiudadGestionRest
from requests.exceptions import ConnectionError, Timeout, HTTPError

from webapp.decorators import admin_required, admin_required_ajax
from math import ceil


# ============================================================
# VISTA PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class CiudadView(View):
    template_name = "webapp/usuario/administrador/crud/ciudad/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTADO CON PAGINACIÓN
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class CiudadListAjaxView(View):
    def get(self, request):
        api = CiudadGestionRest()

        try:
            data = api.obtener_ciudades()

            # PAGINACIÓN
            page = int(request.GET.get("page", 1))
            per_page = 20
            total_items = len(data)
            total_pages = ceil(total_items / per_page)

            start = (page - 1) * per_page
            end = start + per_page

            return JsonResponse({
                "status": "ok",
                "data": data[start:end],
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items
            })

        except (ConnectionError, Timeout):
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except HTTPError:
            return JsonResponse({"status": "error", "message": "Error inesperado del servidor remoto"}, status=500)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Ocurrió un error inesperado"}, status=500)


# ============================================================
# OBTENER UNA CIUDAD
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class CiudadGetAjaxView(View):
    def get(self, request, id_ciudad):
        api = CiudadGestionRest()

        try:
            data = api.obtener_ciudad_por_id(id_ciudad)
            return JsonResponse({"status": "ok", "data": data})

        except (ConnectionError, Timeout):
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": str(ve)}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "Ciudad no encontrada"}, status=404)


# ============================================================
# CREAR CIUDAD
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class CiudadCreateAjaxView(View):
    def post(self, request):
        try:
            idCiudad = request.POST.get("IdCiudad")
            idPais = request.POST.get("IdPais")
            nombre = request.POST.get("NombreCiudad")
            estado = request.POST.get("EstadoCiudad") == "true"

            # Validaciones
            if not idCiudad:
                return JsonResponse({"status": "error", "message": "ID Ciudad es requerido"}, status=400)
            if not idPais:
                return JsonResponse({"status": "error", "message": "ID País es requerido"}, status=400)
            if not nombre:
                return JsonResponse({"status": "error", "message": "Nombre Ciudad es requerido"}, status=400)

            api = CiudadGestionRest()
            api.crear_ciudad(int(idCiudad), int(idPais), nombre, estado)

            return JsonResponse({"status": "ok", "message": "Ciudad creada exitosamente"})

        except (ConnectionError, Timeout):
            return JsonResponse({"status": "error", "message": "Error de conexión"}, status=503)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": str(ve)}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo crear la ciudad"}, status=500)


# ============================================================
# ACTUALIZAR CIUDAD
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class CiudadUpdateAjaxView(View):
    def post(self, request, id_ciudad):
        try:
            idPais = request.POST.get("IdPais")
            nombre = request.POST.get("NombreCiudad")
            estado_enviado = request.POST.get("EstadoCiudad")

            if not idPais:
                return JsonResponse({"status": "error", "message": "ID País es requerido"}, status=400)

            if not nombre:
                return JsonResponse({"status": "error", "message": "Nombre Ciudad es requerido"}, status=400)

            api = CiudadGestionRest()

            # Obtener estado actual si no se envía
            if estado_enviado is None:
                registro_actual = api.obtener_ciudad_por_id(id_ciudad)
                estado = registro_actual.get("EstadoCiudad", True)
            else:
                estado = estado_enviado == "true"

            api.actualizar_ciudad(id_ciudad, int(idPais), nombre, estado)

            return JsonResponse({"status": "ok", "message": "Ciudad actualizada exitosamente"})

        except (ConnectionError, Timeout):
            return JsonResponse({"status": "error", "message": "Error de conexión"}, status=503)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": str(ve)}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo actualizar la ciudad"}, status=500)


# ============================================================
# ELIMINAR CIUDAD
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class CiudadDeleteAjaxView(View):
    def post(self, request, id_ciudad):
        api = CiudadGestionRest()

        try:
            api.eliminar_ciudad(id_ciudad)
            return JsonResponse({"status": "ok", "message": "Ciudad eliminada exitosamente"})

        except (ConnectionError, Timeout):
            return JsonResponse({"status": "error", "message": "Error de conexión"}, status=503)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar la ciudad. Puede estar en uso"}, status=500)
