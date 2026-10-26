import socket

HOST = "127.0.0.1"   
PUERTO = 5001

cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cliente.settimeout(3)  

try:
    cliente.sendto("ESTADO".encode("utf-8"), (HOST, PUERTO))
    datos, direccion = cliente.recvfrom(1024)
    print(f"Respuesta de {direccion}: {datos.decode('utf-8')}")
except socket.timeout:
    print("Sin respuesta en 3 segundos: el servidor no esta activo o se perdio el datagrama.")
except ConnectionResetError:
    print("El servidor no esta escuchando en ese puerto.")
finally:
    cliente.close()
