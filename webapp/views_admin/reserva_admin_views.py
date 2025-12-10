# webapp/views_admin/views_reserva_admin.py
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.ReservaGestionRest import ReservaGestionRest
from webapp.decorators import admin_required, admin_required_ajax


# ============================================================
# VISTA PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name='dispatch')
class ReservaView(View):
    template_name = "webapp/usuario/administrador/crud/reserva/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR (AJAX) – 20 en 20
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class ReservaListAjaxView(View):
    def get(self, request):
        api = ReservaGestionRest()
        try:
            data = api.obtener_reservas()  # lista de dicts

            page_number = int(request.GET.get("page", 1))
            paginator = Paginator(data, 20)  # 20 registros por página
            page_obj = paginator.get_page(page_number)

            return JsonResponse({
                "status": "ok",
                "data": list(page_obj),  # serializable
                "page": page_obj.number,
                "total_pages": paginator.num_pages
            })
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# OBTENER UNA RESERVA (AJAX)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class ReservaGetAjaxView(View):
    def get(self, request, id_reserva):
        api = ReservaGestionRest()
        try:
            data = api.obtener_reserva_por_id(id_reserva)
            return JsonResponse({"status": "ok", "data": data})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# CREAR RESERVA (AJAX)
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class ReservaCreateAjaxView(View):
    def post(self, request):
        api = ReservaGestionRest()
        try:
            # Campos enviados desde el formulario (PascalCase)
            id_reserva = int(request.POST.get("IdReserva"))

            id_unico_usuario = request.POST.get("IdUnicoUsuario")
            id_unico_usuario = int(id_unico_usuario) if id_unico_usuario else None

            id_unico_usuario_externo = request.POST.get("IdUnicoUsuarioExterno")
            id_unico_usuario_externo = int(id_unico_usuario_externo) if id_unico_usuario_externo else None

            costo_total = request.POST.get("CostoTotalReserva")
            costo_total = float(costo_total) if costo_total else None

            fecha_registro = request.POST.get("FechaRegistroReserva")  # string ISO
            fecha_inicio = request.POST.get("FechaInicioReserva")
            fecha_final = request.POST.get("FechaFinalReserva")

            estado_general = request.POST.get("EstadoGeneralReserva")  # string
            estado_reserva = request.POST.get("EstadoReserva") == "true"

            dto = {
                "idReserva": id_reserva,
                "idUnicoUsuario": id_unico_usuario,
                "idUnicoUsuarioExterno": id_unico_usuario_externo,
                "costoTotalReserva": costo_total,
                "fechaRegistroReserva": fecha_registro,
                "fechaInicioReserva": fecha_inicio,
                "fechaFinalReserva": fecha_final,
                "estadoGeneralReserva": estado_general,
                "estadoReserva": estado_reserva
            }

            api.crear_reserva(dto)
            return JsonResponse({"status": "ok", "message": "Reserva creado exitosamente"})

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# ACTUALIZAR RESERVA (AJAX)
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class ReservaUpdateAjaxView(View):
    def post(self, request, id_reserva):
        api = ReservaGestionRest()
        try:
            id_unico_usuario = request.POST.get("IdUnicoUsuario")
            id_unico_usuario = int(id_unico_usuario) if id_unico_usuario else None

            id_unico_usuario_externo = request.POST.get("IdUnicoUsuarioExterno")
            id_unico_usuario_externo = int(id_unico_usuario_externo) if id_unico_usuario_externo else None

            costo_total = request.POST.get("CostoTotalReserva")
            costo_total = float(costo_total) if costo_total else None

            fecha_registro = request.POST.get("FechaRegistroReserva")
            fecha_inicio = request.POST.get("FechaInicioReserva")
            fecha_final = request.POST.get("FechaFinalReserva")

            estado_general = request.POST.get("EstadoGeneralReserva")
            
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoReserva")
            if estado_enviado is not None:
                estado_reserva = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_reserva_por_id(int(id_reserva))
                estado_reserva = registro_actual.get("EstadoReserva", True) if registro_actual else True

            dto = {
                "idReserva": int(id_reserva),
                "idUnicoUsuario": id_unico_usuario,
                "idUnicoUsuarioExterno": id_unico_usuario_externo,
                "costoTotalReserva": costo_total,
                "fechaRegistroReserva": fecha_registro,
                "fechaInicioReserva": fecha_inicio,
                "fechaFinalReserva": fecha_final,
                "estadoGeneralReserva": estado_general,
                "estadoReserva": estado_reserva
            }

            api.actualizar_reserva(int(id_reserva), dto)
            return JsonResponse({"status": "ok", "message": "Reserva actualizado exitosamente"})

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


# ============================================================
# ELIMINAR RESERVA (AJAX)
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class ReservaDeleteAjaxView(View):
    def post(self, request, id_reserva):
        api = ReservaGestionRest()
        try:
            api.eliminar_reserva(int(id_reserva))
            return JsonResponse({"status": "ok", "message": "Reserva eliminado exitosamente"})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )

# ================================
# BUSCADOR AJAX PARA SELECT2 (RESERVAS)
# ================================
from django.utils.decorators import method_decorator
from webapp.decorators import admin_required_ajax
from servicios.rest.gestion.ReservaGestionRest import ReservaGestionRest

@method_decorator(admin_required_ajax, name='dispatch')
class ReservaSearchAjaxView(View):
    def get(self, request):
        # Texto que escribe el usuario en el Select2
        q = request.GET.get("q", "").strip().upper()

        api = ReservaGestionRest()

        try:
            reservas = api.obtener_reservas()   # ya te devuelve la lista de dicts

            if not isinstance(reservas, list):
                reservas = []

            # Si el usuario escribió algo, filtramos
            if q:
                filtradas = []
                for r in reservas:
                    id_reserva   = str(r.get("IdReserva", "")).upper()
                    estado_gen   = (r.get("EstadoGeneralReserva") or "").upper()
                    id_usuario   = str(r.get("IdUnicoUsuario") or "").upper()

                    # puedes ajustar los campos que quieras usar para buscar
                    if (
                        q in id_reserva or
                        q in estado_gen or
                        q in id_usuario
                    ):
                        filtradas.append(r)

                reservas = filtradas

            # devolvemos máximo 20 como en habitaciones
            return JsonResponse({
                "status": "ok",
                "data": reservas[:20]
            })

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al buscar reservas: {e}"},
                status=500
            )
# ============================================================
# OBTENER SIGUIENTE ID (NEXT-ID)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class ReservaNextIdAjaxView(View):
    def get(self, request):
        api = ReservaGestionRest()
        try:
            reservas = api.obtener_reservas()  # lista de dicts
            max_id = 0

            if isinstance(reservas, list):
                for r in reservas:
                    # soporta tanto "IdReserva" como "idReserva"
                    raw = r.get("IdReserva") or r.get("idReserva")
                    try:
                        val = int(raw)
                    except (TypeError, ValueError):
                        continue

                    if val > max_id:
                        max_id = val

            next_id = max_id + 1

            return JsonResponse({
                "status": "ok",
                "next": next_id,       # por compatibilidad
                "next_id": next_id     # clave más explícita
            })

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al calcular siguiente IdReserva: {e}"},
                status=500
            )



# ============================================================
# OBTENER SIGUIENTE ID (NEXT-ID)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class ReservaNextIdAjaxView(View):
    def get(self, request):
        api = ReservaGestionRest()
        try:
            reservas = api.obtener_reservas()  # lista de dicts
            max_id = 0

            if isinstance(reservas, list):
                for r in reservas:
                    # Puede venir como "IdReserva" o "idReserva"
                    raw_id = r.get("IdReserva") or r.get("idReserva")
                    try:
                        val = int(raw_id)
                    except (TypeError, ValueError):
                        continue

                    if val > max_id:
                        max_id = val

            next_id = max_id + 1

            return JsonResponse({
                "status": "ok",
                "next_id": next_id,   # clave principal
                "next": next_id       # por compatibilidad con otros CRUDs
            })

        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al calcular siguiente IdReserva: {e}"
                },
                status=500
            )

