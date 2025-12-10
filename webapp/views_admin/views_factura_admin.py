# webapp/views_admin/views_factura_admin.py

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation

from servicios.rest.gestion.FacturasGestionRest import FacturasGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VISTA PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name="dispatch")
class FacturaView(View):
    """
    Renderiza el template principal del CRUD de facturas.
    """
    template_name = "webapp/usuario/administrador/crud/factura/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR (20 en 20)
# ============================================================
@method_decorator(admin_required_ajax, name="dispatch")
class FacturaListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = FacturasGestionRest()

        try:
            data = api.obtener_facturas() or []

            paginator = Paginator(data, page_size)
            page_obj = paginator.get_page(page)

            return JsonResponse({
                "status": "ok",
                "data": list(page_obj),
                "page": page_obj.number,
                "total_pages": paginator.num_pages
            })

        except ConnectionError as e:
            return JsonResponse(
                {"status": "error",
                 "message": str(e)},
                status=503
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error",
                 "message": f"Error al cargar la lista de facturas: {e}"},
                status=500
            )


# ============================================================
# OBTENER UNA FACTURA
# ============================================================
@method_decorator(admin_required_ajax, name="dispatch")
class FacturaGetAjaxView(View):
    def get(self, request, id_factura):
        api = FacturasGestionRest()

        try:
            data = api.obtener_por_id(int(id_factura))
            if data is None:
                return JsonResponse(
                    {"status": "error", "message": "Factura no encontrada"},
                    status=404
                )

            return JsonResponse({"status": "ok", "data": data})

        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": str(ve)},
                status=400
            )
        except ConnectionError as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=503
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error",
                 "message": f"No se pudo obtener la factura: {e}"},
                status=500
            )


# ============================================================
# CREAR FACTURA
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name="dispatch")
class FacturaCreateAjaxView(View):
    def post(self, request):
        api = FacturasGestionRest()

        try:
            id_factura = request.POST.get("IdFactura")
            id_reserva = request.POST.get("IdReserva")

            if not id_factura:
                return JsonResponse(
                    {"status": "error", "message": "IdFactura es obligatorio."},
                    status=400
                )
            if not id_reserva:
                return JsonResponse(
                    {"status": "error", "message": "IdReserva es obligatorio."},
                    status=400
                )

            # Campos numéricos opcionales
            def to_float(val):
                return float(val) if val not in (None, "",) else None

            subtotal  = to_float(request.POST.get("Subtotal"))
            descuento = to_float(request.POST.get("Descuento"))
            impuesto  = to_float(request.POST.get("Impuesto"))
            total     = to_float(request.POST.get("Total"))

            url_pdf = request.POST.get("UrlPdf") or request.POST.get("UrlPDF") or None

            api.crear_factura(
                id_factura=int(id_factura),
                id_reserva=int(id_reserva),
                subtotal=subtotal,
                descuento=descuento,
                impuesto=impuesto,
                total=total,
                url_pdf=url_pdf
            )

            return JsonResponse(
                {"status": "ok", "message": "Factura creada exitosamente"}
            )

        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400
            )
        except ConnectionError as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=503
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error",
                 "message": f"No se pudo crear la factura: {e}"},
                status=500
            )


# ============================================================
# ACTUALIZAR FACTURA
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name="dispatch")
class FacturaUpdateAjaxView(View):
    def post(self, request, id_factura):
        api = FacturasGestionRest()

        try:
            id_reserva = request.POST.get("IdReserva")
            if not id_reserva:
                return JsonResponse(
                    {"status": "error", "message": "IdReserva es obligatorio."},
                    status=400
                )

            def to_float(val):
                return float(val) if val not in (None, "",) else None

            subtotal  = to_float(request.POST.get("Subtotal"))
            descuento = to_float(request.POST.get("Descuento"))
            impuesto  = to_float(request.POST.get("Impuesto"))
            total     = to_float(request.POST.get("Total"))

            url_pdf = request.POST.get("UrlPdf") or request.POST.get("UrlPDF") or None

            updated = api.actualizar_factura(
                id_factura=int(id_factura),
                id_reserva=int(id_reserva),
                subtotal=subtotal,
                descuento=descuento,
                impuesto=impuesto,
                total=total,
                url_pdf=url_pdf
            )

            if updated is None:
                return JsonResponse(
                    {"status": "error", "message": "Factura no encontrada"},
                    status=404
                )

            return JsonResponse(
                {"status": "ok", "message": "Factura actualizada exitosamente"}
            )

        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400
            )
        except ConnectionError as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=503
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error",
                 "message": f"No se pudo actualizar la factura: {e}"},
                status=500
            )


# ============================================================
# ELIMINAR FACTURA (lógico)
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name="dispatch")
class FacturaDeleteAjaxView(View):
    def post(self, request, id_factura):
        api = FacturasGestionRest()

        try:
            ok = api.eliminar_factura(int(id_factura))

            if not ok:
                return JsonResponse(
                    {"status": "error", "message": "Factura no encontrada"},
                    status=404
                )

            return JsonResponse(
                {"status": "ok", "message": "Factura eliminada exitosamente"}
            )

        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400
            )
        except ConnectionError as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=503
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error",
                 "message": f"No se pudo eliminar la factura: {e}"},
                status=500
            )


# ============================================================
# BUSCADOR AJAX PARA SELECT2 (para pagos, etc.)
# ============================================================
@method_decorator(admin_required_ajax, name="dispatch")
class FacturaSearchAjaxView(View):
    """
    Endpoint para Select2:
    /admin/factura/search/?q=100
    Devuelve lista resumida de facturas para usar en combos.
    """

    def get(self, request):
        q = (request.GET.get("q", "") or "").strip().upper()
        api = FacturasGestionRest()

        try:
            items = api.obtener_facturas() or []

            if q:
                filtrados = []
                for f in items:
                    # Soportar ambas notaciones de nombres
                    id_factura = f.get("IdFactura") or f.get("idFactura")
                    id_reserva = f.get("IdReserva") or f.get("idReserva")

                    subtotal = Decimal(str(f.get("Subtotal")  or f.get("subtotal")  or "0"))
                    descuento = Decimal(str(f.get("Descuento") or f.get("descuento") or "0"))
                    impuesto  = Decimal(str(f.get("Impuesto")  or f.get("impuesto")  or "0"))

                    total_calc = subtotal - descuento + impuesto

                    # Lo guardamos para que pueda usarlo el front
                    f["TotalCalculado"] = float(total_calc)

                    id_str  = str(id_factura).upper()
                    res_str = str(id_reserva).upper()
                    tot_str = str(total_calc).upper()

                    if q in id_str or q in res_str or q in tot_str:
                        filtrados.append(f)

                items = filtrados
            else:
                # Si no hay filtro, igual calculamos el total para todos
                for f in items:
                    subtotal = Decimal(str(f.get("Subtotal")  or f.get("subtotal")  or "0"))
                    descuento = Decimal(str(f.get("Descuento") or f.get("descuento") or "0"))
                    impuesto  = Decimal(str(f.get("Impuesto")  or f.get("impuesto")  or "0"))
                    total_calc = subtotal - descuento + impuesto
                    f["TotalCalculado"] = float(total_calc)

            return JsonResponse({
                "status": "ok",
                "data": items[:20]  # máximo 20
            })

        except Exception as e:
            return JsonResponse(
                {"status": "error",
                 "message": f"Error al buscar facturas: {e}"},
                status=500
            )
