from pprint import pprint

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

from math import ceil

from servicios.rest.gestion.DescuentosGestionRest import DescuentosGestionRest
from webapp.decorators import admin_required, admin_required_ajax


@method_decorator(admin_required, name='dispatch')
class DescuentoView(View):
    template_name = "webapp/usuario/administrador/crud/descuento/index.html"

    def get(self, request):
        return render(request, self.template_name)


@method_decorator(admin_required_ajax, name='dispatch')
class DescuentoListAjaxView(View):
    def get(self, request):
        api = DescuentosGestionRest()
        try:
            data = api.obtener_descuentos()   # <- que devuelva TODOS, activos e inactivos

            # paginación...
            page = int(request.GET.get("page", 1))
            page_size = 20
            total = len(data)
            total_pages = (total + page_size - 1) // page_size
            start = (page - 1) * page_size
            end = start + page_size
            pagina_data = data[start:end]

            return JsonResponse({
                "status": "ok",
                "data": pagina_data,
                "page": page,
                "total_pages": total_pages
            })

        except Exception:
            return JsonResponse({"status": "error", "message": "Error al cargar descuentos"}, status=500)

@method_decorator(admin_required_ajax, name='dispatch')
class DescuentoGetAjaxView(View):
    def get(self, request, id_descuento):

        api = DescuentosGestionRest()
        try:
            data = api.obtener_descuento_por_id(id_descuento)
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
class DescuentoCreateAjaxView(View):
    def post(self, request):
        try:
            pprint(request.POST)
            id_descuento = request.POST.get("IdDescuento")
            nombre_descuento = request.POST.get("NombreDescuento")
            
            if not id_descuento:
                return JsonResponse({"status": "error", "message": "ID Descuento es requerido"}, status=400)
            
            if not nombre_descuento:
                return JsonResponse({"status": "error", "message": "Nombre Descuento es requerido"}, status=400)
            valor = float(request.POST.get("ValorDescuento"))
            fechaInicio = request.POST.get("FechaInicioDescuento")
            fechaFin = request.POST.get("FechaInicioDescuento")
            estado = request.POST.get("EstadoDescuento") == "true"
            print(f"Datos enviados: id_descuento: {id_descuento} "
                  f"nombre_descuento: {nombre_descuento} "
                  f"valor: {valor} "
                  f"fechaInicio: {fechaInicio} "
                  f"fechaFin: {fechaFin} "
                  f"estado: {estado}")
            api = DescuentosGestionRest()
            api.crear_descuento(int(id_descuento), nombre_descuento, valor, fechaInicio, fechaFin, estado)
            return JsonResponse({"status": "ok", "message": "Descuento creado exitosamente"})

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
class DescuentoUpdateAjaxView(View):
    def post(self, request, id_descuento):
        try:
            nombre_descuento = request.POST.get("NombreDescuento")
            
            if not nombre_descuento:
                return JsonResponse({"status": "error", "message": "Nombre Descuento es requerido"}, status=400)

            valor = float(request.POST.get("ValorDescuento"))
            fechaInicio = request.POST.get("FechaInicioDescuento")
            fechaFin = request.POST.get("FechaFinDescuento")
            
            api = DescuentosGestionRest()
            
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoDescuento")
            if estado_enviado is not None:
                estado = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_descuento_por_id(id_descuento)
                estado = registro_actual.get("EstadoDescuento", True) if registro_actual else True
            api.actualizar_descuento(id_descuento, nombre_descuento, valor, fechaInicio, fechaFin, estado)
            return JsonResponse({"status": "ok", "message": "Descuento actualizado exitosamente"})

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
class DescuentoDeleteAjaxView(View):
    def post(self, request, id_descuento):
        api = DescuentosGestionRest()
        try:
            api.eliminar_descuento(id_descuento)
            return JsonResponse({"status": "ok", "message": "Descuento eliminado exitosamente"})

        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)

@method_decorator(admin_required_ajax, name='dispatch')
class DescuentoNextIdAjaxView(View):

    def get(self, request):

        api = DescuentosGestionRest()

        try:
            data = api.obtener_descuentos()

            if not data:
                return JsonResponse({"next": 1})

            # Extraer solo IDs válidos
            ids = [
                int(d.get("IdDescuento", 0))
                for d in data
                if str(d.get("IdDescuento")).isdigit()
            ]

            siguiente = max(ids) + 1 if ids else 1

            return JsonResponse({"next": siguiente})

        except Exception:
            return JsonResponse({"next": 1})
