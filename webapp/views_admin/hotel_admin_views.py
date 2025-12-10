from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.HotelGestionRest import HotelGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class HotelView(View):
    template_name = "webapp/usuario/administrador/crud/hotel/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR 20 EN 20
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HotelListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = HotelGestionRest()

        try:
            data = api.obtener_hoteles()

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
class HotelGetAjaxView(View):
    def get(self, request, id_hotel):
        api = HotelGestionRest()

        try:
            data = api.obtener_hotel_por_id(int(id_hotel))
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
class HotelCreateAjaxView(View):
    def post(self, request):

        try:
            id_hotel = request.POST.get("IdHotel")
            nombre_hotel = request.POST.get("NombreHotel")
            
            if not id_hotel:
                return JsonResponse({"status": "error", "message": "ID de Hotel es requerido"}, status=400)
            
            if not nombre_hotel:
                return JsonResponse({"status": "error", "message": "Nombre del Hotel es requerido"}, status=400)

            api = HotelGestionRest()
            api.crear_hotel(
                id_hotel=int(id_hotel),
                nombre_hotel=nombre_hotel,
                estado_hotel=request.POST.get("EstadoHotel") == "true"
            )
            return JsonResponse({"status": "ok", "message": "Hotel creado exitosamente"})

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
class HotelUpdateAjaxView(View):
    def post(self, request, id_hotel):

        try:
            nombre_hotel = request.POST.get("NombreHotel")
            
            if not nombre_hotel:
                return JsonResponse({"status": "error", "message": "Nombre del Hotel es requerido"}, status=400)

            api = HotelGestionRest()
            
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoHotel")
            if estado_enviado is not None:
                estado_hotel = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_hotel_por_id(id_hotel)
                estado_hotel = registro_actual.get("EstadoHotel", True)
            
            api.actualizar_hotel(
                id_hotel=int(id_hotel),
                nombre_hotel=nombre_hotel,
                estado_hotel=estado_hotel
            )
            return JsonResponse({"status": "ok", "message": "Hotel actualizado exitosamente"})

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
class HotelDeleteAjaxView(View):
    def post(self, request, id_hotel):

        api = HotelGestionRest()

        try:
            api.eliminar_hotel(int(id_hotel))
            return JsonResponse({"status": "ok", "message": "Hotel eliminado exitosamente"})

        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)

# ============================================================
# OBTENER SIGUIENTE ID HOTEL
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HotelNextIdAjaxView(View):
    def get(self, request):
        api = HotelGestionRest()
        try:
            # Traemos todos los hoteles
            hoteles = api.obtener_hoteles() or []

            # Extraemos los IdHotel como enteros (ignorando los que no se puedan convertir)
            ids = []
            for h in hoteles:
                try:
                    # por si el REST usa otra clave, intentamos ambas
                    raw_id = h.get("IdHotel") or h.get("id_hotel")
                    if raw_id is not None:
                        ids.append(int(raw_id))
                except (TypeError, ValueError):
                    continue

            # Si no hay registros, empezamos en 1
            if not ids:
                next_id = 1
            else:
                next_id = max(ids) + 1

            return JsonResponse({
                "status": "ok",
                "next_id": next_id
            })

        except ConnectionError:
            return JsonResponse(
                {"status": "error",
                 "message": "No se pudo conectar con el servidor. Verifique su conexión"},
                status=503
            )
        except Timeout:
            return JsonResponse(
                {"status": "error",
                 "message": "El servidor no responde. Intente nuevamente"},
                status=504
            )
        except Exception:
            return JsonResponse(
                {"status": "error",
                 "message": "No se pudo obtener el siguiente ID de hotel."},
                status=500
            )
