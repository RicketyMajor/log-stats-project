import sys
import re
from collections import Counter

# CONSTANTE: Expresion regular para parsear una linea de log
# Captura grupos: 1=IP, 2=Fecha, 3=Metodo/Ruta, 4=Codigo Estado, 5=Tamano
# Nota: Este regex es basico, lo mejoraremos luego.
LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'


def process_log_file(file_path):
    """
    Lee el archivo linea por linea y extrae estadisticas.
    NO carga todo el archivo en memoria.
    """
    print(f"--- Iniciando analisis de: {file_path} ---")

    # Contadores para nuestras estadisticas
    total_requests = 0
    ip_counter = Counter()
    status_counter = Counter()

    try:
        # TODO: Aqui empieza la magia del Nivel 1 (I/O eficiente)
        # Debes abrir el archivo y recorrerlo linea por linea.
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue  # Saltar lineas vacias

                # Intentamos hacer match con el regex
                match = re.match(LOG_PATTERN, line)
                if match:
                    # Extraemos los datos capturados
                    ip = match.group(1)
                    status = match.group(4)

                    # TODO: Actualizar los contadores aqui
                    # total_requests += 1
                    # ...
                    pass  # 'pass' es un placeholder, borralo cuando escribas codigo
                else:
                    # Si la linea no cumple el formato, la ignoramos (o la loggeamos como error)
                    continue

        # TODO: Imprimir los resultados finales aqui
        print(f"Total de peticiones: {total_requests}")
        print("Top IPs:")
        # ... imprimir top ips
        print("Codigos de estado:")
        # ... imprimir status_counter

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no existe.")
    except Exception as e:
        print(f"Ocurrio un error inesperado: {e}")


if __name__ == "__main__":
    # Verificamos que el usuario paso un argumento (la ruta del archivo)
    if len(sys.argv) != 2:
        print("Uso correcto: python3 main.py <ruta_del_log>")
        sys.exit(1)

    log_file = sys.argv[1]
    process_log_file(log_file)
