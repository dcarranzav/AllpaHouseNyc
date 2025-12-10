from __future__ import annotations
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
from utils.s3_upload import subir_pdf_a_s3
from servicios.rest.gestion.PdfGestionRest import PdfGestionRest
from webapp.decorators import admin_required, admin_required_ajax
import os
import uuid
from django.core.files.uploadedfile import UploadedFile

# ============================================================
# VIEW PRINCIPAL
# ============================================================
@method_decorator(admin_required, name='dispatch')
class PdfView(View):
    template_name = "webapp/usuario/administrador/crud/pdf/index.html"

    def get(self, request):
        return render(request, self.template_name)


# ============================================================
# LISTA (Paginada 20 en 20)
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class PdfListAjaxView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        page_size = 20

        api = PdfGestionRest()

        try:
            data = api.obtener_pdfs()

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

        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión a internet"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente en unos momentos"}, status=504)
        except HTTPError as e:
            return JsonResponse({"status": "error", "message": f"Error en el servidor: {e.response.status_code}. Contacte al administrador"}, status=500)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": "Error al cargar la lista de PDFs. Intente nuevamente"}, status=500)


# ============================================================
# GET UNO
# ============================================================
@method_decorator(admin_required_ajax, name='dispatch')
class PdfGetAjaxView(View):
    def get(self, request, id_pdf):
        api = PdfGestionRest()
        try:
            data = api.obtener_pdf_por_id(id_pdf)
            return JsonResponse({"status": "ok", "data": data})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo obtener el PDF. Verifique que el ID sea correcto"}, status=404)


# ============================================================
# CREAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PdfCreateAjaxView(View):
    def post(self, request):
        api = PdfGestionRest()

        try:
            api.crear_pdf(
                id_pdf=int(request.POST.get("IdPdf")),
                id_factura=request.POST.get("IdFactura") or None,
                url_pdf=request.POST.get("UrlPdf"),
                estado_pdf=request.POST.get("EstadoPdf") == "true"
            )

            return JsonResponse({"status": "ok", "message": "PDF creado exitosamente"})

        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor. Verifique su conexión"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo crear el PDF. Verifique los datos ingresados"}, status=500)


# ============================================================
# ACTUALIZAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PdfUpdateAjaxView(View):
    def post(self, request, id_pdf):
        api = PdfGestionRest()

        try:
            # Obtener el estado actual del registro si no se envía
            estado_enviado = request.POST.get("EstadoPdf")
            if estado_enviado is not None:
                estado_pdf = estado_enviado == "true"
            else:
                # Obtener el estado actual del registro
                registro_actual = api.obtener_pdf_por_id(id_pdf)
                estado_pdf = registro_actual.get("EstadoPdf", True) if registro_actual else True
            
            api.actualizar_pdf(
                id_pdf=int(id_pdf),
                id_factura=request.POST.get("IdFactura") or None,
                url_pdf=request.POST.get("UrlPdf"),
                estado_pdf=estado_pdf
            )

            return JsonResponse({"status": "ok", "message": "PDF actualizado exitosamente"})

        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": f"Datos inválidos: {str(ve)}"}, status=400)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo actualizar el PDF. Verifique los datos"}, status=500)


# ============================================================
# ELIMINAR
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PdfDeleteAjaxView(View):
    def post(self, request, id_pdf):
        api = PdfGestionRest()

        try:
            api.eliminar_pdf(id_pdf)
            return JsonResponse({"status": "ok", "message": "PDF eliminado exitosamente"})
        except ConnectionError:
            return JsonResponse({"status": "error", "message": "No se pudo conectar con el servidor"}, status=503)
        except Timeout:
            return JsonResponse({"status": "error", "message": "El servidor no responde. Intente nuevamente"}, status=504)
        except Exception:
            return JsonResponse({"status": "error", "message": "No se pudo eliminar el PDF. Puede estar en uso"}, status=500)

# ============================================================
# SUBIR ARCHIVO PDF A S3 (para el CRUD)
# ============================================================
@method_decorator([csrf_exempt, admin_required_ajax], name='dispatch')
class PdfUploadAjaxView(View):
    def post(self, request):
        file_obj: UploadedFile | None = request.FILES.get("file")

        if not file_obj:
            return JsonResponse(
                {"status": "error", "message": "No se recibió ningún archivo"},
                status=400
            )

        # Validar tipo
        if (
            file_obj.content_type != "application/pdf"
            and not file_obj.name.lower().endswith(".pdf")
        ):
            return JsonResponse(
                {"status": "error", "message": "Solo se permiten archivos PDF."},
                status=400
            )

        # Máx 10 MB (ajusta si quieres)
        max_size = 10 * 1024 * 1024
        if file_obj.size > max_size:
            return JsonResponse(
                {"status": "error", "message": "El archivo es demasiado grande (máx 10MB)."},
                status=400
            )

        try:
            # Generamos un nombre único dentro de una carpeta lógica
            _, ext = os.path.splitext(file_obj.name)
            ext = ext or ".pdf"
            filename = f"facturas/pdfs/{uuid.uuid4().hex}{ext}"

            # Leemos el archivo en bytes y usamos TU helper
            pdf_bytes = file_obj.read()
            url = subir_pdf_a_s3(pdf_bytes, filename)

            return JsonResponse({
                "status": "ok",
                "url": url
            })

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error al subir el PDF: {e}"},
                status=500
            )

@method_decorator(admin_required_ajax, name="dispatch")
class PdfNextIdAjaxView(View):
    """
    Devuelve el siguiente ID_PDF disponible.
    GET /admin/pdf/next-id/
    -> { "next": 118 }
    """
    def get(self, request):
        api = PdfGestionRest()
        try:
            data = api.obtener_pdfs() or []

            ids = []
            for p in data:
                val = p.get("IdPdf")
                if isinstance(val, int):
                    ids.append(val)
                else:
                    try:
                        ids.append(int(val))
                    except (TypeError, ValueError):
                        pass

            siguiente = (max(ids) + 1) if ids else 1
            return JsonResponse({"next": siguiente})

        except Exception:
            # En caso de error devolvemos 1 para no romper el flujo
            return JsonResponse({"next": 1})
