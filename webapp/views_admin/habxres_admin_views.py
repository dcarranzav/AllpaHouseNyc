from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.HabxResGestionRest import HabxResGestionRest
from webapp.decorators import admin_required, admin_required_ajax

from django.views import View
from django.http import JsonResponse
from servicios.rest.gestion.HabxResGestionRest import HabxResGestionRest

class HabxResSearchAjaxView(View):
    def get(self, request):
        q = request.GET.get("q", "").strip().upper()

        api = HabxResGestionRest()

        try:
            registros = api.obtener_habxres()

            if q:
                registros = [
                    r for r in registros
                    if q in str(r["IdHabxRes"]).upper()
                       or q in r.get("Descripcion", "").upper()
                ]

            return JsonResponse({
                "status": "ok",
                "data": registros[:20]
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error al buscar HabxRes: {e}"
            }, status=500)

# ============================================================
# VISTA PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class HabxResView(View):
    template_name = "webapp/usuario/administrador/crud/habxres/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTA PAGINADA (20 en 20)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HabxResListAjaxView(View):
    def get(self, request):
        api = HabxResGestionRest()
        try:
            data = api.obtener_habxres()

            page = int(request.GET.get("page", 1))
            per_page = 20

            total = len(data)
            total_pages = (total + per_page - 1) // per_page

            start = (page - 1) * per_page
            end = start + per_page
            data_pag = data[start:end]

            return JsonResponse({
                "status": "ok",
                "page": page,
                "total_pages": total_pages,
                "data": data_pag
            })

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# OBTENER UNO
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class HabxResGetAjaxView(View):
    def get(self, request, id_habxres):
        api = HabxResGestionRest()
        try:
            data = api.obtener_por_id(int(id_habxres))
            return JsonResponse({"status": "ok", "data": data})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class HabxResCreateAjaxView(View):
    def post(self, request):
        api = HabxResGestionRest()

        try:
            idHabxRes = int(request.POST.get("IdHabxRes"))
            idHabitacion = request.POST.get("IdHabitacion")
            idReserva = int(request.POST.get("IdReserva"))

            capacidad = request.POST.get("CapacidadReservaHabxRes")
            capacidad = int(capacidad) if capacidad not in ("", None) else None

            costo = request.POST.get("CostoCalculadoHabxRes")
            costo = float(costo) if costo not in ("", None) else None

            descuento = request.POST.get("DescuentoHabxRes")
            descuento = float(descuento) if descuento not in ("", None) else None

            impuestos = request.POST.get("ImpuestosHabxRes")
            impuestos = float(impuestos) if impuestos not in ("", None) else None

            estado = request.POST.get("EstadoHabxRes") == "true"

            api.crear_habxres(
                idHabxRes,
                idHabitacion,
                idReserva,
                capacidad,
                costo,
                descuento,
                impuestos,
                estado,
            )

            return JsonResponse({"status": "ok", "message": "Habitación por Reserva creado exitosamente"})

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
class HabxResUpdateAjaxView(View):
    def post(self, request, id_habxres):
        api = HabxResGestionRest()

        try:
            idHabxRes = int(id_habxres)
            idHabitacion = request.POST.get("IdHabitacion")
            idReserva = int(request.POST.get("IdReserva"))

            capacidad = request.POST.get("CapacidadReservaHabxRes")
            capacidad = int(capacidad) if capacidad not in ("", None) else None

            costo = request.POST.get("CostoCalculadoHabxRes")
            costo = float(costo) if costo not in ("", None) else None

            descuento = request.POST.get("DescuentoHabxRes")
            descuento = float(descuento) if descuento not in ("", None) else None

            impuestos = request.POST.get("ImpuestosHabxRes")
            impuestos = float(impuestos) if impuestos not in ("", None) else None

            # Obtener el estado actual del registro si no se envía
            estado_txt = request.POST.get("EstadoHabxRes")
            if estado_txt is not None and estado_txt != "":
                estado = estado_txt == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_por_id(idHabxRes)
                estado = registro_actual.get("EstadoHabxRes", True) if registro_actual else True

            api.actualizar_habxres(
                idHabxRes,
                idHabitacion,
                idReserva,
                capacidad,
                costo,
                descuento,
                impuestos,
                estado,
            )

            return JsonResponse({"status": "ok", "message": "Habitación por Reserva actualizado exitosamente"})

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
class HabxResDeleteAjaxView(View):
    def post(self, request, id_habxres):
        api = HabxResGestionRest()
        try:
            api.eliminar_habxres(int(id_habxres))
            return JsonResponse({"status": "ok", "message": "Habitación por Reserva eliminado exitosamente"})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)

@method_decorator(admin_required_ajax, name='dispatch')
class HabxResNextIdAjaxView(View):

    def get(self, request):
        api = HabxResGestionRest()

        try:
            data = api.obtener_habxres()

            # Si no hay registros, empezamos en 1
            if not data:
                return JsonResponse({"next": 1})

            # Extraer IDs numéricos
            ids = [
                int(r.get("IdHabxRes", 0))
                for r in data
                if str(r.get("IdHabxRes")).isdigit()
            ]

            siguiente = max(ids) + 1 if ids else 1

            return JsonResponse({"next": siguiente})

        except Exception:
            # En caso de error devolvemos 1 como valor seguro por defecto
            return JsonResponse({"next": 1})
