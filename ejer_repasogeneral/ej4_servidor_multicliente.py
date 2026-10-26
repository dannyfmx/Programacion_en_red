import socket
import threading

HOST = "0.0.0.0"
PUERTO = 5000

def atender_cliente(conexion, direccion):
    """Se ejecuta en un hilo aparte: atiende a UN cliente de principio a fin."""
    print(f"[{threading.current_thread().name}] Atendiendo a {direccion}")
    buffer = ""
    while True:
        datos = conexion.recv(1024)
        if not datos:                 
            break
        buffer += datos.decode("utf-8")
        while "\n" in buffer:       
            mensaje, buffer = buffer.split("\n", 1)
            print(f"[{direccion}] {mensaje}")
            conexion.sendall((mensaje + "\n").encode("utf-8"))
    conexion.close()
    print(f"Cliente {direccion} desconectado")

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind((HOST, PUERTO))
servidor.listen(5)
print(f"Servidor multicliente escuchando en el puerto {PUERTO}...")

while True:
    conexion, direccion = servidor.accept()
    hilo = threading.Thread(
        target=atender_cliente,          
        args=(conexion, direccion),    
        daemon=True,                    
    )
    hilo.start()             
    print(f"Clientes activos: {threading.active_count() - 1}")
