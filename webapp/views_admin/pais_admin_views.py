from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.PaisGestionRest import PaisGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class PaisView(View):
    template_name = "webapp/usuario/administrador/crud/pais/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTA (Paginar 20)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class PaisListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = PaisGestionRest()

        try:
            data = api.obtener_paises()

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


# ============================================================
# OBTENER UNO
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class PaisGetAjaxView(View):
    def get(self, request, id_pais):
        api = PaisGestionRest()
        try:
            data = api.obtener_pais_por_id(id_pais)
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


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PaisCreateAjaxView(View):
    def post(self, request):
        api = PaisGestionRest()
        try:
            api.crear_pais(
                id_pais=int(request.POST.get("IdPais")),
                nombre_pais=request.POST.get("NombrePais"),
                estado_pais=request.POST.get("EstadoPais") == "true"
            )
            return JsonResponse({"status": "ok", "message": "País creado exitosamente"})
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


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PaisUpdateAjaxView(View):
    def post(self, request, id_pais):
        api = PaisGestionRest()
        try:
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoPais")
            if estado_enviado is not None:
                estado_pais = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_pais_por_id(id_pais)
                estado_pais = registro_actual.get("EstadoPais", True)
            
            api.actualizar_pais(
                id_pais=int(id_pais),
                nombre_pais=request.POST.get("NombrePais"),
                estado_pais=estado_pais
            )
            return JsonResponse({"status": "ok", "message": "País actualizado exitosamente"})
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


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PaisDeleteAjaxView(View):
    def post(self, request, id_pais):
        api = PaisGestionRest()
        try:
            api.eliminar_pais(id_pais)
            return JsonResponse({"status": "ok", "message": "País eliminado exitosamente"})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)

@method_decorator(admin_required_ajax, name="dispatch")
class PaisNextIdAjaxView(View):
    """
    Devuelve el siguiente ID disponible para PAIS.
    Endpoint: /admin/pais/next-id/
    Respuesta: {"next": 10}
    """

    def get(self, request):
        api = PaisGestionRest()

        try:
            data = api.obtener_paises() or []

            # Aseguramos lista
            if not isinstance(data, list):
                data = [data]

            ids = []
            for p in data:
                raw_id = p.get("IdPais")
                try:
                    ids.append(int(raw_id))
                except (TypeError, ValueError):
                    continue

            siguiente = max(ids) + 1 if ids else 1

            return JsonResponse({"next": siguiente})
        except Exception:
            # Si algo falla, devolvemos 1 para no romper el front
            return JsonResponse({"next": 1})
