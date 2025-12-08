import requests
from datetime import datetime
from zeep import Client, Transport
from zeep.helpers import serialize_object
from zeep.exceptions import Fault


class ImagenHabitacionGestionSoap:

    def __init__(self):
        # Asegúrate de que esta URL coincida con donde desplegaste el .asmx
        self.wsdl = "http://allpahousenycgs.runasp.net/ImagenHabitacionWS.asmx?wsdl"

        session = requests.Session()
        session.verify = False
        requests.packages.urllib3.disable_warnings()
        transport = Transport(session=session)

        self.client = Client(wsdl=self.wsdl, transport=transport)

    # ========================================================
    # Helpers
    # ========================================================
    def _fmt_date(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.isoformat()

    def _normalize(self, d):
        if d is None:
            return None

        d = serialize_object(d)

        return {
            "IdImagenHabitacion": d.get("IdImagenHabitacion"),
            "IdHabitacion": d.get("IdHabitacion"),
            "UrlImagen": d.get("UrlImagen"),
            "EstadoImagen": d.get("EstadoImagen"),
            "FechaModificacionImagenHabitacion": self._fmt_date(
                d.get("FechaModificacionImagenHabitacion")
            ),
        }

    def _to_list(self, r):
        if r is None:
            return []

        r = serialize_object(r)

        if isinstance(r, list):
            return r

        if isinstance(r, dict):
            # Caso .asmx típico: {'ImagenHabitacionDto': [ {...}, {...} ]}
            for v in r.values():
                if isinstance(v, list):
                    return v
            return [r]

        return [r]

    # ========================================================
    # LISTAR (todas las imágenes)
    # ========================================================
    def listar(self):
        """
        Obtiene todas las imágenes de todas las habitaciones.

        Tu servicio C# tiene:
        public List<ImagenHabitacionDto> ObtenerImagenesHabitacion()
        {
            return _ln.ObtenerTodasImagenes();
        }
        Es decir, SIN parámetros.
        """
        try:
            r = self.client.service.ObtenerImagenesHabitacion()  # SIN argumentos
            items = self._to_list(r)
            return [self._normalize(x) for x in items]
        except Fault as e:
            raise Exception(f"SOAP Error al listar imágenes: {e}")
        except Exception as e:
            raise Exception(f"Error al listar imágenes: {e}")

    # Método que usas en tu admin para el listado
    def obtener_imagenes(self):
        return self.listar()

    # ========================================================
    # OBTENER POR ID
    # ========================================================
    def obtener_imagen_por_id(self, id_imagen):
        return self.obtener_por_id(id_imagen)

    def obtener_por_id(self, id_imagen):
        try:
            r = self.client.service.ObtenerImagenPorId(id_imagen)
            return self._normalize(r)
        except Fault as e:
            raise Exception(f"SOAP Error al obtener imagen por ID: {e}")
        except Exception as e:
            raise Exception(f"Error al obtener imagen por ID: {e}")

    # ========================================================
    # CREAR
    # ========================================================
    def crear(self, dto):
        try:
            new_id = self.client.service.AgregarImagenHabitacion(dto)
            return new_id
        except Fault as e:
            raise Exception(f"SOAP Error al crear imagen: {e}")
        except Exception as e:
            raise Exception(f"Error al crear imagen: {e}")

    # ========================================================
    # ACTUALIZAR
    # ========================================================
    def actualizar(self, id_imagen, dto):
        try:
            r = self.client.service.ActualizarImagenHabitacion(id_imagen, dto)
            return self._normalize(r)
        except Fault as e:
            raise Exception(f"SOAP Error al actualizar imagen: {e}")
        except Exception as e:
            raise Exception(f"Error al actualizar imagen: {e}")

    # ========================================================
    # ELIMINAR
    # ========================================================
    def eliminar(self, id_imagen):
        try:
            return self.client.service.EliminarImagenHabitacion(id_imagen)
        except Fault as e:
            raise Exception(f"SOAP Error al eliminar imagen: {e}")
        except Exception as e:
            raise Exception(f"Error al eliminar imagen: {e}")

# ========================================================
    # ALIAS PARA COMPATIBILIDAD CON VIEWS DEL ADMIN
    # ========================================================
    def crear_imagen(self, id_habitacion, url_imagen, estado_imagen=True):
        dto = {
            "IdImagenHabitacion": 0,  # 0 indica que es un nuevo registro
            "IdHabitacion": id_habitacion,
            "UrlImagen": url_imagen,
            "EstadoImagen": estado_imagen,
            "FechaModificacionImagenHabitacion": datetime.now().isoformat()
        }
        return self.crear(dto)
    
    def actualizar_imagen(self, id_imagen, id_habitacion, url_imagen, estado_imagen=True):
        dto = {
            "IdImagenHabitacion": id_imagen,
            "IdHabitacion": id_habitacion,
            "UrlImagen": url_imagen,
            "EstadoImagen": estado_imagen,
            "FechaModificacionImagenHabitacion": datetime.now().isoformat()
        }
        return self.actualizar(id_imagen, dto)
    
    def eliminar_imagen(self, id_imagen):
        return self.eliminar(id_imagen)
