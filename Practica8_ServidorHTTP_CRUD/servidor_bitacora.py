"""
Práctica 8 · Programación en Red · NRC 19141
Servidor HTTP con CRUD sobre un archivo JSON (bitácora de incidencias).
Solo usa la biblioteca estándar de Python.

Rutas:
  GET    /                      información del servicio
  GET    /incidencias           lista (filtros opcionales: ?tipo=...&estado=...)
  GET    /incidencias/<id>      una incidencia
  POST   /incidencias           crea (201)
  PUT    /incidencias/<id>      reemplazo completo (200)
  PATCH  /incidencias/<id>      modifica campos (200)
  DELETE /incidencias/<id>      elimina (204)
  GET    /logs                  bitácora de peticiones de la sesión
  GET    /contadores            contadores de la sesión
"""
import http.server, json, time
from urllib.parse import urlparse, parse_qs

PUERTO = 8001
ARCHIVO = "incidencias.json"            # la "base de datos": un archivo JSON
ESTADOS_VALIDOS = ("abierta", "en_proceso", "resuelta")
siguiente_id = 1


# ---------------------------------------------------------------- Paso 2
def cargar():
    """Lee las incidencias del archivo JSON al arrancar el servidor."""
    global siguiente_id
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
        if datos:
            siguiente_id = max(i["id"] for i in datos) + 1
        return datos
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # primera ejecución o archivo corrupto: empezar vacío


def guardar():
    """Reescribe el archivo JSON con la lista actual de incidencias."""
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(incidencias, f, ensure_ascii=False, indent=2)


incidencias = cargar()  # al arrancar, recupera lo que había en disco

# ---------------------------------------------------------------- Paso 3
logs = []

contadores = {
    "peticiones_totales": 0,
    "por_metodo": {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "HEAD": 0},
    "por_familia": {"2xx": 0, "4xx": 0, "5xx": 0},
    "incidencias_por_tipo": {"alerta": 0, "vulnerabilidad": 0, "incidente": 0},
}


def mensaje_estados():
    return "estado inválido; valores válidos: " + ", ".join(ESTADOS_VALIDOS)


class Manejador(http.server.BaseHTTPRequestHandler):

    # ------------------------------------------------------------ utilidades
    def _leer_json(self):
        """Lee el cuerpo de la petición y lo interpreta como JSON."""
        try:
            tam = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(tam).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None  # cuerpo ausente o JSON inválido

    def _enviar(self, codigo, datos=None):
        """Envía la respuesta JSON y anota la petición en logs y contadores."""
        cuerpo = b"" if datos is None else json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)
        logs.append({"hora": time.strftime("%H:%M:%S"),
                     "metodo": self.command, "ruta": self.path, "codigo": codigo})
        contadores["peticiones_totales"] += 1
        contadores["por_metodo"][self.command] = contadores["por_metodo"].get(self.command, 0) + 1
        contadores["por_familia"][f"{codigo // 100}xx"] += 1

    def _id_de_ruta(self, url):
        """Devuelve el id entero de /incidencias/<id>, o None (ya respondió 400)."""
        try:
            return int(url.path.split("/")[2])
        except (ValueError, IndexError):
            self._enviar(400, {"error": "id debe ser entero"})
            return None

    def log_message(self, formato, *args):
        pass

    # ------------------------------------------------------------------ HEAD
    def do_HEAD(self):
        url = urlparse(self.path)
        if url.path in ("/", "/incidencias", "/logs", "/contadores"):
            self._enviar(200)
        else:
            self._enviar(404)

    # ------------------------------------------------- Paso 4, 8 y ejercicio 5
    def do_GET(self):
        url = urlparse(self.path)
        parametros = parse_qs(url.query)

        if url.path == "/":
            self._enviar(200, {
                "servicio": "Bitácora de incidencias",
                "rutas": ["GET /incidencias", "GET /incidencias/<id>",
                          "POST /incidencias", "PUT /incidencias/<id>",
                          "PATCH /incidencias/<id>", "DELETE /incidencias/<id>",
                          "GET /logs", "GET /contadores"],
            })

        elif url.path == "/incidencias":
            lista = incidencias
            if "tipo" in parametros:
                lista = [i for i in lista if i["tipo"] == parametros["tipo"][0]]
            if "estado" in parametros:
                lista = [i for i in lista if i["estado"] == parametros["estado"][0]]
            self._enviar(200, lista)

        elif url.path.startswith("/incidencias/"):
            buscado = self._id_de_ruta(url)
            if buscado is None:
                return
            for inc in incidencias:
                if inc["id"] == buscado:
                    self._enviar(200, inc)
                    return
            self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})

        elif url.path == "/logs":
            self._enviar(200, logs)

        elif url.path == "/contadores":
            self._enviar(200, contadores)

        else:
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})

    # ------------------------------------------------- Paso 5 + ejercicio 1
    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/incidencias":
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})
            return

        datos = self._leer_json()
        if not isinstance(datos, dict):
            self._enviar(400, {"error": "el cuerpo debe ser JSON válido"})
            return
        faltan = [c for c in ("tipo", "descripcion") if c not in datos]
        if faltan:
            self._enviar(400, {"error": f"faltan campos: {', '.join(faltan)}"})
            return
        estado = str(datos.get("estado", "abierta"))
        if estado not in ESTADOS_VALIDOS:
            self._enviar(400, {"error": mensaje_estados()})
            return

        global siguiente_id
        incidencia = {
            "id": siguiente_id,
            "tipo": str(datos["tipo"]),
            "descripcion": str(datos["descripcion"]),
            "estado": estado,
            "hora": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        siguiente_id += 1
        incidencias.append(incidencia)
        contadores["incidencias_por_tipo"][incidencia["tipo"]] = (
            contadores["incidencias_por_tipo"].get(incidencia["tipo"], 0) + 1)
        guardar()  # <-- aquí se escribe incidencias.json
        self._enviar(201, incidencia)

    # ------------------------------------------------------ Ejercicio 4: PUT
    def do_PUT(self):
        url = urlparse(self.path)
        if not url.path.startswith("/incidencias/"):
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})
            return
        buscado = self._id_de_ruta(url)
        if buscado is None:
            return

        datos = self._leer_json()
        if not isinstance(datos, dict):
            self._enviar(400, {"error": "el cuerpo debe ser JSON válido"})
            return
        faltan = [c for c in ("tipo", "descripcion") if c not in datos]
        if faltan:
            self._enviar(400, {"error": f"faltan campos: {', '.join(faltan)}"})
            return

        for pos, inc in enumerate(incidencias):
            if inc["id"] == buscado:
                nueva = {
                    "id": buscado,                       # el id original se conserva
                    "tipo": str(datos["tipo"]),
                    "descripcion": str(datos["descripcion"]),
                    "estado": "abierta",                 # reemplazo completo: reinicia
                    "hora": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                incidencias[pos] = nueva
                guardar()
                self._enviar(200, nueva)
                return
        self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})

    # ------------------------------------------------- Paso 6 + ejercicio 1
    def do_PATCH(self):
        url = urlparse(self.path)
        if not url.path.startswith("/incidencias/"):
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})
            return
        buscado = self._id_de_ruta(url)
        if buscado is None:
            return

        datos = self._leer_json()
        if not isinstance(datos, dict):
            self._enviar(400, {"error": "el cuerpo debe ser JSON válido"})
            return
        if "estado" in datos and str(datos["estado"]) not in ESTADOS_VALIDOS:
            self._enviar(400, {"error": mensaje_estados()})
            return

        for inc in incidencias:
            if inc["id"] == buscado:
                for campo in ("tipo", "descripcion", "estado"):
                    if campo in datos:
                        inc[campo] = str(datos[campo])
                guardar()  # <-- el cambio queda en el archivo
                self._enviar(200, inc)
                return
        self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})

    # ----------------------------------------------------------------- Paso 7
    def do_DELETE(self):
        url = urlparse(self.path)
        if not url.path.startswith("/incidencias/"):
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})
            return
        buscado = self._id_de_ruta(url)
        if buscado is None:
            return

        for i, inc in enumerate(incidencias):
            if inc["id"] == buscado:
                del incidencias[i]
                guardar()  # <-- el archivo también lo olvida
                self._enviar(204)  # sin cuerpo
                return
        self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})


if __name__ == "__main__":
    servidor = http.server.HTTPServer(("localhost", PUERTO), Manejador)
    print(f"Escuchando en http://localhost:{PUERTO}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
