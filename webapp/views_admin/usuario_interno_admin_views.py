from pprint import pprint

from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


from servicios.rest.gestion.UsuarioInternoGestionRest import UsuarioInternoGestionRest
from webapp.decorators import admin_required, admin_required_ajax


@method_decorator(admin_required, name='dispatch')
class UsuarioInternoView(View):
    template_name = "webapp/usuario/administrador/crud/usuarios_internos/index.html"

    def get(self, request):
        return render(request, self.template_name)


@method_decorator(admin_required_ajax, name='dispatch')
class UsuarioInternoListAjaxView(View):
    def get(self, request):
        api = UsuarioInternoGestionRest()
        try:
            data = api.listar()
            page_number = int(request.GET.get("page", 1))
            paginator = Paginator(data, 20)
            page = paginator.get_page(page_number)

            return JsonResponse({
                "status": "ok",
                "data": list(page),
                "page": page.number,
                "total_pages": paginator.num_pages
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
class UsuarioInternoGetAjaxView(View):
    def get(self, request, id_usuario):
        api = UsuarioInternoGestionRest()
        try:
            data = api.obtener_por_id(id_usuario)
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
class UsuarioInternoCreateAjaxView(View):
    def post(self, request):
        import re
        api = UsuarioInternoGestionRest()
        try:
            # Obtener datos
            nombre = request.POST.get("nombre", "").strip()
            apellido = request.POST.get("apellido", "").strip()
            correo = request.POST.get("correo", "").strip()
            tipo_doc = request.POST.get("tipo_documento", "").strip().upper()  # Normalizar a mayúsculas
            documento = request.POST.get("documento", "").strip()
            
            # Validaciones mejoradas
            if not nombre or nombre.isspace():
                return JsonResponse({"status": "error", "message": "El nombre es obligatorio y no puede ser solo espacios"}, status=400)
            
            if not apellido or apellido.isspace():
                return JsonResponse({"status": "error", "message": "El apellido es obligatorio y no puede ser solo espacios"}, status=400)
            
            if not correo or "@" not in correo:
                return JsonResponse({"status": "error", "message": "El correo debe ser válido y contener @"}, status=400)
            
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, correo):
                return JsonResponse({"status": "error", "message": "El formato del correo no es válido"}, status=400)
            
            # Tipo documento y documento son opcionales, pero si hay documento debe haber tipo
            if documento and not tipo_doc:
                return JsonResponse({"status": "error", "message": "Si ingresa un documento, debe seleccionar el tipo"}, status=400)
            
            if tipo_doc and not documento:
                return JsonResponse({"status": "error", "message": "Si selecciona tipo de documento, debe ingresar el número"}, status=400)
            
            # Validar formato según tipo documento (CEDULA, PASAPORTE en mayúsculas)
            if tipo_doc == "CEDULA":
                if not documento.isdigit() or len(documento) != 10:
                    return JsonResponse({"status": "error", "message": "La cédula debe tener exactamente 10 dígitos"}, status=400)
            elif tipo_doc == "PASAPORTE":
                if len(documento) < 5 or len(documento) > 20:
                    return JsonResponse({"status": "error", "message": "El pasaporte debe tener entre 5 y 20 caracteres"}, status=400)
            
            dto = {
                "Id": 0,
                "IdRol": int(request.POST.get("id_rol")),
                "Nombre": nombre,
                "Apellido": apellido,
                "Correo": correo,
                "Clave": request.POST.get("clave"),  # Texto plano
                "Estado": request.POST.get("estado") == "true",
                "FechaNacimiento": request.POST.get("fecha_nacimiento") or None,
                "TipoDocumento": tipo_doc or None,
                "Documento": documento or None,
            }

            api.crear(dto)
            return JsonResponse({"status": "ok", "message": "Usuario Interno creado exitosamente"})

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
class UsuarioInternoUpdateAjaxView(View):
    def post(self, request, id_usuario):
        import re
        api = UsuarioInternoGestionRest()
        pprint(request.POST)
        try:
            # Obtener datos
            nombre = request.POST.get("nombre", "").strip()
            apellido = request.POST.get("apellido", "").strip()
            correo = request.POST.get("correo", "").strip()
            tipo_doc = request.POST.get("tipo_documento", "").strip().upper()  # Normalizar a mayúsculas
            documento = request.POST.get("documento", "").strip()
            
            # Validaciones mejoradas
            if not nombre or nombre.isspace():
                return JsonResponse({"status": "error", "message": "El nombre es obligatorio y no puede ser solo espacios"}, status=400)
            
            if not apellido or apellido.isspace():
                return JsonResponse({"status": "error", "message": "El apellido es obligatorio y no puede ser solo espacios"}, status=400)
            
            if not correo or "@" not in correo:
                return JsonResponse({"status": "error", "message": "El correo debe ser válido y contener @"}, status=400)
            
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, correo):
                return JsonResponse({"status": "error", "message": "El formato del correo no es válido"}, status=400)
            
            # Tipo documento y documento son opcionales, pero si hay documento debe haber tipo
            if documento and not tipo_doc:
                return JsonResponse({"status": "error", "message": "Si ingresa un documento, debe seleccionar el tipo"}, status=400)
            
            if tipo_doc and not documento:
                return JsonResponse({"status": "error", "message": "Si selecciona tipo de documento, debe ingresar el número"}, status=400)
            
            # Validar formato según tipo documento (CEDULA, PASAPORTE en mayúsculas)
            if tipo_doc == "CEDULA":
                if not documento.isdigit() or len(documento) != 10:
                    return JsonResponse({"status": "error", "message": "La cédula debe tener exactamente 10 dígitos"}, status=400)
            elif tipo_doc == "PASAPORTE":
                if len(documento) < 5 or len(documento) > 20:
                    return JsonResponse({"status": "error", "message": "El pasaporte debe tener entre 5 y 20 caracteres"}, status=400)
            
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("estado")
            if estado_enviado is not None:
                estado = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_por_id(id_usuario)
                estado = registro_actual.get("Estado", True) if registro_actual else True
            
            dto = {
                "Id": id_usuario,
                "IdRol": int(request.POST.get("id_rol")),
                "Nombre": nombre,
                "Apellido": apellido,
                "Correo": correo,
                "Clave": request.POST.get("clave"),  # Vacío = no cambiar
                "Estado": estado,
                "FechaNacimiento": request.POST.get("fecha_nacimiento") or None,
                "TipoDocumento": tipo_doc or None,
                "Documento": documento or None,
            }

            api.actualizar(dto)
            return JsonResponse({"status": "ok", "message": "Usuario Interno actualizado exitosamente"})
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
class UsuarioInternoDeleteAjaxView(View):
    def post(self, request, id_usuario):
        api = UsuarioInternoGestionRest()
        try:
            api.eliminar(id_usuario)
            return JsonResponse({"status": "ok", "message": "Usuario Interno eliminado exitosamente"})
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el registro. Puede estar en uso"}, status=500)

@method_decorator(admin_required_ajax, name='dispatch')
class UsuarioInternoSearchAjaxView(View):
    """
    Buscador AJAX para Select2 de Usuarios Internos.
    Endpoint: /admin/usuario-interno/search/?q=texto
    """

    def get(self, request):
        q = (request.GET.get("q", "") or "").strip().upper()
        api = UsuarioInternoGestionRest()

        try:
            usuarios = api.listar() or []

            # Normalizamos a lista
            if not isinstance(usuarios, list):
                usuarios = []

            if q:
                filtrados = []
                for u in usuarios:
                    id_str   = str(u.get("Id", "")).upper()
                    nombre   = (u.get("Nombre") or "").upper()
                    apellido = (u.get("Apellido") or "").upper()
                    correo   = (u.get("Correo") or "").upper()
                    doc      = (u.get("Documento") or "").upper()

                    if (
                        q in id_str
                        or q in nombre
                        or q in apellido
                        or q in correo
                        or q in doc
                    ):
                        filtrados.append(u)

                usuarios = filtrados

            # Devolvemos máximo 20 resultados, el JS (Select2) se encarga de formatear
            return JsonResponse({
                "status": "ok",
                "data": usuarios[:20]
            })

        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al buscar usuarios internos: {e}"
                },
                status=500
            )
# ============================================================
# OBTENER SIGUIENTE ID (NEXT-ID)
# ============================================================
@method_decorator(admin_required_ajax, name="dispatch")
class UsuarioInternoNextIdAjaxView(View):
    """
    Devuelve el siguiente Id sugerido para mostrar en el formulario
    (máximo Id actual + 1). Es solo informativo: tu API genera su propio Id.
    """
    def get(self, request):
        api = UsuarioInternoGestionRest()
        try:
            usuarios = api.listar()
            max_id = 0

            if isinstance(usuarios, list):
                for u in usuarios:
                    # soporta tanto "Id" como "id"
                    raw = u.get("Id") or u.get("id")
                    try:
                        val = int(raw)
                    except (TypeError, ValueError):
                        continue
                    if val > max_id:
                        max_id = val

            next_id = max_id + 1

            return JsonResponse(
                {
                    "status": "ok",
                    "next": next_id,      # por compatibilidad
                    "next_id": next_id    # más explícito
                }
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Error al calcular siguiente Id de usuario interno: {e}",
                },
                status=500,
            )
