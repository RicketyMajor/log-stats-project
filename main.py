"""
main.py
=======
Analizador de logs de servidor web en formato Common Log Format (CLF).
Herramienta CLI que extrae estadísticas de archivos de logs sin cargar todo en memoria.

Uso:
    python3 main.py <ruta_del_archivo_log>

Ejemplo:
    python3 main.py server.log

Estadísticas generadas:
    - Total de peticiones
    - Tráfico total transferido (en formato legible: KB, MB, GB)
    - Tamaño promedio de respuesta
    - Top 5 IPs más activas (con porcentajes)
    - Distribución de códigos de estado HTTP (con porcentajes)
"""

# === IMPORTACIONES ===
# Para acceder a argumentos de línea de comandos (sys.argv) y salir del programa (sys.exit)
import sys
# Para usar expresiones regulares (regex) y parsear el formato de log
import re
# Estructura de datos optimizada para contar elementos
from collections import Counter

# === PATRÓN DE EXPRESIÓN REGULAR (REGEX) ===
# Define cómo identificar y extraer datos de cada línea del log

# CONSTANTE: Patrón para parsear formato Common Log Format (CLF)
# Formato esperado: IP - - [timestamp] "METHOD path HTTP/version" status size
# Ejemplo: 192.168.1.1 - - [27/Nov/2025:10:00:00 +0000] "GET /home HTTP/1.1" 200 1234

LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'

# DESGLOSE DEL PATRÓN (cada paréntesis crea un "grupo" capturado):
# ^           → Inicio de línea (asegura que coincida desde el principio)
# (\S+)       → GRUPO 1: uno o más caracteres NO-espacio → captura la IP
# - -         → Texto literal: dos guiones con espacios (campos RFC1413 y auth)
# \[          → Corchete literal (escapado porque [ tiene significado especial en regex)
# (.*?)       → GRUPO 2: cualquier carácter, modo NO-codicioso (mínimo posible) → timestamp
# \]          → Corchete de cierre literal
# "           → Comillas literales
# (.*?)       → GRUPO 3: cualquier carácter NO-codicioso → "METHOD path HTTP/version"
# "           → Comillas de cierre
#             → Espacio literal
# (\d+)       → GRUPO 4: uno o más dígitos → código de estado HTTP (200, 404, etc.)
#             → Espacio literal
# (\d+)       → GRUPO 5: uno o más dígitos → tamaño de respuesta en bytes
# $           → Final de línea (asegura que coincida hasta el final)

# Prefijo 'r' (raw string): evita que Python interprete '\' como escape
# Sin 'r': necesitarías escribir '\\[' en vez de '\['

# === FUNCIONES AUXILIARES (HELPERS) ===


def format_bytes(size):
    """
    Convierte bytes a formato legible para humanos (B, KB, MB, GB).

    Algoritmo: divide repetidamente por 1024 hasta que el número sea < 1024,
    incrementando la etiqueta de unidad en cada división.

    Args:
        size (float): Cantidad en bytes

    Returns:
        str: Tamaño formateado con 2 decimales y su unidad

    Ejemplos:
        format_bytes(500)      → "500.00 B"
        format_bytes(2048)     → "2.00 KB"
        format_bytes(5242880)  → "5.00 MB"
    """
    power = 2**10  # 1024 bytes = 1 KB (estándar binario IEC, no decimal SI)
    n = 0          # Índice de la unidad actual (0=B, 1=KB, 2=MB, 3=GB)

    # Diccionario que mapea índice → etiqueta de unidad
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}

    # Bucle: mientras el tamaño sea mayor a 1024, divide y sube de unidad
    # Ejemplo: 2048 bytes → 2048/1024=2 KB → sale del bucle
    while size > power:
        size /= power  # Divide por 1024
        n += 1         # Incrementa el índice de unidad

    # Formato: .2f = 2 decimales (ej: 2.00, no 2 o 2.0000)
    return f"{size:.2f} {power_labels[n]}"


# === FUNCIÓN PRINCIPAL DE PROCESAMIENTO ===

def process_log_file(file_path):
    """
    Procesa un archivo de logs línea por línea y genera estadísticas.

    Ventajas de este enfoque:
        - NO carga todo el archivo en memoria (eficiente para logs gigantes)
        - Procesa cada línea inmediatamente y la descarta
        - Usa Counter para acumular estadísticas de forma eficiente

    Args:
        file_path (str): Ruta del archivo de logs a analizar

    Returns:
        None (imprime resultados directamente en la consola)
    """
    print(f"--- Iniciando analisis de: {file_path} ---\n")

    # --- Inicialización de acumuladores ---

    total_requests = 0   # Contador simple: cuántas líneas válidas procesamos
    # Acumulador: suma de todos los tamaños de respuesta (en bytes)
    total_bytes = 0

    # Counter: diccionario especializado para contar elementos
    # Ventaja sobre dict normal: no necesitas verificar si la clave existe antes de incrementar
    # Ejemplo: ip_counter['192.168.1.1'] += 1 funciona aunque no exista la clave
    ip_counter = Counter()      # Cuenta cuántas veces aparece cada IP
    status_counter = Counter()  # Cuenta cuántas veces aparece cada código HTTP

    # --- Bloque de manejo de errores (try-except) ---
    # Atrapa errores comunes para que el programa no se "crashee" sin explicación

    try:
        # Context manager 'with': cierra el archivo automáticamente al salir
        # Modo 'r': lectura (read). encoding='utf-8': soporte para caracteres internacionales
        with open(file_path, 'r', encoding='utf-8') as f:

            # === ITERACIÓN LÍNEA POR LÍNEA (CLAVE PARA EFICIENCIA) ===
            # 'for line in f' NO carga todo el archivo en memoria
            # Python lee línea por línea bajo demanda (lazy evaluation)
            # Esto permite procesar archivos de TERABYTES con poca RAM
            for line in f:

                # .strip(): elimina espacios, tabs y saltos de línea (\n, \r) al inicio/final
                # Ejemplo: "  192.168.1.1 ...\n  " → "192.168.1.1 ..."
                line = line.strip()

                # Validación: saltar líneas vacías (pueden aparecer en logs corruptos)
                # 'if not line' es True si line == "" (string vacío)
                if not line:
                    continue  # 'continue' salta a la siguiente iteración del bucle

                # === APLICACIÓN DE REGEX ===
                # re.match(patron, texto): intenta hacer coincidir el patrón DESDE EL INICIO
                # Devuelve: objeto Match si coincide, None si no
                # Diferencia con re.search(): match solo busca al inicio, search en toda la línea
                match = re.match(LOG_PATTERN, line)

                # Si el regex coincidió (la línea tiene el formato correcto)
                if match:
                    # === EXTRACCIÓN DE GRUPOS CAPTURADOS ===
                    # .group(n): devuelve el contenido del grupo N del regex
                    # Los grupos se numeran desde 1 (no desde 0)
                    # .group(0) devuelve toda la coincidencia completa

                    ip = match.group(1)          # GRUPO 1: IP del cliente
                    # timestamp = match.group(2) # GRUPO 2: timestamp (no lo usamos aún)
                    # request = match.group(3)   # GRUPO 3: "METHOD path HTTP/version" (futuro)
                    # GRUPO 4: código de estado HTTP (string)
                    status = match.group(4)
                    # GRUPO 5: tamaño en bytes (string)
                    size_str = match.group(5)

                    # === ACTUALIZACIÓN DE ESTADÍSTICAS ===

                    # 1. Incremento simple de contador
                    total_requests += 1

                    # 2. Counter: incremento automático (crea clave si no existe)
                    # Equivalente a: if ip not in ip_counter: ip_counter[ip] = 0
                    #                ip_counter[ip] += 1
                    ip_counter[ip] += 1
                    status_counter[status] += 1

                    # 3. Casting (conversión de tipo) y acumulación
                    # size_str es un string "1234", necesitamos int para sumar
                    # int() puede lanzar ValueError si el string no es numérico (lo atrapamos abajo)
                    total_bytes += int(size_str)

                else:
                    # Si la línea NO coincide con el patrón: ignorarla silenciosamente
                    # En producción podrías loggear estas líneas en un archivo de errores:
                    # with open('errores.log', 'a') as err: err.write(f"Línea inválida: {line}\n")
                    continue

        # === GENERACIÓN DE REPORTE (SALIDA) ===

        # --- Validación: caso borde de archivo vacío ---
        # Programación defensiva: evitar división por cero más abajo
        if total_requests == 0:
            print("El archivo esta vacio o no se encontraron lineas validas.")
            # Salir de la función sin devolver nada (return None implícito)
            return

        # --- Cálculo de métricas derivadas ---
        # Promedio: división entre cantidad de peticiones
        # Resultado es float (ej: 1234.56 bytes)
        avg_size = total_bytes / total_requests

        # --- Impresión de estadísticas generales ---
        print(f"Total de peticiones  : {total_requests}")

        # Usamos nuestra función helper para formato legible
        # Ejemplo: 5242880 bytes → "5.00 MB"
        print(f"Trafico total        : {format_bytes(total_bytes)}")
        print(f"Tamano promedio      : {format_bytes(avg_size)}")

        # --- Top 5 IPs más activas ---
        print("\n--- Top 5 IPs (Clientes mas activos) ---")

        # .most_common(n): devuelve lista de tuplas [(elemento, count), ...] ordenada por count
        # Ejemplo: [('192.168.1.1', 3500), ('10.0.0.1', 2800), ...]
        for ip, count in ip_counter.most_common(5):
            # Cálculo de porcentaje: (parte/total) * 100
            percentage = (count / total_requests) * 100

            # Formato de string:
            # {ip:<15} → alinea 'ip' a la izquierda con 15 caracteres de ancho
            # {percentage:.1f} → muestra 1 decimal (ej: 35.2%, no 35.23456%)
            print(f"{ip:<15} : {count} peticiones ({percentage:.1f}%)")

        # --- Distribución de códigos de estado HTTP ---
        print("\n--- Distribucion de Codigos de Estado ---")

        # sorted(dict.items()): ordena las tuplas (clave, valor) por clave
        # Ejemplo: Counter({'200': 5000, '404': 300, '500': 100})
        #       → [('200', 5000), ('404', 300), ('500', 100)]
        # Esto muestra los códigos en orden numérico (200, 301, 404, 500...)
        # Alternativa: usar .most_common() para ordenar por frecuencia (más común primero)
        for status, count in sorted(status_counter.items()):
            percentage = (count / total_requests) * 100

            # {count:<5} → alinea 'count' a la izquierda con 5 caracteres
            # Hace que los porcentajes se alineen verticalmente
            print(f"Status {status}     : {count:<5} ({percentage:.1f}%)")

    # --- Manejo de excepciones (errores esperados) ---
    # Múltiples bloques except: captura errores más específicos primero, genéricos después

    except FileNotFoundError:
        # Error específico: el archivo no existe en la ruta especificada
        # Se lanza cuando open() no puede encontrar el archivo
        print(f"Error: El archivo '{file_path}' no existe.")

    except ValueError:
        # Error de conversión de tipos: ocurre si int(size_str) falla
        # Ejemplo: si una línea tiene texto en vez de número en el campo size
        print("Error: Se encontro un dato no numerico donde se esperaba un numero.")

    except Exception as e:
        # Captura CUALQUIER otro error no anticipado
        # 'as e': guarda el objeto de error en la variable 'e'
        # e contiene información sobre qué salió mal
        # En producción, podrías loggear 'e' a un archivo para debugging
        print(f"Ocurrio un error inesperado: {e}")


# === PUNTO DE ENTRADA DEL PROGRAMA ===

# Patrón común en Python: distinguir entre "ejecutar" vs "importar"
# __name__ es una variable especial que Python asigna automáticamente:
#   - Si ejecutas directamente: python3 main.py → __name__ == "__main__"
#   - Si importas: import main → __name__ == "main"
# Propósito: evitar que el código se ejecute accidentalmente al importar el módulo
if __name__ == "__main__":

    # === VALIDACIÓN DE ARGUMENTOS DE LÍNEA DE COMANDOS ===

    # sys.argv es una lista con todos los argumentos pasados al script
    # Ejemplo: python3 main.py server.log
    #   sys.argv[0] = "main.py"      (nombre del script)
    #   sys.argv[1] = "server.log"   (primer argumento)
    #   len(sys.argv) = 2

    # Validamos que el usuario pasó EXACTAMENTE 1 argumento (además del nombre del script)
    if len(sys.argv) != 2:
        # Si la validación falla: mostrar mensaje de ayuda
        print("Uso correcto: python3 main.py <ruta_del_log>")

        # sys.exit(codigo): termina el programa inmediatamente
        # Códigos de salida (convención Unix/Linux):
        #   0 = éxito (todo OK)
        #   1-255 = error (diferentes tipos de error)
        # Los scripts que llamen a este programa pueden verificar el código de salida
        sys.exit(1)

    # === EXTRACCIÓN DEL ARGUMENTO Y EJECUCIÓN ===

    # Si llegamos aquí, la validación pasó: tenemos exactamente 1 argumento
    # Extraer la ruta del archivo (segundo elemento de la lista)
    log_file = sys.argv[1]

    # Llamada a la función principal con la ruta proporcionada
    # El procesamiento completo ocurre dentro de process_log_file()
    process_log_file(log_file)

    # Al terminar process_log_file(), el programa finaliza naturalmente
    # Código de salida implícito: 0 (éxito)
