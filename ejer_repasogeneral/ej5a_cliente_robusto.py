import socket

HOST = "127.0.0.1" 
PUERTO = 5000

class ServidorDesconectado(Exception):
    """Excepcion propia: el servidor cerro la conexion antes de responder."""

def recibir_linea(sock, buffer):
    """Lee del socket hasta tener una linea completa. Devuelve (linea, resto_del_buffer)."""
    while "\n" not in buffer:
        datos = sock.recv(1024)
        if not datos:
            raise ServidorDesconectado()
        buffer += datos.decode("utf-8")
    return buffer.split("\n", 1)

cliente = None
try:
    cliente = socket.create_connection((HOST, PUERTO), timeout=5)
    print(f"Conectado a {HOST}:{PUERTO}")

    buffer = ""
    for mensaje in ["hola", "redes", "adios"]:
        cliente.sendall((mensaje + "\n").encode("utf-8"))
        respuesta, buffer = recibir_linea(cliente, buffer)
        print(f"Enviado: {mensaje!r:10} -> Respuesta: {respuesta!r}")

except socket.gaierror:
    print(f"ERROR: no se pudo resolver la direccion '{HOST}'. Revise la IP o el nombre del servidor.")
except ConnectionRefusedError:
    print(f"ERROR: el servidor en {HOST}:{PUERTO} esta apagado o no acepta conexiones.")
except socket.timeout:
    print("ERROR: el servidor tardo demasiado en responder.")
except (ServidorDesconectado, ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
    print("ERROR: el servidor se desconecto a media conversacion.")
finally:
    if cliente is not None:
        cliente.close()
        print("Conexion cerrada.")
