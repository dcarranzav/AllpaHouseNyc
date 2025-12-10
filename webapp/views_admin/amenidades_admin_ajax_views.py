from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from requests.exceptions import ConnectionError, Timeout, HTTPError

from servicios.rest.gestion.AmenidadesGestionRest import AmenidadesGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VISTA HTML (CARGA LA PÁGINA)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class AmenidadesView(View):
    template_name = "webapp/usuario/administrador/crud/amenidad/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR AMENIDADES (AJAX)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class AmenidadesListAjaxView(View):
    def get(self, request):
        api = AmenidadesGestionRest()
        try:
            page = int(request.GET.get("page", 1))
            page_size = 20

            data = api.obtener_amenidades()

            # Asegurar lista
            if not isinstance(data, list):
                data = []

            total = len(data)
            total_pages = (total + page_size - 1) // page_size or 1

            start = (page - 1) * page_size
            end = start + page_size

            return JsonResponse({
                "status": "ok",
                "data": data[start:end],
                "page": page,
                "total_pages": total_pages,
                "total_records": total
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error al listar amenidades: {str(e)}"
            }, status=500)


# ============================================================
# CREAR AMENIDAD
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class AmenidadesCreateAjaxView(View):
    def post(self, request):

        idA = request.POST.get("IdAmenidad")
        nombre = request.POST.get("NombreAmenidad")
        estado = request.POST.get("EstadoAmenidad") == "true"

        if not idA:
            return JsonResponse({"status": "error", "message": "ID Amenidad es requerido"}, status=400)

        if not nombre:
            return JsonResponse({"status": "error", "message": "Nombre Amenidad es requerido"}, status=400)

        try:
            api = AmenidadesGestionRest()
            api.crear_amenidad(
                id_amenidad=int(idA),
                nombre=nombre,
                estado=estado
            )
            return JsonResponse({"status": "ok", "message": "Amenidad creada correctamente."})

        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo crear la amenidad"}, status=500)


# ============================================================
# OBTENER AMENIDAD (PARA EDITAR)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class AmenidadesGetAjaxView(View):
    def get(self, request, id):
        api = AmenidadesGestionRest()
        try:
            data = api.obtener_amenidad_por_id(id)
            return JsonResponse({"status": "ok", "data": data})

        except Exception:
            return JsonResponse({"status": "error", "message": "Error al obtener la amenidad"}, status=404)


# ============================================================
# ACTUALIZAR AMENIDAD
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class AmenidadesUpdateAjaxView(View):
    def post(self, request, id):

        nombre = request.POST.get("NombreAmenidad")
        estado_raw = request.POST.get("EstadoAmenidad")

        if not nombre:
            return JsonResponse({"status": "error", "message": "Nombre Amenidad es requerido"}, status=400)

        api = AmenidadesGestionRest()

        try:
            # Si enviaron el estado (checkbox)
            if estado_raw is not None:
                estado = estado_raw == "true"
            else:
                # Recuperamos el estado actual
                registro = api.obtener_amenidad_por_id(id)
                estado = registro.get("EstadoAmenidad", True)

            api.actualizar_amenidad(
                id_amenidad=id,
                nombre=nombre,
                estado=estado
            )

            return JsonResponse({"status": "ok", "message": "Amenidad actualizada correctamente."})

        except Exception:
            return JsonResponse({"status": "error", "message": "Error al actualizar"}, status=500)


# ============================================================
# ELIMINAR AMENIDAD
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class AmenidadesDeleteAjaxView(View):
    def post(self, request, id):

        api = AmenidadesGestionRest()

        try:
            api.eliminar_amenidad(id)
            return JsonResponse({"status": "ok", "message": "Amenidad eliminada correctamente."})

        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar (puede estar en uso)"}, status=500)


@method_decorator(admin_required_ajax, name='dispatch')
class AmenidadesNextIdAjaxView(View):

    def get(self, request):
        api = AmenidadesGestionRest()

        try:
            data = api.obtener_amenidades()

            if not data:
                return JsonResponse({"next": 1})

            # Extraer IDs existentes
            ids = [
                int(a.get("IdAmenidad", 0))
                for a in data
                if str(a.get("IdAmenidad")).isdigit()
            ]

            siguiente = max(ids) + 1 if ids else 1

            return JsonResponse({"next": siguiente})

        except Exception:
            return JsonResponse({"next": 1})
