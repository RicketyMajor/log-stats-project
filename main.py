import sys
import re
from collections import Counter

# CONSTANTE: Expresion regular para parsear una linea de log
LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'


def format_bytes(size):
    """
    [NUEVO] Convierte un numero de bytes a una unidad legible (B, KB, MB).
    """
    power = 2**10  # 1024
    n = 0
    power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def process_log_file(file_path):
    print(f"--- Iniciando analisis de: {file_path} ---\n")

    total_requests = 0
    total_bytes = 0  # [NUEVO] Acumulador para el tamano total
    ip_counter = Counter()
    status_counter = Counter()

    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                match = re.match(LOG_PATTERN, line)
                if match:
                    ip = match.group(1)
                    status = match.group(4)
                    # [NUEVO] Extraemos el tamano como texto
                    size_str = match.group(5)

                    # 1. Agregacion Basica
                    total_requests += 1
                    ip_counter[ip] += 1
                    status_counter[status] += 1

                    # 2. [NUEVO] Agregacion de Bytes (Casting seguro)
                    # Convertimos texto a entero para poder sumar
                    total_bytes += int(size_str)

        # --- SECCION DE RESULTADOS ---

        # [NUEVO] Manejo de caso borde: Archivo vacio
        if total_requests == 0:
            print("El archivo esta vacio o no se encontraron lineas validas.")
            return

        # [NUEVO] Calculo del promedio
        avg_size = total_bytes / total_requests

        print(f"Total de peticiones  : {total_requests}")
        # Usamos nuestra funcion helper
        print(f"Trafico total        : {format_bytes(total_bytes)}")
        # Usamos nuestra funcion helper
        print(f"Tamano promedio      : {format_bytes(avg_size)}")

        print("\n--- Top 5 IPs (Clientes mas activos) ---")
        for ip, count in ip_counter.most_common(5):
            # Calculamos el porcentaje que representa cada IP del total
            percentage = (count / total_requests) * 100
            print(f"{ip:<15} : {count} peticiones ({percentage:.1f}%)")

        print("\n--- Distribucion de Codigos de Estado ---")
        for status, count in sorted(status_counter.items()):
            percentage = (count / total_requests) * 100
            print(f"Status {status}     : {count:<5} ({percentage:.1f}%)")

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no existe.")
    except ValueError:
        print("Error: Se encontro un dato no numerico donde se esperaba un numero.")
    except Exception as e:
        print(f"Ocurrio un error inesperado: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso correcto: python3 main.py <ruta_del_log>")
        sys.exit(1)

    log_file = sys.argv[1]
    process_log_file(log_file)
