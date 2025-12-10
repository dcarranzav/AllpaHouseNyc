from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from webapp.decorators import admin_required, admin_required_ajax
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from servicios.rest.gestion.MetodoPagoGestionRest import MetodoPagoGestionRest
from webapp.decorators import admin_required_ajax

# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class MetodoPagoView(View):
    template_name = "webapp/usuario/administrador/crud/metodoPago/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR (20 EN 20)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class MetodoPagoListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = MetodoPagoGestionRest()

        try:
            data = api.obtener_metodos_pago()

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
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# OBTENER UNO
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class MetodoPagoGetAjaxView(View):
    def get(self, request, id_metodo):
        api = MetodoPagoGestionRest()
        try:
            data = api.obtener_metodo_pago_por_id(int(id_metodo))
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
class MetodoPagoCreateAjaxView(View):
    def post(self, request):
        api = MetodoPagoGestionRest()
        try:
            api.crear_metodo_pago(
                id_metodo=int(request.POST.get("IdMetodoPago")),
                nombre_metodo=request.POST.get("NombreMetodoPago"),
                estado_metodo=request.POST.get("EstadoMetodoPago") == "true"
            )
            return JsonResponse({"status": "ok", "message": "Método de Pago creado exitosamente"})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class MetodoPagoUpdateAjaxView(View):
    def post(self, request, id_metodo):
        api = MetodoPagoGestionRest()
        try:
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoMetodoPago")
            if estado_enviado is not None:
                estado_metodo = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_metodo_pago_por_id(id_metodo)
                estado_metodo = registro_actual.get("EstadoMetodoPago", True) if registro_actual else True
            
            api.actualizar_metodo_pago(
                id_metodo=int(id_metodo),
                nombre_metodo=request.POST.get("NombreMetodoPago"),
                estado_metodo=estado_metodo
            )
            return JsonResponse({"status": "ok", "message": "Método de Pago actualizado exitosamente"})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class MetodoPagoDeleteAjaxView(View):
    def post(self, request, id_metodo):
        api = MetodoPagoGestionRest()
        try:
            api.eliminar_metodo_pago(int(id_metodo))
            return JsonResponse({"status": "ok", "message": "Método de Pago eliminado exitosamente"})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )






@method_decorator(admin_required_ajax, name="dispatch")
class MetodoPagoSearchAjaxView(View):
    """
    Buscador AJAX para Select2 de Métodos de Pago.
    Endpoint: /admin/metodo-pago/search/?q=visa
    """

    def get(self, request):
        q = (request.GET.get("q", "") or "").strip().upper()

        api = MetodoPagoGestionRest()

        try:
            # Debe devolver una lista de dicts, por ejemplo:
            # [
            #   {"IdMetodoPago": 1, "NombreMetodoPago": "Visa", ...},
            #   ...
            # ]
            metodos = api.obtener_metodos_pago()  # ajusta al nombre real del método

            if not isinstance(metodos, list):
                metodos = []

            if q:
                filtrados = []
                for m in metodos:
                    id_str = str(m.get("IdMetodoPago", "")).upper()
                    nombre = (m.get("NombreMetodoPago") or "").upper()
                    descripcion = (m.get("DescripcionMetodoPago") or "").upper()

                    if (
                        q in id_str
                        or q in nombre
                        or q in descripcion
                    ):
                        filtrados.append(m)
                metodos = filtrados

            return JsonResponse({
                "status": "ok",
                "data": metodos[:20]  # máximo 20 resultados
            })

        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al buscar métodos de pago: {e}"
                },
                status=500
            )
