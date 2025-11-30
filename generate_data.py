# Librerias necesarias para generar datos de logs falsos.
# Se utiliza random para seleccionar valores aleatorios y time para generar timestamps.
import random
import time

# Configuraciones para el archivo de log falso, se usan variables constantes, valores figos que no deberían cambiar durante la ejecución.
FILE_NAME = "server.log"
# Se establece el numero de lineas que tendrá el archivo de log. 10000 lineas.
NUM_LINES = 10000

# Las siguientes variables contienen listas, las cuales definen un universo de datos posibles.
IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.5", "192.168.1.200", "8.8.8.8"]
# Pequeño truco de probabilidad: el número 200 (que indica éxito) se cooloca más veces para que aparezca con mayor frecuencia.
# Son códigos HTTP comunes (200 OK, 404 Not Found, 500 Internal Server Error, 301 Moved Permanently).
STATUS_CODES = [200, 200, 200, 404, 500, 301]
# URLs/rutas que simulan páginas web o recursos del servidor.
PATHS = ["/home", "/about", "/contact", "/api/login", "/assets/logo.png"]

print(f"Generando {FILE_NAME} con {NUM_LINES} lineas...")

# Se define el bloque with para garantizar que si hay un error al escribir el archivo, este se cierre correctamente.
# open() abre el archivo en modo escritura ("w"). Si el archivo no existe, lo crea. Si sí existe, lo sobrescribe.
# La variable f es creada para representar el archivo abierto.
with open(FILE_NAME, "w") as f:
    # El bucle for itera NUM_LINES veces para generar cada linea del log. La variable _ es una convención en Python para indicar que no se usará el valor de la variable.
    for _ in range(NUM_LINES):
        ip = random.choice(IPS)
        timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
        method = random.choice(["GET", "POST", "PUT"])
        path = random.choice(PATHS)
        status = random.choice(STATUS_CODES)
        size = random.randint(100, 5000)

        # Formato estandar tipo Apache/Nginx
        # Ejemplo: 192.168.1.1 - - [27/Nov/2025:10:00:00 +0000] "GET /home HTTP/1.1" 200 1234
        line = f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size}\n'
        f.write(line)

print("¡Listo! Archivo creado.")
