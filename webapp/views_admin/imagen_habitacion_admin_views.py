from __future__ import annotations

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from requests.exceptions import ConnectionError, Timeout, HTTPError
from utils.s3_upload import subir_imagen_habitacion_a_s3
import os
import uuid
import boto3
from django.conf import settings

from servicios.rest.gestion.ImagenHabitacionGestionRest import ImagenHabitacionGestionRest
from webapp.decorators import admin_required, admin_required_ajax
from django.core.files.uploadedfile import UploadedFile


# ============================================================
# VIEW PRINCIPAL (HTML)
# ============================================================
@method_decorator(admin_required, name="dispatch")
class ImagenHabitacionView(View):
    template_name = "webapp/usuario/administrador/crud/imagen_habitacion/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTAR 20 EN 20
# ============================================================
@method_decorator(admin_required_ajax, name="dispatch")
class ImagenHabitacionListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = ImagenHabitacionGestionRest()

        try:
            data = api.obtener_imagenes() or []

            total = len(data)
            total_pages = (total + page_size - 1) // page_size

            inicio = (page - 1) * page_size
            fin = inicio + page_size

            return JsonResponse(
                {
                    "status": "ok",
                    "data": data[inicio:fin],
                    "page": page,
                    "total_pages": total_pages,
                }
            )

        except ConnectionError:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo conectar con el servidor. Verifique su conexión a internet",
                },
                status=503,
            )
        except Timeout:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "El servidor no responde. Intente nuevamente en unos momentos",
                },
                status=504,
            )
        except HTTPError:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Error en el servidor. Contacte al administrador",
                },
                status=500,
            )
        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400,
            )
        except Exception:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Error al cargar la lista. Intente nuevamente",
                },
                status=500,
            )


# ============================================================
# OBTENER UNO
# ============================================================
@method_decorator(admin_required_ajax, name="dispatch")
class ImagenHabitacionGetAjaxView(View):
    def get(self, request, id_imagen):
        api = ImagenHabitacionGestionRest()

        try:
            data = api.obtener_imagen_por_id(int(id_imagen))
            return JsonResponse({"status": "ok", "data": data})
        except ConnectionError:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo conectar con el servidor",
                },
                status=503,
            )
        except Timeout:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "El servidor no responde. Intente nuevamente",
                },
                status=504,
            )
        except ValueError as ve:
            return JsonResponse(
                {"status": "error", "message": f"Datos inválidos: {ve}"},
                status=400,
            )
        except Exception:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo obtener el registro. Verifique que el ID sea correcto",
                },
                status=404,
            )


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class ImagenHabitacionCreateAjaxView(View):
    def post(self, request):

        api = ImagenHabitacionGestionRest()

        try:
            id_habitacion = request.POST.get("IdHabitacion")
            url_imagen = request.POST.get("UrlImagen") or ""
            estado_imagen = request.POST.get("EstadoImagen") == "true"

            if not id_habitacion:
                return JsonResponse({"status": "error", "message": "ID Habitación es requerido"}, status=400)

            # si viene archivo, subimos a S3 y usamos esa URL, sin importar lo que vino en UrlImagen
            file_obj = request.FILES.get("file")
            if file_obj:
                url_imagen = subir_imagen_habitacion_a_s3(file_obj)

            if not url_imagen:
                return JsonResponse({"status": "error", "message": "Debe ingresar una URL o subir una imagen."},
                                    status=400)

            api.crear_imagen(
                id_habitacion=id_habitacion,
                url_imagen=url_imagen,
                estado_imagen=estado_imagen
            )
            return JsonResponse({"status": "ok", "message": "Imagen creada exitosamente"})

        except ConnectionError:
            return JsonResponse(
                {"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión"},
                status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"},
                                status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"No se pudo crear el registro. Verifique los datos ingresados: {e}"},
                status=500)


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class ImagenHabitacionUpdateAjaxView(View):
    def post(self, request, id_imagen):

        api = ImagenHabitacionGestionRest()

        try:
            id_habitacion = request.POST.get("IdHabitacion")
            url_imagen = (request.POST.get("UrlImagen") or "").strip()
            file_obj: UploadedFile | None = request.FILES.get("file")

            if not id_habitacion:
                return JsonResponse({"status": "error", "message": "ID Habitación es requerido"}, status=400)

            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoImagen")
            if estado_enviado is not None:
                estado_imagen = estado_enviado == "true"
            else:
                registro_actual = api.obtener_imagen_por_id(int(id_imagen))
                estado_imagen = registro_actual.get("EstadoImagen", True) if registro_actual else True

            # Si el usuario sube un nuevo archivo, se sube a S3 y se reemplaza la URL
            if file_obj:
                url_imagen = subir_imagen_habitacion_a_s3(file_obj)

            # Si no hay ni archivo ni URL manual, error
            if not url_imagen:
                return JsonResponse(
                    {"status": "error", "message": "Debe enviar una URL o subir un archivo de imagen."},
                    status=400
                )

            api.actualizar_imagen(
                id_imagen=int(id_imagen),
                id_habitacion=id_habitacion,
                url_imagen=url_imagen,
                estado_imagen=estado_imagen
            )
            return JsonResponse({"status": "ok", "message": "Imagen actualizada exitosamente"})

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"No se pudo actualizar el registro. Verifique los datos ({e})"},
                status=500
            )


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name="dispatch")
class ImagenHabitacionDeleteAjaxView(View):
    def post(self, request, id_imagen):
        api = ImagenHabitacionGestionRest()

        try:
            result = api.eliminar_imagen(int(id_imagen))

            if result:
                return JsonResponse(
                    {"status": "ok", "message": "Imagen eliminada exitosamente"}
                )
            else:
                return JsonResponse(
                    {"status": "error", "message": "Imagen no encontrada"},
                    status=404,
                )
        except ConnectionError:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo conectar con el servidor",
                },
                status=503,
            )
        except Timeout:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "El servidor no responde. Intente nuevamente",
                },
                status=504,
            )
        except Exception:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No se pudo eliminar el registro. Puede estar en uso",
                },
                status=500,
            )


# ============================================================
# SUBIR ARCHIVO A S3 (DRAG & DROP)
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name="dispatch")
class ImagenHabitacionUploadAjaxView(View):
    """
    Sube una imagen a S3 y devuelve la URL pública.
    Espera el archivo en request.FILES["file"].
    """

    def post(self, request):
        archivo = request.FILES.get("file")

        if not archivo:
            return JsonResponse(
                {"status": "error", "message": "No se recibió ninguna imagen."},
                status=400,
            )

        if not archivo.content_type.startswith("image/"):
            return JsonResponse(
                {"status": "error", "message": "El archivo debe ser una imagen."},
                status=400,
            )

        # Máx 5MB
        if archivo.size > 5 * 1024 * 1024:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "La imagen supera los 5 MB permitidos.",
                },
                status=400,
            )

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        _, ext = os.path.splitext(archivo.name)
        if not ext:
            ext = ".jpg"

        key = f"imagenes/carlos/{uuid.uuid4().hex}{ext.lower()}"

        try:
            s3.upload_fileobj(
                archivo,
                settings.AWS_STORAGE_BUCKET_NAME,
                key,
                ExtraArgs={
                    "ContentType": archivo.content_type,
                    "ACL": "public-read",
                },
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al subir la imagen: {e}"},
                status=500,
            )

        url = (
            f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3."
            f"{settings.AWS_REGION}.amazonaws.com/{key}"
        )

        return JsonResponse({"status": "ok", "url": url})
