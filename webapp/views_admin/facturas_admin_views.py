from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from servicios.rest.gestion.FacturasGestionRest import FacturasGestionRest
from webapp.decorators import admin_required, admin_required_ajax

@method_decorator(admin_required, name='dispatch')
class FacturasView(View):
    template_name = "webapp/usuario/administrador/crud/facturas/index.html"

    def get(self, request):
        """
        GET maneja:
        - Listado general
        - Cargar registro para editar (?edit=ID)
        """
        api = FacturasGestionRest()

        # ¿Modificar?
        edit_id = request.GET.get("edit")
        obj = None

        if edit_id:
            try:
                obj = api.obtener_por_id(int(edit_id))
                if not obj:
                    messages.error(request, "Factura no encontrada.")
            except Exception as e:
                messages.error(request, f"Error al cargar factura: {e}")

        # Listado general
        try:
            lista = api.obtener_facturas()
        except Exception as e:
            messages.error(request, f"Error al listar facturas: {e}")
            lista = []

        return render(request, self.template_name, {
            "lista": lista,
            "editar": obj
        })

    def post(self, request):
        """
        POST maneja:
        - Crear
        - Actualizar (?update=ID)
        - Eliminar (?delete=ID)
        """
        api = FacturasGestionRest()

        # 🔥 ELIMINAR
        delete_id = request.GET.get("delete")
        if delete_id:
            try:
                api.eliminar_factura(int(delete_id))
                messages.success(request, "Factura eliminada correctamente.")
            except Exception as e:
                messages.error(request, f"Error al eliminar: {e}")
            return redirect(reverse("admin_facturas"))

        # 🔥 ACTUALIZAR
        update_id = request.GET.get("update")
        if update_id:
            try:
                id_reserva = int(request.POST.get("idReserva"))
                subtotal = request.POST.get("subtotal")
                descuento = request.POST.get("descuento")
                impuesto = request.POST.get("impuesto")
                total = request.POST.get("total")
                url_pdf = request.POST.get("urlPdf")

                api.actualizar_factura(
                    int(update_id),
                    id_reserva,
                    float(subtotal) if subtotal else None,
                    float(descuento) if descuento else None,
                    float(impuesto) if impuesto else None,
                    float(total) if total else None,
                    url_pdf
                )

                messages.success(request, "Factura actualizada correctamente.")
            except Exception as e:
                messages.error(request, f"Error al actualizar: {e}")

            return redirect(reverse("admin_facturas"))

        # 🔥 CREAR
        try:
            id_factura = int(request.POST.get("idFactura"))
            id_reserva = int(request.POST.get("idReserva"))
            subtotal = request.POST.get("subtotal")
            descuento = request.POST.get("descuento")
            impuesto = request.POST.get("impuesto")
            total = request.POST.get("total")
            url_pdf = request.POST.get("urlPdf")

            api.crear_factura(
                id_factura,
                id_reserva,
                float(subtotal) if subtotal else None,
                float(descuento) if descuento else None,
                float(impuesto) if impuesto else None,
                float(total) if total else None,
                url_pdf
            )

            messages.success(request, "Factura creada correctamente.")
        except Exception as e:
            messages.error(request, f"Error al crear factura: {e}")

        return redirect(reverse("admin_facturas"))

