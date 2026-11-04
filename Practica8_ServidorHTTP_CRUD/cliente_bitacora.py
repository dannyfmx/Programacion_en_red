"""
Práctica 8 · Cliente en Python (requests) para la bitácora de incidencias.
Requiere: pip install requests   y el servidor corriendo en el puerto 8001.
"""
import requests

BASE = "http://localhost:8001"


def titulo(texto):
    print(f"\n=== {texto} ===")


# 1. Crear (POST): los datos van en el cuerpo (json=)
titulo("POST /incidencias")
r = requests.post(f"{BASE}/incidencias",
                  json={"tipo": "alerta", "descripcion": "Escaneo de puertos"}, timeout=10)
print(r.status_code, r.json())          # 201
creada = r.json()

r = requests.post(f"{BASE}/incidencias",
                  json={"tipo": "vulnerabilidad", "descripcion": "SSH con contrasena debil"},
                  timeout=10)
print(r.status_code, r.json())
segunda = r.json()

# 2. Consultar (GET): el filtro va en la URL (params=)
titulo("GET /incidencias (todas)")
print(requests.get(f"{BASE}/incidencias", timeout=10).json())

titulo("GET /incidencias?tipo=alerta")
print(requests.get(f"{BASE}/incidencias", params={"tipo": "alerta"}, timeout=10).json())

titulo(f"GET /incidencias/{creada['id']}")
print(requests.get(f"{BASE}/incidencias/{creada['id']}", timeout=10).json())

# 3. Modificar parcialmente (PATCH): id en la ruta, cambios en el cuerpo
titulo("PATCH (estado -> en_proceso)")
r = requests.patch(f"{BASE}/incidencias/{creada['id']}",
                   json={"estado": "en_proceso"}, timeout=10)
print(r.status_code, r.json())          # 200

# Ejercicio 1: estado inválido -> 400 con los valores válidos
r = requests.patch(f"{BASE}/incidencias/{creada['id']}",
                   json={"estado": "cerrada"}, timeout=10)
print(r.status_code, r.json())          # 400

# 4. Reemplazar (PUT): reemplazo completo, estado vuelve a "abierta"
titulo("PUT (reemplazo completo)")
r = requests.put(f"{BASE}/incidencias/{segunda['id']}",
                 json={"tipo": "incidente", "descripcion": "Servidor web caído"}, timeout=10)
print(r.status_code, r.json())          # 200

r = requests.put(f"{BASE}/incidencias/{segunda['id']}",
                 json={"tipo": "incidente"}, timeout=10)
print(r.status_code, r.json())          # 400: falta descripcion

# 5. Filtros combinados (ejercicio 5)
titulo("Filtros combinados")
for params in ({"tipo": "alerta"}, {"estado": "abierta"},
               {"tipo": "alerta", "estado": "abierta"},
               {"tipo": "alerta", "estado": "en_proceso"}):
    r = requests.get(f"{BASE}/incidencias", params=params, timeout=10)
    print(params, "->", [i["id"] for i in r.json()])

# 6. Eliminar (DELETE): solo el id en la ruta, 204 sin cuerpo
titulo("DELETE")
r = requests.delete(f"{BASE}/incidencias/{creada['id']}", timeout=10)
print(r.status_code, repr(r.text))      # 204 ''
r = requests.delete(f"{BASE}/incidencias/{creada['id']}", timeout=10)
print(r.status_code, r.json())          # 404

# 7. Comprobar el código antes de usar el cuerpo
titulo("Manejo de errores")
r = requests.get(f"{BASE}/incidencias/999", timeout=10)
if r.status_code == 404:
    print("no existe:", r.json()["error"])

# 8. La auditoría del servidor, desde fuera
titulo("GET /contadores")
print(requests.get(f"{BASE}/contadores", timeout=10).json())
titulo("GET /logs")
for linea in requests.get(f"{BASE}/logs", timeout=10).json():
    print(linea)
