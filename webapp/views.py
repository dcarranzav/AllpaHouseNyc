import base64
from xml.sax.handler import property_interning_dict
import boto3
from django.conf import settings

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from datetime import datetime
from servicios.rest.gestion.HoldGestionRest import HoldGestionRest
from servicios.rest.gestion.TipoHabitacionGestionRest import TipoHabitacionGestionRest
from servicios.rest.gestion.AmexHabGestionRest import AmexHabGestionRest
from servicios.rest.gestion.AmenidadesGestionRest import AmenidadesGestionRest
from pprint import pprint
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from servicios.rest.gestion.UsuarioInternoGestionRest import UsuarioInternoGestionRest
from django.shortcuts import render, redirect
from servicios.rest.gestion.PagoGestionRest import PagoGestionRest
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
from servicios.rest.gestion.UsuarioInternoGestionRest import UsuarioInternoGestionRest
from servicios.rest.gestion.FuncionesEspecialesGestionRest import FuncionesEspecialesGestionRest
import threading
import time
from servicios.rest.gestion.FacturasGestionRest import FacturasGestionRest
from servicios.rest.gestion.PdfGestionRest import PdfGestionRest
from servicios.rest.gestion.HabxResGestionRest import HabxResGestionRest
from servicios.rest.gestion.HabitacionesGestionRest import HabitacionesGestionRest
from servicios.rest.gestion.ReservaGestionRest import ReservaGestionRest
from servicios.rest.gestion.ImagenHabitacionGestionRest import ImagenHabitacionGestionRest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from utils.pdf_generator import generar_pdf_factura
from utils.s3_upload import subir_pdf_a_s3
from webapp.decorators import admin_required

import uuid


def index_inicio(request):
    return render(request, 'webapp/inicio/index.html')

class HabitacionesView(View):
    template_name = "webapp/habitaciones/index.html"

    def get(self, request):

        # Cargar tipos de habitación
        cliente_tipos = TipoHabitacionGestionRest()
        tipos = cliente_tipos.obtener_tipos()

        return render(request, self.template_name, {
            "usuario_id": request.session.get("usuario_id"),
            "token_sesion": request.session.session_key or "anon-" + str(uuid.uuid4()),
            "tipos_habitacion": tipos
        })


class HabitacionesAjaxView(View):
    def get(self, request):
        try:
            import time
            start_time = time.time()

            # ------------------------------------
            # 🔑 EXPIRAR HOLDs VENCIDOS PRIMERO
            # ------------------------------------
            # Asegurar que los HOLDs vencidos se expiren antes de buscar habitaciones
            from servicios.hold_service import expirar_holds_async
            expirar_holds_async()  # Se ejecuta en background, no bloquea

            # ------------------------------------
            # Filtros
            # ------------------------------------
            tipo_habitacion = request.GET.get("tipo_habitacion") or None
            fecha_entrada = request.GET.get("fecha_entrada") or None
            fecha_salida = request.GET.get("fecha_salida") or None
            capacidad = request.GET.get("capacidad") or None
            precio_min = request.GET.get("precio_min") or None
            precio_max = request.GET.get("precio_max") or None

            # Paginación
            try:
                page = int(request.GET.get("page", 1))
            except:
                page = 1

            page = max(page, 1)
            per_page = 5

            date_from = datetime.strptime(fecha_entrada, "%Y-%m-%d") if fecha_entrada else None
            date_to = datetime.strptime(fecha_salida, "%Y-%m-%d") if fecha_salida else None

            # ------------------------------------
            # OPTIMIZACIÓN: Cargar datos EN PARALELO
            # ------------------------------------

            # Contenedor para almacenar resultados
            datos = {
                "habitaciones_all": None,
                "todas_habitaciones": None,
                "amex_list": None,
                "amenidades_data": None,
                "tipos_list": None,
                "imagenes_list": None,
                "hoteles_list": None,    # ← NUEVO: hoteles
                "ciudades_list": None,   # ← NUEVO: ciudades
            }

            # Funciones para ejecutar en threads
            def cargar_buscar():
                # Usar REST en lugar de SOAP
                cliente = HabitacionesGestionRest()
                todas_habs = cliente.obtener_habitaciones() or []
                
                # Aplicar filtros manualmente en Python
                habitaciones_filtradas = todas_habs
                
                # Filtrar por tipo de habitación
                if tipo_habitacion:
                    habitaciones_filtradas = [
                        h for h in habitaciones_filtradas 
                        if h.get("NombreTipoHabitacion", "").lower() == tipo_habitacion.lower()
                    ]
                
                # Filtrar por capacidad
                if capacidad:
                    habitaciones_filtradas = [
                        h for h in habitaciones_filtradas 
                        if h.get("CapacidadHabitacion", 0) >= int(capacidad)
                    ]
                
                # Filtrar por precio
                if precio_min:
                    habitaciones_filtradas = [
                        h for h in habitaciones_filtradas 
                        if h.get("PrecioActualHabitacion", 0) >= float(precio_min)
                    ]
                
                if precio_max:
                    habitaciones_filtradas = [
                        h for h in habitaciones_filtradas 
                        if h.get("PrecioActualHabitacion", 0) <= float(precio_max)
                    ]
                
                # Nota: El filtrado por fechas requeriría consultar disponibilidad,
                # por ahora devolvemos todas las que cumplan los otros criterios
                datos["habitaciones_all"] = habitaciones_filtradas


            def cargar_habitaciones():
                api_habs = HabitacionesGestionRest()
                datos["todas_habitaciones"] = api_habs.obtener_habitaciones()

            def cargar_amexhab():
                amex_rest = AmexHabGestionRest()
                datos["amex_list"] = amex_rest.obtener_amexhab()

            def cargar_amenidades():
                amen_rest = AmenidadesGestionRest()
                datos["amenidades_data"] = amen_rest.obtener_amenidades()

            def cargar_tipos():
                tipos_rest = TipoHabitacionGestionRest()
                datos["tipos_list"] = tipos_rest.obtener_tipos()

            def cargar_imagenes():
                imgs_rest = ImagenHabitacionGestionRest()
                datos["imagenes_list"] = imgs_rest.obtener_imagenes()

            def cargar_hoteles():
                from servicios.rest.gestion.HotelGestionRest import HotelGestionRest
                hoteles_rest = HotelGestionRest()
                datos["hoteles_list"] = hoteles_rest.obtener_hoteles()

            def cargar_ciudades():
                from servicios.rest.gestion.CiudadGestionRest import CiudadGestionRest
                ciudades_rest = CiudadGestionRest()
                datos["ciudades_list"] = ciudades_rest.obtener_ciudades()

            # Crear threads para cargas paralelas
            threads = [
                threading.Thread(target=cargar_buscar),
                threading.Thread(target=cargar_habitaciones),
                threading.Thread(target=cargar_amexhab),
                threading.Thread(target=cargar_amenidades),
                threading.Thread(target=cargar_tipos),
                threading.Thread(target=cargar_imagenes),
                threading.Thread(target=cargar_hoteles),   # ← NUEVO
                threading.Thread(target=cargar_ciudades),  # ← NUEVO
            ]

            # Iniciar todos los threads
            for t in threads:
                t.start()

            # Esperar a que terminen TODOS
            for t in threads:
                t.join()

            elapsed_data = time.time() - start_time
            print(f"[PERF] Carga de datos en paralelo: {elapsed_data:.2f}s")

            # Desempacar datos
            habitaciones_all = datos["habitaciones_all"]
            todas_las_habitaciones = datos["todas_habitaciones"]
            amex_list = datos["amex_list"]
            amenidades_data = datos["amenidades_data"]
            tipos_list = datos["tipos_list"]
            imagenes_list = datos["imagenes_list"] or []
            hoteles_list = datos["hoteles_list"] or []     # ← NUEVO
            ciudades_list = datos["ciudades_list"] or []   # ← NUEVO

            total = len(habitaciones_all)

            # ------------------------------------
            # Paginación
            # ------------------------------------
            start = (page - 1) * per_page
            end = start + per_page
            habitaciones_slice = habitaciones_all[start:end]

            if not habitaciones_slice:
                return JsonResponse({"success": True, "data": [], "total": total})

            # ------------------------------------
            # Crear índices para búsqueda O(1)
            # ------------------------------------
            hab_index = {h["IdHabitacion"]: h for h in todas_las_habitaciones}

            amex_index = {}
            for a in amex_list:
                amex_index.setdefault(a["IdHabitacion"], []).append(a["IdAmenidad"])

            amen_index = {a["IdAmenidad"]: a["NombreAmenidad"] for a in amenidades_data}

            idx_tipos = {t["IdTipoHabitacion"]: t for t in tipos_list}
            
            # ← NUEVO: Índices de hoteles y ciudades
            idx_hoteles = {h["IdHotel"]: h["NombreHotel"] for h in hoteles_list}
            idx_ciudades = {c["IdCiudad"]: c["NombreCiudad"] for c in ciudades_list}
            
            # ← NUEVO: Índice de imágenes por habitación
            imgs_index = {}
            for img in imagenes_list:
                id_hab = img.get("IdHabitacion")
                url_img = img.get("UrlImagen")  # ← CORREGIDO: el servicio retorna "UrlImagen"
                if id_hab and url_img:
                    if id_hab not in imgs_index:
                        imgs_index[id_hab] = []
                    imgs_index[id_hab].append(url_img)

            resultado = []

            for h in habitaciones_slice:
                # REST retorna con PascalCase, no camelCase
                hid = h.get("IdHabitacion") or h.get("idHabitacion")

                # Usar índice en lugar de llamar API
                detalle = hab_index.get(hid)

                if not detalle:
                    continue

                capacidad_real = detalle.get("CapacidadHabitacion")
                tipo_id = detalle.get("IdTipoHabitacion")
                tipo_data = idx_tipos.get(tipo_id)

                # Amenidades
                ids_amen = amex_index.get(hid, [])
                nombres_amenidades = [amen_index.get(aid, "Amenidad desconocida") for aid in ids_amen]

                # ← MEJORADO: Imagen - Priorizar imágenes del servicio REST (panel admin)
                imagen_principal = None
                
                # 1. Intentar obtener imagen desde el servicio REST (que usa el panel admin)
                imagenes_rest = imgs_index.get(hid, [])
                if imagenes_rest and len(imagenes_rest) > 0:
                    imagen_principal = imagenes_rest[0]  # Primera imagen de la habitación
                
                # 2. Si no hay imágenes en REST, usar la del SOAP (legacy)
                if not imagen_principal:
                    raw_img = h.get("imagenes") or ""
                    imagen_principal = raw_img.split("|")[0].strip() if "|" in raw_img else raw_img.strip()
                
                # 3. Si aún no hay imagen, usar la por defecto
                if not imagen_principal:
                    imagen_principal = "https://imageness3realdecuenca.s3.us-east-2.amazonaws.com/Imagen4.png"

                # Obtener nombres de hotel y ciudad desde los índices
                id_hotel = detalle.get("IdHotel")
                id_ciudad = detalle.get("IdCiudad")
                
                nombre_hotel = idx_hoteles.get(id_hotel, "Hotel desconocido")
                nombre_ciudad = idx_ciudades.get(id_ciudad, "Ciudad desconocida")
                
                item = {
                    "id": hid,
                    "nombre": detalle.get("NombreHabitacion"),
                    "hotel": nombre_hotel,
                    "ubicacion": nombre_ciudad,
                    "precio": detalle.get("PrecioActualHabitacion"),
                    "imagen": imagen_principal,
                    "amenidades": nombres_amenidades,
                    "capacidad": capacidad_real,
                    "tipo_nombre": tipo_data.get("NombreHabitacion") if tipo_data else None,
                    "descripcion_tipo": tipo_data.get("DescripcionTipoHabitacion") if tipo_data else None,
                }

                resultado.append(item)

            elapsed_total = time.time() - start_time
            print(f"[PERF] Tiempo total de solicitud: {elapsed_total:.2f}s")

            return JsonResponse({"success": True, "data": resultado, "total": total})

        except Exception as e:
            print("\n❌ ERROR EN SERVIDOR:")
            print(e)
            import traceback
            traceback.print_exc()
            return JsonResponse({"success": False, "error": str(e)}, status=500)


def detalle_habitacion(request, id):
    """
    Vista para mostrar los detalles de una habitación específica.
    OPTIMIZACIÓN: Carga de datos en paralelo
    """
    import time
    start_time = time.time()

    # 🔑 EXPIRAR HOLDs VENCIDOS PRIMERO
    from servicios.hold_service import expirar_holds_async
    expirar_holds_async()  # Se ejecuta en background

    # ==============================
    # CARGAR DATOS EN PARALELO
    # ==============================
    datos = {
        "habitaciones": None,
        "amex_list": None,
        "amenidades_data": None,
    }

    def cargar_habitaciones():
        # Usar REST en lugar de SOAP
        cliente = HabitacionesGestionRest()
        datos["habitaciones"] = cliente.obtener_habitaciones()

    def cargar_amexhab():
        amex_rest = AmexHabGestionRest()
        datos["amex_list"] = amex_rest.obtener_amexhab()

    def cargar_amenidades():
        amen_rest = AmenidadesGestionRest()
        datos["amenidades_data"] = amen_rest.obtener_amenidades()

    # Crear threads
    threads = [
        threading.Thread(target=cargar_habitaciones),
        threading.Thread(target=cargar_amexhab),
        threading.Thread(target=cargar_amenidades),
    ]

    # Ejecutar en paralelo
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    elapsed_data = time.time() - start_time
    print(f"[PERF] Carga de datos en paralelo: {elapsed_data:.2f}s")

    # ==============================
    # PROCESAR DATOS
    # ==============================

    habitaciones = datos["habitaciones"]
    amex_list = datos["amex_list"]
    amenidades_data = datos["amenidades_data"]

    # Buscar la habitación con el ID proporcionado (REST usa PascalCase)
    habitacion = next((h for h in habitaciones if h.get("IdHabitacion") == id), None)

    if not habitacion:
        # Si no se encuentra la habitación
        return render(request, 'webapp/habitaciones/no_encontrada.html', {"id": id})

    # Filtrar solo registros de la habitación actual
    ids_amenidades = [
        a["IdAmenidad"]
        for a in amex_list
        if a.get("IdHabitacion") == id
    ]

    # Index de amenidad por ID
    amen_index = {a["IdAmenidad"]: a["NombreAmenidad"] for a in amenidades_data}

    # Lista final de nombres de amenidad
    amenidades = [
        amen_index.get(aid, "Amenidad desconocida")
        for aid in ids_amenidades
    ]

    # ==============================
    # Procesar imágenes
    # ==============================
    imagenes_raw = habitacion.get("imagenes", "") or ""
    imagen_lista = [img.strip() for img in imagenes_raw.split("|") if img.strip()]
    if not imagen_lista:
        imagen_lista = ["https://imageness3realdecuenca.s3.us-east-2.amazonaws.com/Imagen4.png"]

    imagen_principal = imagen_lista[0]

    # ==============================
    # Armar contexto
    # ==============================
    contexto = {
        "id": habitacion.get("IdHabitacion"),
        "nombre": habitacion.get("NombreHabitacion") or "Habitación",
        "hotel": habitacion.get("NombreHotel") or "Hotel desconocido",
        "ubicacion": habitacion.get("NombreCiudad") or "Ubicación no disponible",
        "pais": habitacion.get("NombrePais") or "No disponible",
        "tipo": habitacion.get("NombreTipoHabitacion") or "N/A",
        "capacidad": habitacion.get("CapacidadHabitacion") or 0,
        "precio": habitacion.get("PrecioActualHabitacion") or 0,

        "imagenes": imagen_lista,
        "imagen_principal": imagen_principal,

        # ahora se llaman AMENIDADES
        "amenidades": amenidades,
    }

    elapsed_total = time.time() - start_time
    print(f"[PERF] Tiempo total de solicitud: {elapsed_total:.2f}s")

    return render(request, 'webapp/habitaciones/detalle.html', contexto)


@method_decorator(csrf_exempt, name="dispatch")
class FechasOcupadasAjaxView(View):
    """
    Endpoint AJAX para obtener las fechas ocupadas de una habitación.
    Retorna un JSON con las fechas bloqueadas para el calendario.
    """
    def get(self, request, id_habitacion):
        try:
            from datetime import datetime, timedelta
            
            # 🔑 EXPIRAR HOLDs VENCIDOS ANTES DE RETORNAR FECHAS
            # Usar sync para garantizar que se complete ANTES de obtener reservas
            from servicios.hold_service import expirar_holds_sync
            expirar_holds_sync()  # Se ejecuta completamente (bloquea, pero es crítico)
            
            # Obtener todas las reservas
            api_reserva = ReservaGestionRest()
            api_habxres = HabxResGestionRest()
            
            reservas_api = api_reserva.obtener_reservas()
            habxres_list = api_habxres.obtener_habxres()
            
            # Crear índice de HabxRes por IdReserva
            idx_habxres = {h["IdReserva"]: h for h in habxres_list}
            
            # Filtrar reservas de esta habitación que estén confirmadas o en pre-reserva
            fechas_ocupadas = []
            
            for r in reservas_api:
                id_reserva = r.get("IdReserva")
                habxres = idx_habxres.get(id_reserva)
                
                if not habxres:
                    continue
                    
                # Verificar que sea la habitación correcta
                if habxres.get("IdHabitacion") != id_habitacion:
                    continue
                
                # Solo considerar reservas confirmadas o pre-reservas activas
                estado = (r.get("EstadoGeneralReserva") or "").strip().upper()
                # EXCLUIR: Canceladas y Expiradas (HOLDs que vencieron)
                if estado in ["CANCELADA", "EXPIRADO"]:
                    continue
                
                fecha_inicio = r.get("FechaInicioReserva")
                fecha_fin = r.get("FechaFinalReserva")
                
                if fecha_inicio and fecha_fin:
                    # Agregar todas las fechas del rango (incluyendo inicio y fin)
                    try:
                        inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                        fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                        
                        # Generar todas las fechas del rango
                        fecha_actual = inicio.date()
                        fecha_final = fin.date()
                        
                        while fecha_actual <= fecha_final:
                            fechas_ocupadas.append(fecha_actual.isoformat())
                            fecha_actual += timedelta(days=1)
                    except Exception as e:
                        print(f"Error al procesar fechas de reserva {id_reserva}: {e}")
                        continue
            
            # Eliminar duplicados y ordenar
            fechas_ocupadas = sorted(list(set(fechas_ocupadas)))
            
            return JsonResponse({
                "success": True,
                "fechas_ocupadas": fechas_ocupadas,
                "total_fechas": len(fechas_ocupadas)
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)
# =============================
#       CREAR PRERESERVA
# =============================
def iniciar_temporizador_hold(id_hold, duracion, api):
    print(f"[TEMPORIZADOR] HOLD {id_hold} iniciado ({duracion} segundos)")

    segundos = duracion

    while segundos > 0:
        print(f"[TEMPORIZADOR] HOLD {id_hold} → quedan {segundos} segundos")
        time.sleep(1)
        segundos -= 1

    # Tiempo terminado → cancelar HOLD
    try:
        print(f"[TEMPORIZADOR] HOLD {id_hold} EXPIRÓ. Cancelando…")
        api.cancelar_hold(id_hold)
        print(f"[TEMPORIZADOR] HOLD {id_hold} CANCELADO correctamente.")
    except Exception as e:
        print(f"[TEMPORIZADOR] Error al cancelar HOLD {id_hold}: {e}")

def crear_prereserva(request):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    # === Datos enviados desde el formulario ===
    id_habitacion = request.POST.get("idHabitacion")
    fecha_inicio = request.POST.get("fechaInicio")
    fecha_fin = request.POST.get("fechaFin")
    numero_huespedes = int(request.POST.get("numeroHuespedes", "1"))

    nombre = request.POST.get("nombre")
    apellido = request.POST.get("apellido")
    correo = request.POST.get("correo")
    tipo_documento = request.POST.get("tipoDocumento")
    documento = request.POST.get("documento")

    precio_actual = float(request.POST.get("precioActual") or 0)
    usuario_id = request.POST.get("usuarioId")

    if not usuario_id:
        return JsonResponse({"error": "Usuario no identificado"}, status=400)

    # Convertir usuario_id a int para enviarlo al API
    try:
        id_usuario_int = int(usuario_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "ID de usuario inválido"}, status=400)

    # === Llamar al servicio SOAP ===
    api = FuncionesEspecialesGestionRest()

    try:
        # 1) Crear Pre-reserva
        resultado = api.crear_prereserva(
            id_habitacion=id_habitacion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            numero_huespedes=numero_huespedes,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            tipo_documento=tipo_documento,
            documento=documento,
            duracion_hold_seg=180,
            precio_actual=precio_actual,
            id_usuario=id_usuario_int  # ← Enviar el ID del usuario logueado
        )

        # Obtener el ID del HOLD de la respuesta (puede venir con diferentes nombres)
        hold_id = resultado.get("IdHold") or resultado.get("idHold") or resultado.get("holdId")
        
        # Validar que tenemos un hold_id válido
        if not hold_id or hold_id == "":
            # Si no hay hold_id en la respuesta, intentar usar los datos directamente de la respuesta
            reserva_id = resultado.get("IdReserva") or resultado.get("idReserva")
            tiempo_hold = resultado.get("TiempoHold") or resultado.get("tiempoHold") or 180
            fecha_inicio_hold = resultado.get("FechaInicioHold") or resultado.get("fechaInicioHold") or fecha_inicio
            
            # Si tampoco tenemos reserva_id, entonces hay un problema con la respuesta
            if not reserva_id:
                return JsonResponse({
                    "error": "La respuesta del servidor no contiene la información necesaria. Respuesta recibida: " + str(resultado)
                }, status=500)
        else:
            # 2) Obtener información extendida del HOLD usando el ID
            hold_api = HoldGestionRest()
            try:
                hold = hold_api.obtener_hold_por_id(str(hold_id))
                
                if not hold:
                    # Si no se encuentra el HOLD, usar los datos de la respuesta original
                    reserva_id = resultado.get("IdReserva") or resultado.get("idReserva")
                    tiempo_hold = resultado.get("TiempoHold") or resultado.get("tiempoHold") or 180
                    fecha_inicio_hold = resultado.get("FechaInicioHold") or resultado.get("fechaInicioHold") or fecha_inicio
                else:
                    reserva_id = hold.get("IdReserva") or hold.get("idReserva")
                    tiempo_hold = hold.get("TiempoHold") or hold.get("tiempoHold") or 180
                    fecha_inicio_hold = hold.get("FechaInicioHold") or hold.get("fechaInicioHold") or fecha_inicio
            except ValueError as ve:
                # Si el error es que el ID_HOLD es obligatorio, usar los datos de la respuesta original
                reserva_id = resultado.get("IdReserva") or resultado.get("idReserva")
                tiempo_hold = resultado.get("TiempoHold") or resultado.get("tiempoHold") or 180
                fecha_inicio_hold = resultado.get("FechaInicioHold") or resultado.get("fechaInicioHold") or fecha_inicio
                
                if not reserva_id:
                    return JsonResponse({"error": f"Error al obtener el HOLD: {str(ve)}"}, status=400)
            except Exception as e:
                # Si hay otro error al obtener el HOLD, usar los datos de la respuesta original
                reserva_id = resultado.get("IdReserva") or resultado.get("idReserva")
                tiempo_hold = resultado.get("TiempoHold") or resultado.get("tiempoHold") or 180
                fecha_inicio_hold = resultado.get("FechaInicioHold") or resultado.get("fechaInicioHold") or fecha_inicio
                
                if not reserva_id:
                    return JsonResponse({"error": f"Error al obtener información del HOLD: {str(e)}"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # === Redirigir con datos correctos ===
    return redirect(
        f"/usuario/reservas/?uid={usuario_id}"
        f"&reserva={reserva_id}"
        f"&ini={fecha_inicio_hold}"
        f"&t={tiempo_hold}"
    )



# =============================
#       RESERVAS
# =============================
def index_reservas(request):
    # Aquí se puede consumir:
    # https://reca.azurewebsites.net/api/v1/hoteles/hold
    return render(request, 'webapp/reservas/index.html')

# =============================
#       LOGIN Y REGISTER
# =============================
def index_login(request):
    return render(request, "webapp/login/index.html")


def login_post(request):
    if request.method != "POST":
        return redirect("login")

    correo = request.POST.get("correo")
    clave = request.POST.get("clave")

    api = UsuarioInternoGestionRest()

    try:
        respuesta = api.login(correo, clave)

        # Validar respuesta del API
        if not respuesta or "Id" not in respuesta:
            messages.error(request, "Credenciales incorrectas.")
            return redirect("login")

        usuario = {
            "id": respuesta["Id"],
            "correo": respuesta["Correo"],
            "nombre": respuesta.get("Nombre", ""),
            "apellido": respuesta.get("Apellido", ""),
            "rol": respuesta.get("IdRol"),
            "tipo_doc": respuesta.get("TipoDocumento", ""),
            "documento": respuesta.get("Documento", ""),
            "fecha_nac": respuesta.get("FechaNacimiento", ""),
        }

        # → Crear respuesta HTML con JavaScript para guardar en localStorage y redirigir
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Iniciando sesión...</title></head>
        <body>
            <script>
                // Guardar datos del usuario en localStorage
                localStorage.setItem("usuario_id", "{usuario['id']}");
                localStorage.setItem("usuario_correo", "{usuario['correo']}");
                localStorage.setItem("usuario_nombre", "{usuario['nombre']}");
                localStorage.setItem("usuario_apellido", "{usuario['apellido']}");
                localStorage.setItem("usuario_rol", "{usuario['rol']}");
                localStorage.setItem("usuario_tipo_doc", "{usuario['tipo_doc']}");
                localStorage.setItem("usuario_documento", "{usuario['documento']}");
                localStorage.setItem("usuario_fecha_nac", "{usuario['fecha_nac']}");
                
                // Redirigir inmediatamente
                window.location.href = "/";
            </script>
        </body>
        </html>
        """
        
        response = HttpResponse(html_response)
        
        # Establecer cookies de sesión del servidor
        response.set_cookie('usuario_rol', str(usuario['rol']), max_age=86400, httponly=False, samesite='Lax')
        response.set_cookie('usuario_id', str(usuario['id']), max_age=86400, httponly=False, samesite='Lax')

        return response


    except Exception as e:
        # Detectar el tipo de error y mostrar mensaje apropiado
        error_msg = str(e).lower()
        
        if "401" in error_msg or "unauthorized" in error_msg or "credenciales" in error_msg:
            messages.error(request, "Correo o contraseña incorrectos. Por favor, verifica tus credenciales e intenta nuevamente.")
        elif "conexión" in error_msg or "connection" in error_msg:
            messages.error(request, "No se pudo conectar al servidor. Verifica tu conexión a internet.")
        else:
            messages.error(request, "No se pudo iniciar sesión. Por favor, intenta nuevamente.")
        
        return redirect("login")



def index_register(request):
    return render(request, 'webapp/register/index.html')
def register_post(request):
    if request.method != "POST":
        return redirect("register")

    nombre = request.POST.get("nombre")
    apellido = request.POST.get("apellido")
    correo = request.POST.get("correo")
    clave = request.POST.get("clave")
    tipo_documento = request.POST.get("tipo_documento")
    documento = request.POST.get("documento")

    # Construir DTO que el API espera
    payload = {
        "Id": 0,
        "IdRol": 1,  # Usuario normal
        "Nombre": nombre,
        "Apellido": apellido,
        "Correo": correo,
        "Clave": clave,  # API la encripta
        "Estado": True,
        "TipoDocumento": tipo_documento,
        "Documento": documento,
        "FechaNacimiento": None,
    }

    api = UsuarioInternoGestionRest()

    try:
        nuevo = api.crear(payload)

        if not nuevo:
            messages.error(request, "No se pudo crear la cuenta.")
            return redirect("register")

        messages.success(request, "Cuenta creada correctamente. Ahora puedes iniciar sesión.")
        return redirect("login")

    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect("register")


# views_webapp.py



class MisReservasView(View):

    template_name = "webapp/reservas/index.html"

    def get(self, request):
        import time
        start_time = time.time()

        api_reserva = ReservaGestionRest()
        api_habxres = HabxResGestionRest()
        api_habs = HabitacionesGestionRest()
        api_imgs = ImagenHabitacionGestionRest()
        api_hold = HoldGestionRest()

        usuario_id = request.GET.get("uid")
        usuario_correo = None  # Django NO tiene acceso a localStorage
        
        if not usuario_id:
            return render(request, self.template_name, {
                "reservas": [],
                "error": "No se pudo determinar el usuario logeado."
            })
        
        try:
            usuario_id_int = int(usuario_id)
        except (ValueError, TypeError):
            return render(request, self.template_name, {
                "reservas": [],
                "error": "ID de usuario inválido."
            })
        
        # SEGURIDAD: Validar que el usuario solo pueda ver sus propias reservas
        usuario_cookie = request.COOKIES.get('usuario_id')
        
        if usuario_cookie:
            try:
                usuario_logueado = int(usuario_cookie)
                if usuario_logueado != usuario_id_int:
                    return render(request, self.template_name, {
                        "reservas": [],
                        "error": "No tiene permisos para ver esta información. Por favor, inicie sesión."
                    })
            except (ValueError, TypeError):
                return render(request, self.template_name, {
                    "reservas": [],
                    "error": "Sesión inválida. Por favor, inicie sesión nuevamente."
                })
        else:
            return render(request, self.template_name, {
                "reservas": [],
                "error": "Debe iniciar sesión para ver sus reservas."
            })

        # -----------------------------------
        # OPTIMIZACIÓN: Cargar datos en paralelo
        # -----------------------------------
        datos = {
            "reservas_api": None,
            "habxres_list": None,
            "hold_list": None,
            "imgs_list": None,
        }

        def cargar_reservas():
            datos["reservas_api"] = api_reserva.obtener_reservas()

        def cargar_habxres():
            datos["habxres_list"] = api_habxres.obtener_habxres()

        def cargar_hold():
            datos["hold_list"] = api_hold.obtener_hold()

        def cargar_imagenes():
            datos["imgs_list"] = api_imgs.obtener_imagenes()

        # Ejecutar en paralelo
        threads = [
            threading.Thread(target=cargar_reservas),
            threading.Thread(target=cargar_habxres),
            threading.Thread(target=cargar_hold),
            threading.Thread(target=cargar_imagenes),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        reservas_api = datos["reservas_api"] or []
        habxres_list = datos["habxres_list"] or []
        hold_list = datos["hold_list"] or []
        imgs_list = datos["imgs_list"] or []

        # Obtener el ID de reserva específico de la URL (si existe)
        reserva_id_url = request.GET.get("reserva")
        
        print(f"[DEBUG MisReservasView] Usuario ID: '{usuario_id}' (tipo: {type(usuario_id)}), Reserva ID URL: {reserva_id_url}")
        print(f"[DEBUG MisReservasView] Total reservas API: {len(reservas_api)}")
        
        # Verificar si reservas_api es una lista
        if not isinstance(reservas_api, list):
            print(f"[ERROR] reservas_api no es una lista, es: {type(reservas_api)}")
            reservas_api = []
        
        # Filtrar reservas del usuario
        # Incluir:
        # 1. Reservas que pertenecen al usuario (IdUnicoUsuario == usuario_id)
        # 2. La reserva específica de la URL (si existe)
        reservas_filtradas = []
        reserva_especifica = None
        
        # Si hay una reserva específica en la URL, intentar obtenerla directamente si no está en la lista
        if reserva_id_url:
            # Buscar en la lista de reservas
            for r in reservas_api:
                if str(r.get("IdReserva")) == str(reserva_id_url):
                    reserva_especifica = r
                    print(f"[DEBUG MisReservasView] Reserva {reserva_id_url} encontrada en lista API")
                    break
            
            # Si no se encuentra en la lista, obtenerla directamente del API
            if not reserva_especifica:
                try:
                    reserva_especifica = api_reserva.obtener_reserva_por_id(int(reserva_id_url))
                    if reserva_especifica:
                        print(f"[DEBUG MisReservasView] Reserva {reserva_id_url} obtenida directamente del API")
                        # Agregar a la lista de reservas para que se procese
                        reservas_api.append(reserva_especifica)
                except Exception as e:
                    print(f"[ERROR] Error al obtener reserva {reserva_id_url}: {e}")
        
        # Filtrar reservas
        # Primero, revisar algunas reservas para debug
        print(f"[DEBUG MisReservasView] Revisando primeras 5 reservas para debug:")
        for i, r in enumerate(reservas_api[:5]):
            id_res = r.get("IdReserva")
            id_usuario = r.get("IdUnicoUsuario")
            print(f"[DEBUG MisReservasView] Reserva {i+1}: IdReserva={id_res}, IdUnicoUsuario={id_usuario} (tipo: {type(id_usuario)})")
        
        # Buscar específicamente la reserva 158
        for r in reservas_api:
            if r.get("IdReserva") == 158:
                print(f"[DEBUG MisReservasView] Reserva 158 encontrada: IdUnicoUsuario={r.get('IdUnicoUsuario')} (tipo: {type(r.get('IdUnicoUsuario'))})")
                break
        
        for r in reservas_api:
            id_res = r.get("IdReserva")
            if not id_res:
                continue
                
            # Intentar obtener IdUnicoUsuario de diferentes formas posibles
            id_usuario_reserva = (
                r.get("IdUnicoUsuario") or 
                r.get("idUnicoUsuario") or 
                r.get("ID_UNICO_USUARIO") or
                r.get("IdUnicoUsuarioInterno")
            )
            
            # Si es la reserva específica de la URL, incluirla siempre
            if reserva_id_url and str(id_res) == str(reserva_id_url):
                reservas_filtradas.append(r)
                print(f"[DEBUG MisReservasView] Reserva {id_res} agregada (reserva específica de URL)")
                continue
            
            # Incluir si pertenece al usuario (comparar como strings para evitar problemas de tipo)
            # También manejar el caso donde id_usuario_reserva puede ser 0 (que es falsy pero válido)
            if id_usuario_reserva is not None:
                if str(id_usuario_reserva).strip() == str(usuario_id).strip():
                    reservas_filtradas.append(r)
                    print(f"[DEBUG MisReservasView] Reserva {id_res} agregada (pertenece al usuario {id_usuario_reserva})")
                elif id_res == 158:  # Debug específico para la reserva 158
                    print(f"[DEBUG MisReservasView] Reserva 158 NO agregada: id_usuario_reserva='{id_usuario_reserva}' (tipo: {type(id_usuario_reserva)}), usuario_id='{usuario_id}' (tipo: {type(usuario_id)})")
        
        # Si hay una reserva específica de la URL, asegurarse de que esté en la lista
        if reserva_especifica:
            id_res_esp = reserva_especifica.get("IdReserva")
            if id_res_esp and not any(r.get("IdReserva") == id_res_esp for r in reservas_filtradas):
                reservas_filtradas.insert(0, reserva_especifica)
                print(f"[DEBUG MisReservasView] Reserva específica {id_res_esp} agregada al inicio")
        
        print(f"[DEBUG MisReservasView] Total reservas filtradas: {len(reservas_filtradas)}")

        # Crear índices
        idx_habxres = {h["IdReserva"]: h for h in habxres_list}
        idx_hold = {h["IdReserva"]: h for h in hold_list}
        
        # Crear índice de imágenes por habitación (optimización)
        idx_imagenes = {}
        for img in imgs_list:
            if img.get("EstadoImagen"):
                hab_id = img.get("IdHabitacion")
                if hab_id not in idx_imagenes:
                    idx_imagenes[hab_id] = img.get("UrlImagen")

        # Crear índice de habitaciones (cargar solo las necesarias)
        habitaciones_ids = set()
        for r in reservas_filtradas:
            id_res = r.get("IdReserva")
            hxr = idx_habxres.get(id_res, {})
            id_habitacion = hxr.get("IdHabitacion")
            if id_habitacion:
                habitaciones_ids.add(id_habitacion)
        
        # Si hay una reserva específica en la URL, asegurarse de incluir su habitación
        if reserva_id_url:
            for hxr in habxres_list:
                if str(hxr.get("IdReserva")) == str(reserva_id_url):
                    id_habitacion = hxr.get("IdHabitacion")
                    if id_habitacion:
                        habitaciones_ids.add(id_habitacion)
                    break
            
            # Si no se encuentra en HABXRES, intentar obtenerla del HOLD
            if not any(str(hxr.get("IdReserva")) == str(reserva_id_url) for hxr in habxres_list):
                for h in hold_list:
                    if str(h.get("IdReserva")) == str(reserva_id_url):
                        id_habitacion = h.get("IdHabitacion")
                        if id_habitacion:
                            habitaciones_ids.add(id_habitacion)
                        break

        # Cargar habitaciones en paralelo
        idx_habitaciones = {}
        def cargar_habitacion(hab_id):
            try:
                hab_data = api_habs.obtener_por_id(hab_id)
                idx_habitaciones[hab_id] = hab_data
            except:
                idx_habitaciones[hab_id] = {}

        threads_hab = [threading.Thread(target=cargar_habitacion, args=(hab_id,)) for hab_id in habitaciones_ids]
        for t in threads_hab:
            t.start()
        for t in threads_hab:
            t.join()

        reservas_final = []

        # -----------------------------------
        # CONSTRUIR RESERVAS
        # -----------------------------------
        for r in reservas_filtradas:
            id_res = r.get("IdReserva")

            # HABXRES
            hxr = idx_habxres.get(id_res, {})
            id_habitacion = hxr.get("IdHabitacion")

            # HOLD
            hold = idx_hold.get(id_res, {})
            id_hold = hold.get("IdHold")

            # HABITACIÓN (desde índice)
            hab_data = idx_habitaciones.get(id_habitacion, {})
            capacidad_habitacion = hab_data.get("CapacidadHabitacion")

            # IMAGEN (desde índice)
            imagen_final = idx_imagenes.get(id_habitacion) or "https://imageness3realdecuenca.s3.us-east-2.amazonaws.com/Imagen4.png"

            estado_reserva = (r.get("EstadoGeneralReserva") or "Pendiente").strip().upper()

            reservas_final.append({
                "idReserva": id_res,
                "idUsuario": r.get("IdUnicoUsuario"),

                "idHabitacion": id_habitacion,
                "idHold": id_hold,

                "habitacion": hab_data.get("NombreHabitacion") or "",
                "hotel": hab_data.get("NombreHotel") or "",
                "ciudad": hab_data.get("NombreCiudad") or "",
                "pais": hab_data.get("NombrePais") or "",

                "fecha_inicio": (r.get("FechaInicioReserva") or "")[:10],
                "fecha_fin": (r.get("FechaFinalReserva") or "")[:10],
                "huespedes": hxr.get("CapacidadReservaHabxRes") or 1,
                "estado": estado_reserva,

                "subtotal": hxr.get("CostoCalculadoHabxRes") or 0,
                "total_descuentos": hxr.get("DescuentoHabxRes") or 0,
                "total_impuestos": hxr.get("ImpuestosHabxRes") or 0,
                "total": r.get("CostoTotalReserva") or 0,

                "capacidad_escogida": hxr.get("CapacidadReservaHabxRes"),
                "capacidad_habitacion": capacidad_habitacion,
                "imagen": imagen_final,
                "usuario_correo": usuario_correo,
            })

        elapsed = time.time() - start_time
        print(f"[PERF] MisReservasView: {elapsed:.2f}s")
        print(f"[DEBUG MisReservasView] Total reservas finales enviadas al template: {len(reservas_final)}")
        for rf in reservas_final:
            print(f"[DEBUG MisReservasView] - Reserva {rf.get('idReserva')}: estado={rf.get('estado')}, hab={rf.get('idHabitacion')}, hold={rf.get('idHold')}, usuario={rf.get('idUsuario')}")

        return render(request, self.template_name, {"reservas": reservas_final})



@method_decorator(csrf_exempt, name="dispatch")
class ConfirmarReservaInternaAjax(View):

    def post(self, request):
        try:
            import json

            # ========= LOGS DE ENTRADA =========
            print("\n" + "="*80)
            print("[DEBUG ConfirmarReserva] >>> INICIO POST /usuario/confirmar-reserva/")
            print(f"[DEBUG ConfirmarReserva] Raw body: {request.body!r}")

            try:
                data = json.loads(request.body)
            except Exception as e:
                print(f"[ERROR ConfirmarReserva] Error parseando JSON: {e}")
                return JsonResponse({"ok": False, "error": f"JSON inválido: {e}"}, status=400)

            print(f"[DEBUG ConfirmarReserva] data recibido: {data}")

            id_habitacion = data.get("idHabitacion")
            id_hold = data.get("idHold")
            id_usuario_str = data.get("idUnicoUsuario")
            fecha_inicio = data.get("fechaInicio")
            fecha_fin = data.get("fechaFin")
            huespedes_str = data.get("numeroHuespedes")

            print("[DEBUG ConfirmarReserva] Campos crudos:")
            print(f"  idHabitacion = {id_habitacion} ({type(id_habitacion)})")
            print(f"  idHold       = {id_hold} ({type(id_hold)})")
            print(f"  idUnicoUsuario = {id_usuario_str} ({type(id_usuario_str)})")
            print(f"  fechaInicio  = {fecha_inicio} ({type(fecha_inicio)})")
            print(f"  fechaFin     = {fecha_fin} ({type(fecha_fin)})")
            print(f"  numeroHuespedes = {huespedes_str} ({type(huespedes_str)})")

            # ========= Validaciones básicas =========
            if not id_habitacion:
                print("[ERROR ConfirmarReserva] Falta idHabitacion")
                return JsonResponse({"ok": False, "error": "idHabitacion es obligatorio"}, status=400)
            if not id_hold:
                print("[ERROR ConfirmarReserva] Falta idHold")
                return JsonResponse({"ok": False, "error": "idHold es obligatorio"}, status=400)
            if not id_usuario_str:
                print("[ERROR ConfirmarReserva] Falta idUnicoUsuario")
                return JsonResponse({"ok": False, "error": "idUnicoUsuario es obligatorio"}, status=400)
            if not fecha_inicio:
                print("[ERROR ConfirmarReserva] Falta fechaInicio")
                return JsonResponse({"ok": False, "error": "fechaInicio es obligatoria"}, status=400)
            if not fecha_fin:
                print("[ERROR ConfirmarReserva] Falta fechaFin")
                return JsonResponse({"ok": False, "error": "fechaFin es obligatoria"}, status=400)
            if huespedes_str in (None, "", "null"):
                print("[ERROR ConfirmarReserva] Falta numeroHuespedes")
                return JsonResponse({"ok": False, "error": "numeroHuespedes es obligatorio"}, status=400)

            # ========= Conversión de tipos =========
            try:
                id_usuario = int(id_usuario_str)
                print(f"[DEBUG ConfirmarReserva] id_usuario (int) = {id_usuario}")
            except (ValueError, TypeError) as e:
                print(f"[ERROR ConfirmarReserva] idUnicoUsuario inválido: {e}")
                return JsonResponse({"ok": False, "error": "idUnicoUsuario debe ser un número válido"}, status=400)

            try:
                huespedes = int(huespedes_str)
                print(f"[DEBUG ConfirmarReserva] numeroHuespedes (int) = {huespedes}")
            except (ValueError, TypeError) as e:
                print(f"[ERROR ConfirmarReserva] numeroHuespedes inválido: {e}")
                return JsonResponse({"ok": False, "error": "numeroHuespedes debe ser un número válido"}, status=400)

            if huespedes <= 0:
                print("[ERROR ConfirmarReserva] numeroHuespedes <= 0")
                return JsonResponse({"ok": False, "error": "numeroHuespedes debe ser mayor que 0"}, status=400)

            # ========= IMPORTANTE: Obtener el número de huéspedes del HOLD =========
            # El SP requiere que el número de huéspedes coincida exactamente con lo reservado en HABXRES
            # HABXRES.CAPACIDAD_RESERVA_HABXRES se establece durante la pre-reserva
            # y debe coincidir exactamente al confirmar
            try:
                from servicios.rest.gestion.HoldGestionRest import HoldGestionRest
                from servicios.rest.gestion.ReservaGestionRest import ReservaGestionRest
                
                hold_api = HoldGestionRest()
                hold_info = hold_api.obtener_hold_por_id(id_hold)
                
                huespedes_hold = None
                id_reserva_from_hold = None
                if hold_info:
                    print(f"[DEBUG ConfirmarReserva] Hold info: {hold_info}")
                    id_reserva_from_hold = (
                        hold_info.get("IdReserva") or 
                        hold_info.get("idReserva") or
                        hold_info.get("ID_RESERVA")
                    )
                    
                    # Intentar obtener numeroHuespedes del HOLD
                    huespedes_hold = (
                        hold_info.get("NumeroHuespedes") or 
                        hold_info.get("numeroHuespedes") or
                        hold_info.get("NUMERO_HUESPEDES")
                    )
                
                # Si no lo encontramos en HOLD, intentar desde RESERVA
                if not huespedes_hold and id_reserva_from_hold:
                    try:
                        reserva_api = ReservaGestionRest()
                        reserva_info = reserva_api.obtener_reserva_por_id(id_reserva_from_hold)
                        if reserva_info:
                            print(f"[DEBUG ConfirmarReserva] Reserva info: {reserva_info}")
                            huespedes_hold = (
                                reserva_info.get("NumeroHuespedes") or
                                reserva_info.get("numeroHuespedes") or
                                reserva_info.get("NUMERO_HUESPEDES")
                            )
                    except Exception as e:
                        print(f"[WARN ConfirmarReserva] Error al obtener Reserva: {e}")
                
                if huespedes_hold:
                    print(f"[DEBUG ConfirmarReserva] Número de huéspedes del HOLD/RESERVA: {huespedes_hold}")
                    huespedes = int(huespedes_hold)
                else:
                    # El número de huéspedes NO está disponible en los APIs
                    # Usaremos el del request y confiamos en que coincide con HABXRES
                    print(f"[INFO ConfirmarReserva] No se pudo obtener numeroHuespedes de APIs, usando del request: {huespedes}")
                    print(f"[INFO ConfirmarReserva] IMPORTANTE: El SP validará que coincida con HABXRES.CAPACIDAD_RESERVA_HABXRES")
            except Exception as e:
                print(f"[WARN ConfirmarReserva] Error al obtener HOLD: {e}. Usando numeroHuespedes del request: {huespedes}")

            # ========= (OPCIONAL) Ver capacidad vs huésped =========
            try:
                from servicios.rest.gestion.HabitacionesGestionRest import HabitacionesGestionRest
                api_hab = HabitacionesGestionRest()
                hab_info = api_hab.obtener_por_id(id_habitacion)
                cap_hab = hab_info.get("CapacidadHabitacion") if hab_info else None
                print(f"[DEBUG ConfirmarReserva] CapacidadHabitacion={cap_hab} vs numeroHuespedes={huespedes}")
            except Exception as e:
                print(f"[WARN ConfirmarReserva] No se pudo obtener capacidad de la habitación: {e}")

            # 1) Obtener datos del usuario desde el API
            api_usuario = UsuarioInternoGestionRest()
            try:
                usuario_data = api_usuario.obtener_por_id(id_usuario)
                print(f"[DEBUG ConfirmarReserva] Datos del usuario obtenidos: {usuario_data}")
                
                nombre = (
                    usuario_data.get("NombreUsuario") or 
                    usuario_data.get("nombreUsuario") or 
                    usuario_data.get("Nombre") or
                    usuario_data.get("nombre")
                )
                apellido = (
                    usuario_data.get("ApellidoUsuario") or 
                    usuario_data.get("apellidoUsuario") or 
                    usuario_data.get("Apellido") or
                    usuario_data.get("apellido")
                )
                correo = (
                    usuario_data.get("EmailUsuario") or 
                    usuario_data.get("emailUsuario") or 
                    usuario_data.get("Correo") or
                    usuario_data.get("correo") or
                    usuario_data.get("Email") or
                    usuario_data.get("email")
                )
                tipo_documento = (
                    usuario_data.get("TipoDocumentoUsuario") or 
                    usuario_data.get("tipoDocumentoUsuario") or 
                    usuario_data.get("TipoDocumento") or
                    usuario_data.get("tipoDocumento")
                )
                documento = (
                    usuario_data.get("DocumentoUsuario") or 
                    usuario_data.get("documentoUsuario") or 
                    usuario_data.get("Documento") or
                    usuario_data.get("documento")
                )
                
                print(f"[DEBUG ConfirmarReserva] Datos extraídos - nombre: {nombre}, apellido: {apellido}, correo: {correo}, tipo_doc: {tipo_documento}, documento: {documento}")
                
            except Exception as e:
                print(f"[ERROR ConfirmarReserva] Error al obtener datos del usuario: {e}")
                return JsonResponse({"ok": False, "error": f"Error al obtener datos del usuario: {str(e)}"}, status=400)

            if not correo:
                print(f"[ERROR ConfirmarReserva] No se pudo obtener el correo. Datos completos del usuario: {usuario_data}")
                return JsonResponse({"ok": False, "error": f"No se pudo obtener el correo del usuario. Datos recibidos: {list(usuario_data.keys()) if usuario_data else 'None'}"}, status=400)

            api = FuncionesEspecialesGestionRest()

            # ========= LOG DEL PAYLOAD QUE VAS A MANDAR AL API =========
            payload_confirmacion = {
                "id_habitacion": id_habitacion,
                "id_hold": id_hold,
                "nombre": nombre,
                "apellido": apellido,
                "correo": correo,
                "tipo_documento": tipo_documento,
                "documento": documento,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "numero_huespedes": huespedes,
            }
            print(f"[DEBUG ConfirmarReserva] Payload para confirmar_reserva_interna: {payload_confirmacion}")

            # 2) Confirmar reserva interna
            try:
                resultado = api.confirmar_reserva_interna(**payload_confirmacion)
                print(f"[DEBUG ConfirmarReserva] Resultado confirmar_reserva_interna: {resultado}")
            except Exception as e:
                import traceback
                print(f"[ERROR ConfirmarReserva] Excepción en confirmar_reserva_interna: {e}")
                print(traceback.format_exc())
                return JsonResponse({"ok": False, "error": f"Error al confirmar reserva interna: {str(e)}"}, status=400)

            id_reserva = resultado.get("IdReserva")
            costo_total = resultado.get("CostoTotalReserva") or 0
            
            if not id_reserva:
                return JsonResponse({"ok": False, "error": "No se pudo obtener idReserva del resultado de confirmación."})

            # 3) Realizar pago usando el API del banco
            from servicios.rest.integracion.BancoRest import BancoRest
            
            api_banco = BancoRest()
            
            # Obtener el documento del usuario para el pago
            documento_pago = documento
            if not documento_pago:
                return JsonResponse({"ok": False, "error": "No se pudo obtener el documento del usuario para realizar el pago"}, status=400)
            
            try:
                # Realizar pago desde la cuenta compartida del cliente hacia la cuenta del hotel
                resultado_pago = api_banco.realizar_pago(
                    cedula_cliente=documento_pago,
                    monto=float(costo_total)
                )
                
                if not resultado_pago.get("ok"):
                    return JsonResponse({
                        "ok": False, 
                        "error": f"Error al realizar el pago en el banco: {resultado_pago.get('mensaje', 'Error desconocido')}"
                    }, status=400)
                
                print(f"[DEBUG ConfirmarReserva] Pago BANCO realizado exitosamente: {resultado_pago.get('mensaje')}")
                
            except Exception as e:
                print(f"[ERROR ConfirmarReserva] Error al realizar pago en banco: {e}")
                import traceback
                print(f"[ERROR ConfirmarReserva] Traceback BANCO: {traceback.format_exc()}")
                return JsonResponse({"ok": False, "error": f"Error al realizar el pago: {str(e)}"}, status=400)

            # 4) Registrar pago en el microservicio de HOTELES (tabla PAGO)
            from servicios.rest.gestion.PagoGestionRest import PagoGestionRest
            api_pagos = PagoGestionRest()

            try:
                print(f"[DEBUG ConfirmarReserva] Registrando PAGO en HOTELES: reserva={id_reserva}, usuario={id_usuario}, monto={costo_total}")
                pago = api_pagos.registrar_pago_reserva_interna(
                    id_reserva=id_reserva,
                    id_unico_usuario=id_usuario,
                    monto_total=float(costo_total),
                    cuenta_origen=BancoRest.CUENTA_CLIENTE,
                    cuenta_destino=BancoRest.CUENTA_HOTEL,
                    id_unico_usuario_externo=None,
                    id_metodo_pago=2
                )
                print(f"[DEBUG ConfirmarReserva] PAGO HOTELES registrado correctamente: {pago}")
            except Exception as e:
                print(f"[ERROR ConfirmarReserva] Error al registrar PAGO en HOTELES: {e}")
                import traceback
                print(f"[ERROR ConfirmarReserva] Traceback PAGO: {traceback.format_exc()}")
                return JsonResponse({"ok": False, "error": f"Error al registrar el pago en el sistema de hoteles: {str(e)}"}, status=400)

            # 5) NO emitir factura automáticamente - se hará desde el botón "Generar Factura" en la página de pagos
            
            return JsonResponse({
                "ok": True,
                "reserva": resultado,
                "mensaje": "Reserva confirmada y pago realizado exitosamente. Puede generar la factura desde la página de pagos."
            })

        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)




# views_webapp.py

from django.http import JsonResponse
from django.views import View

from servicios.rest.gestion.FuncionesEspecialesGestionRest import FuncionesEspecialesGestionRest


class CancelarReservaAjax(View):
    """
    Cancela una pre-reserva desde el botón en Mis Reservas.
    """

    def post(self, request):
        try:
            import json
            data = json.loads(request.body)

            # Puede venir idHold directamente o idReserva para buscarlo
            id_hold = data.get("idHold")
            id_reserva = data.get("idReserva")

            if not id_hold and not id_reserva:
                return JsonResponse({"ok": False, "error": "idHold o idReserva es obligatorio"}, status=400)

            # Si ya tenemos el idHold, usarlo directamente
            if id_hold:
                print(f"[DEBUG CancelarReserva] Usando idHold directamente: {id_hold}")
            else:
                # Si no, buscar el HOLD por idReserva
                print(f"[DEBUG CancelarReserva] Buscando HOLD para reserva {id_reserva}")

                api_hold = HoldGestionRest()
                try:
                    holds = api_hold.obtener_hold()
                except Exception as e:
                    print(f"[ERROR CancelarReserva] Error al obtener HOLDs: {e}")
                    return JsonResponse({"ok": False, "error": f"Error al obtener HOLDs: {str(e)}"}, status=500)

                id_hold = None
                for h in holds:
                    h_id_reserva = h.get("IdReserva") or h.get("idReserva")
                    if str(h_id_reserva) == str(id_reserva):
                        id_hold = h.get("IdHold") or h.get("idHold")
                        print(f"[DEBUG CancelarReserva] HOLD encontrado: {id_hold}")
                        break

                if not id_hold:
                    print(f"[ERROR CancelarReserva] No se encontró HOLD para reserva {id_reserva}")
                    return JsonResponse({"ok": False, "error": f"No se encontró HOLD asociado a la reserva {id_reserva}"}, status=404)

            # 2) Llamar al microservicio REST
            api = FuncionesEspecialesGestionRest()
            try:
                resultado = api.cancelar_prereserva(id_hold)
                print(f"[DEBUG CancelarReserva] Pre-reserva cancelada exitosamente: {resultado}")
                return JsonResponse({
                    "ok": True,
                    "resultado": resultado
                })
            except Exception as e:
                print(f"[ERROR CancelarReserva] Error al cancelar pre-reserva: {e}")
                return JsonResponse({"ok": False, "error": f"Error al cancelar la pre-reserva: {str(e)}"}, status=400)

        except Exception as e:
            print(f"[ERROR CancelarReserva] Error general: {e}")
            return JsonResponse({"ok": False, "error": str(e)}, status=400)


class MisPagosView(View):
    def get(self, request, *args, **kwargs):
        # logica
        #correo, pero realmente no hace nada, solo ejecutamos la api
        # http://mibanca.runasp.net/api/Transacciones/{cuenta_origen}/{cuenta_destino}/{monto}
        # y se ejecuta los dos rest o soap de
        None
def usuario_gestion(request):
    """
    Vista: Gestión del perfil del usuario.
    - Solo renderiza la página.
    - La actualización se realiza vía fetch() desde el HTML (REST PUT).
    """

    # NOTA:
    # No usamos request.session porque ahora manejas todo con localStorage
    # El HTML tomará los valores desde localStorage.

    return render(request, "webapp/usuario/cliente/gestion/index.html")

from django.shortcuts import render

@admin_required
def usuario_gestion_administrador(request):
    """
    Vista principal del panel administrativo.
    Solo accesible para usuarios con rol = 2 (administrador).
    """
    return render(request, "webapp/usuario/administrador/gestion/index.html")

def mis_pagos(request):
    import time
    start_time = time.time()

    usuario_id = request.GET.get("uid")

    if not usuario_id:
        return render(request, "webapp/pagos/index.html", {
            "pagos": [],
            "error": "Debe iniciar sesión para ver sus pagos."
        })

    try:
        usuario_id = int(usuario_id)
    except (ValueError, TypeError):
        return render(request, "webapp/pagos/index.html", {
            "pagos": [],
            "error": "ID de usuario inválido."
        })
    
    # SEGURIDAD: Validar que el usuario solo pueda ver sus propios pagos
    # Verificar con la cookie del usuario logueado
    usuario_cookie = request.COOKIES.get('usuario_id')
    
    if usuario_cookie:
        try:
            usuario_logueado = int(usuario_cookie)
            if usuario_logueado != usuario_id:
                # El usuario está intentando ver los pagos de otro usuario
                return render(request, "webapp/pagos/index.html", {
                    "pagos": [],
                    "error": "No tiene permisos para ver esta información. Por favor, inicie sesión."
                })
        except (ValueError, TypeError):
            return render(request, "webapp/pagos/index.html", {
                "pagos": [],
                "error": "Sesión inválida. Por favor, inicie sesión nuevamente."
            })
    else:
        # No hay cookie de sesión
        return render(request, "webapp/pagos/index.html", {
            "pagos": [],
            "error": "Debe iniciar sesión para ver sus pagos."
        })

    api_pagos = PagoGestionRest()
    api_facturas = FacturasGestionRest()
    api_pdf = PdfGestionRest()

    # OPTIMIZACIÓN: Cargar datos en paralelo
    datos = {
        "lista_pagos": None,
        "lista_facturas": None,
        "lista_pdfs": None,
    }

    def cargar_pagos():
        datos["lista_pagos"] = api_pagos.obtener_pagos()

    def cargar_facturas():
        datos["lista_facturas"] = api_facturas.obtener_facturas()

    def cargar_pdfs():
        datos["lista_pdfs"] = api_pdf.obtener_pdfs()

    threads = [
        threading.Thread(target=cargar_pagos),
        threading.Thread(target=cargar_facturas),
        threading.Thread(target=cargar_pdfs),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    try:
        lista_pagos = datos["lista_pagos"]
        lista_facturas = datos["lista_facturas"]
        lista_pdfs = datos["lista_pdfs"]
    except Exception as e:
        return render(request, "webapp/pagos/index.html", {
            "pagos": [],
            "error": f"Error al conectar con el servidor: {e}"
        })

    # Convertir facturas por ID
    facturas_dict = {f["IdFactura"]: f for f in lista_facturas}

    # Convertir pdfs por factura
    pdf_por_factura = {}
    for p in lista_pdfs:
        fid = p.get("IdFactura")
        if fid:
            pdf_por_factura[fid] = p

    # Obtener datos del usuario para pre-llenar el formulario de factura
    api_usuario = UsuarioInternoGestionRest()
    usuario_data = None
    try:
        usuario_data = api_usuario.obtener_por_id(usuario_id)
    except Exception as e:
        print(f"[ERROR mis_pagos] Error al obtener datos del usuario: {e}")

    # Filtrar pagos del usuario
    pagos_usuario = [
        p for p in lista_pagos if p.get("IdUnicoUsuario") == usuario_id
    ]

    # DEBUG: Ver qué pagos se están filtrando
    print(f"[DEBUG mis_pagos] Total pagos del usuario: {len(pagos_usuario)}")
    if pagos_usuario:
        print(f"[DEBUG mis_pagos] Primer pago (ejemplo): {pagos_usuario[0]}")

    pagos_final = []

    for p in pagos_usuario:
        fid = p.get("IdFactura")
        id_reserva_pago = p.get("IdReserva")
        
        # DEBUG: Ver si IdReserva existe en cada pago
        print(f"[DEBUG mis_pagos] Pago {p.get('IdPago')} - IdReserva: {id_reserva_pago} (tipo: {type(id_reserva_pago)})")

        factura = facturas_dict.get(fid)
        pdf = pdf_por_factura.get(fid)

        estado_pdf = None
        url_pdf = None

        if pdf:
            estado_pdf = pdf.get("EstadoPdf")
            url_pdf = pdf.get("UrlPdf")

        # reparar fecha
        raw_fecha = p.get("FechaEmisionPago")
        fecha = ""
        if raw_fecha and isinstance(raw_fecha, str):
            if "-" in raw_fecha:
                fecha = raw_fecha[:10]
            else:
                fecha = "Fecha no disponible"

        pagos_final.append({
            "id": p.get("IdPago"),
            "id_reserva": p.get("IdReserva"),  # Agregar id_reserva para generar factura
            "factura_id": fid,
            "monto": p.get("MontoTotalPago"),
            "fecha": fecha,
            "estado": "Pagado" if p.get("EstadoPago") else "Pendiente",
            "cuenta_origen": p.get("CuentaOrigenPago"),
            "cuenta_destino": p.get("CuentaDestinoPago"),
            "metodo": p.get("IdMetodoPago"),

            # Datos factura
            "factura": factura,
            "pdf_estado": estado_pdf,
            "pdf_url": url_pdf,
        })

    elapsed = time.time() - start_time
    print(f"[PERF] mis_pagos: {elapsed:.2f}s")

    # Obtener datos del usuario para pre-llenar el formulario de factura
    api_usuario = UsuarioInternoGestionRest()
    usuario_data = None
    try:
        usuario_data = api_usuario.obtener_por_id(usuario_id)
    except Exception as e:
        print(f"[ERROR mis_pagos] Error al obtener datos del usuario: {e}")

    # Preparar datos del usuario para el template
    usuario_info = None
    if usuario_data:
        usuario_info = {
            "nombre": usuario_data.get("NombreUsuario") or usuario_data.get("nombreUsuario") or usuario_data.get("Nombre") or usuario_data.get("nombre"),
            "apellido": usuario_data.get("ApellidoUsuario") or usuario_data.get("apellidoUsuario") or usuario_data.get("Apellido") or usuario_data.get("apellido"),
            "correo": usuario_data.get("EmailUsuario") or usuario_data.get("emailUsuario") or usuario_data.get("Correo") or usuario_data.get("correo"),
            "tipo_documento": usuario_data.get("TipoDocumentoUsuario") or usuario_data.get("tipoDocumentoUsuario") or usuario_data.get("TipoDocumento") or usuario_data.get("tipoDocumento"),
            "documento": usuario_data.get("DocumentoUsuario") or usuario_data.get("documentoUsuario") or usuario_data.get("Documento") or usuario_data.get("documento"),
        }

    return render(request, "webapp/pagos/index.html", {
        "pagos": pagos_final,
        "usuario_info": usuario_info
    })


# ============================================================
# GENERAR FACTURA (endpoint para el botón en pagos)
# ============================================================
@csrf_exempt
def generar_factura(request):
    """
    Endpoint para generar factura desde la página de pagos.
    Recibe los datos del usuario (pueden ser los del sistema o personalizados).
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        id_reserva = data.get("idReserva")
        
        # Manejar cuando viene como string 'None' o None
        if not id_reserva or id_reserva == 'None' or id_reserva == 'null':
            return JsonResponse({"ok": False, "error": "idReserva es obligatorio"}, status=400)
        
        # Convertir a int de forma segura
        try:
            id_reserva_int = int(id_reserva)
        except (ValueError, TypeError):
            return JsonResponse({"ok": False, "error": "idReserva debe ser un número válido"}, status=400)
        
        # Datos del usuario (pueden venir del sistema o personalizados)
        nombre = data.get("nombre")
        apellido = data.get("apellido")
        correo = data.get("correo")
        tipo_documento = "CEDULA"  # Siempre CEDULA
        documento = data.get("documento")
        
        # Validar correo (obligatorio según el API)
        if not correo:
            return JsonResponse({"ok": False, "error": "El correo es obligatorio"}, status=400)
        
        # Validar documento (obligatorio)
        if not documento:
            return JsonResponse({"ok": False, "error": "El documento es obligatorio"}, status=400)
        
        # Emitir factura usando el API
        api = FuncionesEspecialesGestionRest()
        factura = api.emitir_factura_interna(
            id_reserva=id_reserva_int,
            correo=correo,
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento
        )
        
        id_factura = factura.get("IdFactura")
        if not id_factura:
            return JsonResponse({"ok": False, "error": "No se pudo obtener idFactura después de emitir la factura."})
        
        print(f"[DEBUG generar_factura] Factura {id_factura} generada correctamente para reserva {id_reserva_int}")
        
        # IMPORTANTE: El SP sp_emitirFacturaHotel_Interno ya actualiza automáticamente la tabla PAGO
        # con el ID_FACTURA (línea 196 del SP). No necesitamos hacerlo manualmente.
        print(f"[DEBUG generar_factura] ✓ Pago actualizado automáticamente por el SP con factura {id_factura}")
        
        # Generar PDF
        from utils.pdf_generator import generar_pdf_factura as generar_pdf_bytes
        from utils.s3_upload import subir_pdf_a_s3
        
        pdf_bytes = generar_pdf_bytes(id_factura, {
            "id_reserva": id_reserva_int,
            "cliente": f"{nombre or ''} {apellido or ''}".strip(),
            "total": factura.get("Total", 0)
        })
        
        pdf_filename = f"facturas/carlos/pdf{id_factura}.pdf"
        url_pdf_final = subir_pdf_a_s3(pdf_bytes, pdf_filename)
        
        return JsonResponse({
            "ok": True,
            "factura": id_factura,
            "url_pdf": url_pdf_final,
            "mensaje": "Factura generada exitosamente"
        })
        
    except Exception as e:
        print(f"[ERROR generar_factura] Error: {e}")
        import traceback
        print(f"[ERROR generar_factura] Traceback: {traceback.format_exc()}")
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


# ============================================================
# GENERAR PDF DE FACTURA EXISTENTE (endpoint /api/generar-pdf-reserva/)
# ============================================================
@csrf_exempt
def generar_pdf_reserva(request):
    """
    Endpoint para generar el PDF de una factura que ya existe.
    Recibe el ID de la factura y regenera el PDF.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        factura_id = data.get("factura_id")
        
        if not factura_id:
            return JsonResponse({"ok": False, "error": "factura_id es obligatorio"}, status=400)
        
        try:
            factura_id_int = int(factura_id)
        except (ValueError, TypeError):
            return JsonResponse({"ok": False, "error": "factura_id debe ser un número válido"}, status=400)
        
        print(f"[DEBUG generar_pdf_reserva] Generando PDF para factura {factura_id_int}")
        
        # Obtener datos de la factura
        api_facturas = FacturasGestionRest()
        factura = api_facturas.obtener_factura_por_id(factura_id_int)
        
        if not factura:
            return JsonResponse({"ok": False, "error": "Factura no encontrada"}, status=404)
        
        # Calcular el total
        subtotal = factura.get("SubtotalFactura", 0) or 0
        impuesto = factura.get("ImpuestoTotalFactura", 0) or 0
        descuento = factura.get("DescuentoTotalFactura", 0) or 0
        total = subtotal + impuesto - descuento
        
        # Obtener email del cliente
        email = factura.get("EmailUsuario") or factura.get("EmailUsuarioExterno") or "Cliente"
        
        # Generar PDF
        from utils.pdf_generator import generar_pdf_factura
        from utils.s3_upload import subir_pdf_a_s3
        
        pdf_bytes = generar_pdf_factura(factura_id_int, {
            "id_reserva": factura.get("IdReserva") or "N/A",
            "cliente": email,
            "total": total
        })
        
        # Subir a S3
        pdf_filename = f"facturas/carlos/pdf{factura_id_int}.pdf"
        url_pdf_final = subir_pdf_a_s3(pdf_bytes, pdf_filename)
        
        print(f"[DEBUG generar_pdf_reserva] PDF generado y subido a: {url_pdf_final}")
        
        # Actualizar o crear el registro en la tabla PDF
        api_pdf = PdfGestionRest()
        try:
            # Buscar si ya existe un PDF para esta factura
            pdfs = api_pdf.obtener_pdfs()
            pdf_existente = None
            for p in pdfs:
                if p.get("IdFactura") == factura_id_int:
                    pdf_existente = p
                    break
            
            if pdf_existente:
                # Actualizar
                print(f"[DEBUG generar_pdf_reserva] Actualizando PDF existente ID: {pdf_existente.get('IdPdf')}")
                # Nota: Necesitarías implementar el método actualizar_pdf en PdfGestionRest si no existe
            else:
                # Crear nuevo
                print(f"[DEBUG generar_pdf_reserva] Creando nuevo registro PDF")
                # Nota: Necesitarías implementar el método crear_pdf en PdfGestionRest si no existe
                
        except Exception as e:
            print(f"[WARN generar_pdf_reserva] No se pudo actualizar BD de PDF: {e}")
            # Continuar aunque falle
        
        return JsonResponse({
            "ok": True,
            "url_pdf": url_pdf_final,
            "mensaje": "PDF generado exitosamente"
        })
        
    except Exception as e:
        print(f"[ERROR generar_pdf_reserva] Error: {e}")
        import traceback
        print(f"[ERROR generar_pdf_reserva] Traceback: {traceback.format_exc()}")
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@csrf_exempt
def validar_token_pdf(request):
    """
    Valida que el token corresponda al factura_id.
    Devuelve True/False sin cambiar la lógica.
    """
    import json
    import hashlib
    
    try:
        data = json.loads(request.body)
        factura_id = data.get("factura_id")
        token = data.get("token")
        
        if not factura_id or not token:
            return JsonResponse({"ok": False})
        
        # Regenerar el token esperado
        secret = "pdf_secure_key_2025"
        data_hash = f"{factura_id}_{secret}".encode()
        token_esperado = hashlib.sha256(data_hash).hexdigest()[:16]
        
        # Comparar
        valido = token_esperado == token
        
        return JsonResponse({"ok": valido})
        
    except:
        return JsonResponse({"ok": False})


# Código de utilidades de PDF movido a utils/pdf_generator.py

