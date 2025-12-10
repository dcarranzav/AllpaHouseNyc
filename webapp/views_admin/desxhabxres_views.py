from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


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
# LISTA PAGINADA (20 en 20)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class DesxHabxResListAjaxView(View):
    def get(self, request):
        api = DesxHabxResGestionRest()

        try:
            data = api.obtener_desxhabxres()

            # Paginación manual
            page = int(request.GET.get("page", 1))
            por_pagina = 20

            total = len(data)
            total_pages = (total + por_pagina - 1) // por_pagina

            inicio = (page - 1) * por_pagina
            fin = inicio + por_pagina

            data_paginada = data[inicio:fin]

            return JsonResponse({
                "status": "ok",
                "page": page,
                "total_pages": total_pages,
                "data": data_paginada
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error al cargar lista de descuento por habitacións: {str(e)}"}, status=400)


# ============================================================
# OBTENER UNO
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class DesxHabxResGetAjaxView(View):
    def get(self, request, id_descuento, id_habxres):
        api = DesxHabxResGestionRest()
        try:
            data = api.obtener_por_id(int(id_descuento), int(id_habxres))
            return JsonResponse({"status": "ok", "data": data})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error al obtener descuento por habitación: {str(e)}"}, status=400)


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class DesxHabxResCreateAjaxView(View):
    def post(self, request):

        idDescuento = int(request.POST.get("IdDescuento"))
        idHabxRes = int(request.POST.get("IdHabxRes"))

        monto = request.POST.get("MontoDesxHabxRes")
        monto = float(monto) if monto not in (None, "") else None

        estado = request.POST.get("EstadoDesxHabxRes") == "true"

        api = DesxHabxResGestionRest()

        try:
            api.crear_desxhabxres(idDescuento, idHabxRes, monto, estado)
            return JsonResponse({"status": "ok", "message": "Descuento por Habitación creado exitosamente"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error al crear descuento por habitación: {str(e)}"}, status=400)


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class DesxHabxResUpdateAjaxView(View):
    def post(self, request, id_descuento, id_habxres):

        monto = request.POST.get("MontoDesxHabxRes")
        monto = float(monto) if monto not in (None, "") else None

        # Obtener el estado actual del registro si no se envía
        estado_enviado = request.POST.get("EstadoDesxHabxRes")
        if estado_enviado is not None:
            estado = estado_enviado == "true"
        else:
            # Obtener el estado actual del registro
            api = DesxHabxResGestionRest()
            registro_actual = api.obtener_desxhabxres_por_id(int(id_descuento), int(id_habxres))
            estado = registro_actual.get("EstadoDesxHabxRes", True) if registro_actual else True

        api = DesxHabxResGestionRest()

        try:
            api.actualizar_desxhabxres(int(id_descuento), int(id_habxres), monto, estado)
            return JsonResponse({"status": "ok", "message": "Descuento por Habitación actualizado exitosamente"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error al actualizar descuento por habitación: {str(e)}"}, status=400)


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class DesxHabxResDeleteAjaxView(View):
    def post(self, request, id_descuento, id_habxres):

        api = DesxHabxResGestionRest()

        try:
            api.eliminar_desxhabxres(int(id_descuento), int(id_habxres))
            return JsonResponse({"status": "ok", "message": "Descuento por Habitación eliminado exitosamente"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error al eliminar descuento por habitación: {str(e)}"}, status=400)

