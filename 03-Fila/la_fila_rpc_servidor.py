import threading
import time
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

HOST = "0.0.0.0"   
PUERTO = 5000

turno_actual = 0               
candado = threading.Lock()    


def registrar(texto):
    print(f"{time.strftime('%H:%M:%S')} | [{threading.current_thread().name}] {texto}")


def tomar_turno(apodo):
    """Asigna el siguiente turno de forma segura entre hilos."""
    global turno_actual
    apodo = str(apodo).strip()
    if not apodo:
        raise ValueError("el apodo no puede estar vacio")
    with candado:
        turno_actual += 1
        numero = turno_actual
    registrar(f"Turno {numero} asignado a '{apodo}'")
    return numero


def cuantos_van():
    """Devuelve el total de turnos asignados (leido con el Lock)."""
    with candado:
        total = turno_actual
    registrar(f"Consulta cuantos_van -> {total}")
    return total

# Servidor XML-RPC con un hilo por peticion
class ServidorRPCConHilos(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True      
    allow_reuse_address = True 


class ManejadorSilencioso(SimpleXMLRPCRequestHandler):
    def log_message(self, formato, *args):
        pass                  


servidor = ServidorRPCConHilos((HOST, PUERTO), requestHandler=ManejadorSilencioso, allow_none=True)
servidor.register_function(tomar_turno, "tomar_turno")
servidor.register_function(cuantos_van, "cuantos_van")
servidor.register_introspection_functions()   

registrar(f"Servidor RPC en http://{HOST}:{PUERTO}  --  LA FILA esta abierta")
try:
    servidor.serve_forever()
except KeyboardInterrupt:
    registrar(f"Servidor detenido. Total de turnos asignados: {cuantos_van()}")
finally:
    servidor.server_close()
