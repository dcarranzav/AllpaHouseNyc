# webapp/views_admin/views_rol_admin.py

from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.RolGestionRest import RolGestionRest
from webapp.decorators import admin_required, admin_required_ajax


@method_decorator(admin_required, name='dispatch')
class RolView(View):
    template_name = "webapp/usuario/administrador/crud/rol/index.html"

    def get(self, request):
        return render(request, self.template_name)


@method_decorator(admin_required_ajax, name='dispatch')
class RolListAjaxView(View):
    def get(self, request):
        api = RolGestionRest()
        try:
            data = api.obtener_roles()

            page_number = int(request.GET.get("page", 1))
            paginator = Paginator(data, 20)
            page = paginator.get_page(page_number)

            return JsonResponse({
                "status": "ok",
                "data": list(page),
                "page": page.number,
                "total_pages": paginator.num_pages,
            })

        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
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


@method_decorator(admin_required_ajax, name='dispatch')
class RolGetAjaxView(View):
    def get(self, request, id_rol):
        api = RolGestionRest()
        try:
            data = api.obtener_rol_por_id(id_rol)
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
class RolCreateAjaxView(View):
    def post(self, request):
        api = RolGestionRest()
        try:
            id_rol = request.POST.get("IdRol")
            nombre = request.POST.get("NombreRol")
            estado = request.POST.get("EstadoRol") == "true"

            dto = {
                "idRol": int(id_rol),
                "nombreRol": nombre,
                "estadoRol": estado,
            }

            api.crear_rol(dto)
            return JsonResponse({"status": "ok", "message": "Rol creado exitosamente"})

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
class RolUpdateAjaxView(View):
    def post(self, request, id_rol):
        api = RolGestionRest()
        try:
            nombre = request.POST.get("NombreRol")
            
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoRol")
            if estado_enviado is not None:
                estado = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_rol_por_id(id_rol)
                estado = registro_actual.get("EstadoRol", True)

            dto = {
                "idRol": int(id_rol),
                "nombreRol": nombre,
                "estadoRol": estado,
            }

            api.actualizar_rol(id_rol, dto)
            return JsonResponse({"status": "ok", "message": "Rol actualizado exitosamente"})

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
class RolDeleteAjaxView(View):
    def post(self, request, id_rol):
        api = RolGestionRest()
        try:
            api.eliminar_rol(id_rol)
            return JsonResponse({"status": "ok", "message": "Rol eliminado exitosamente"})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)

# ============================================================
# OBTENER SIGUIENTE ID (NEXT-ID) PARA ROL
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class RolNextIdAjaxView(View):
    def get(self, request):
        api = RolGestionRest()
        try:
            roles = api.obtener_roles()   # lista de dicts
            max_id = 0

            if isinstance(roles, list):
                for r in roles:
                    # Soporta tanto "IdRol" (PascalCase) como "idRol" (camelCase)
                    raw = r.get("IdRol") or r.get("idRol")
                    try:
                        val = int(raw)
                    except (TypeError, ValueError):
                        continue

                    if val > max_id:
                        max_id = val

            next_id = max_id + 1

            return JsonResponse({
                "status": "ok",
                "next": next_id,      # por compatibilidad
                "next_id": next_id    # nombre más descriptivo
            })

        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al calcular siguiente IdRol: {e}"
                },
                status=500
            )

