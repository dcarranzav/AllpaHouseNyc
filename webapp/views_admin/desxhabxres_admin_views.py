# desxhabxres_admin_views.py

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from math import ceil

from servicios.rest.gestion.DesxHabxResGestionRest import DesxHabxResGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class DesxHabxResView(View):
    template_name = "webapp/usuario/administrador/crud/desxhabxres/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTA PAGINADA
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class DesxHabxResListAjaxView(View):
    def get(self, request):

        api = DesxHabxResGestionRest()

        try:
            data = api.obtener_desxhabxres()

            # ----- PAGINACIÓN -----
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

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error al cargar lista DesxHabxRes: {e}"
            }, status=500)


# ============================================================
# OBTENER UNO POR ID DOBLE
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class DesxHabxResGetAjaxView(View):
    def get(self, request, id_descuento, id_habxres):

        api = DesxHabxResGestionRest()

        try:
            data = api.obtener_por_id(int(id_descuento), int(id_habxres))

            if not data:
                return JsonResponse({
                    "status": "error",
                    "message": "Registro no encontrado"
                }, status=404)

            return JsonResponse({"status": "ok", "data": data})

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error al obtener registro: {e}"
            }, status=500)


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class DesxHabxResCreateAjaxView(View):
    def post(self, request):

        try:
            idDescuento = int(request.POST.get("IdDescuento"))
            idHabxRes = int(request.POST.get("IdHabxRes"))

            monto_raw = request.POST.get("MontoDesxHabxRes")
            monto = float(monto_raw) if monto_raw else None

            estado = request.POST.get("EstadoDesxHabxRes") == "true"

            api = DesxHabxResGestionRest()
            api.crear_desxhabxres(idDescuento, idHabxRes, monto, estado)

            return JsonResponse({
                "status": "ok",
                "message": "Descuento por Habitación creado exitosamente"
            })

        except ValueError as ve:
            return JsonResponse({
                "status": "error",
                "message": f"Datos inválidos: {ve}"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error al crear registro: {e}"
            }, status=500)


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class DesxHabxResUpdateAjaxView(View):
    def post(self, request, id_descuento, id_habxres):

        api = DesxHabxResGestionRest()

        try:
            monto_raw = request.POST.get("MontoDesxHabxRes")
            monto = float(monto_raw) if monto_raw else None

            estado_raw = request.POST.get("EstadoDesxHabxRes")

            if estado_raw is not None:
                estado = estado_raw == "true"
            else:
                registro = api.obtener_por_id(int(id_descuento), int(id_habxres))
                estado = registro.get("estadoDesxHabxRes", True)

            api.actualizar_desxhabxres(int(id_descuento), int(id_habxres), monto, estado)

            return JsonResponse({
                "status": "ok",
                "message": "Registro actualizado exitosamente"
            })

        except ValueError as ve:
            return JsonResponse({
                "status": "error",
                "message": f"Datos inválidos: {ve}"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error al actualizar: {e}"
            }, status=500)


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class DesxHabxResDeleteAjaxView(View):
    def post(self, request, id_descuento, id_habxres):

        api = DesxHabxResGestionRest()

        try:
            api.eliminar_desxhabxres(int(id_descuento), int(id_habxres))

            return JsonResponse({
                "status": "ok",
                "message": "Registro eliminado exitosamente"
            })

        except ValueError as ve:
            return JsonResponse({
                "status": "error",
                "message": f"Datos inválidos: {ve}"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"No se pudo eliminar el registro: {e}"
            }, status=500)
