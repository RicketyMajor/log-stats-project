import sys  # Librería que permite interactuar con argumentos de línea de comandos
import re  # Librería que trbaja con expresiones regulares
# Librería que facilita el conteo de elementos en listas
from collections import Counter

# CONSTANTE: Expresion regular para parsear una linea de log
# Captura grupos: 1=IP, 2=Fecha, 3=Metodo/Ruta, 4=Codigo Estado, 5=Tamano
# Nota: Este regex es basico, lo mejoraremos luego.
LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'


def process_log_file(file_path):  # Función que recibe la ruta del archivo de log
    """
    Lee el archivo linea por linea y extrae estadisticas.
    NO carga todo el archivo en memoria.
    """
    print(f"--- Iniciando analisis de: {file_path} ---")

    # Contadores para nuestras estadisticas
    total_requests = 0  # Una variable entero, que cuenta el total de peticiones
    ip_counter = Counter()  # Contador para las IPs
    status_counter = Counter()  # Contador para los códigos de estado

    # Este bloque asegura que si el archivo no existe o hay un error, el programa no se caiga y que avise al usuario de manera adecuada.
    try:
        with open(file_path, 'r') as f:
            for line in f:  # Itera linea por línea, lo lee todo de una
                line = line.strip()  # Elimina espacios en blanco al inicio y final
                if not line:  # Condicional para lineas vacias
                    continue  # Saltar lineas vacias

                # Intentamos hacer match con el regex
                match = re.match(LOG_PATTERN, line)
                if match:
                    # Extraemos los datos capturados
                    ip = match.group(1)  # La IP del cliente
                    status = match.group(4)  # Código de estado
                    # Actualizamos los contadores
                    total_requests += 1  # Incrementa el total de peticiones
                    # Si la IP "192.168.1.1" no existía, Counter la crea con valor 1. Si ya existía, incrementa su valor en 1.
                    ip_counter[ip] += 1
                    # Lo mismo para códigos de estado (200, 404, etc)
                    status_counter[status] += 1
                else:
                    # Si la linea no cumple el formato, la ignoramos (o la loggeamos como error)
                    continue

        print(f"Total de peticiones: {total_requests}")
        print("\n--- Top 5 Direcciones IP ---")
        # Obtiene las 5 IPs más comunes
        for ip, count in ip_counter.most_common(5):
            print(f"{ip:<20} : {count} peticiones")
        # ... imprimir top ips
        print("\n--- Distribución de códigos de estado ---")
        for status, count in sorted(status_counter.items()):
            print(f"Status {status:<10} : {count} veces")

    except FileNotFoundError:  # Captura de errores especificos
        print(f"Error: El archivo '{file_path}' no existe.")
    except Exception as e:  # Cualquier otro error se captura aqui
        print(f"Ocurrio un error inesperado: {e}")


# Comprueba si el archivo se está ejecutando directamente o si se está importando desde otro archivo
if __name__ == "__main__":
    # Verificamos que el usuario paso un argumento (la ruta del archivo)
    if len(sys.argv) != 2:  # Si no hay exactamente 2 argumentos (el script y la ruta)
        print("Uso correcto: python3 main.py <ruta_del_log>")
        sys.exit(1)  # Salir con codigo de error

    # El segundo argumento es la ruta del archivo de log
    log_file = sys.argv[1]
    # Llamada a la función principal con la ruta del archivo
    process_log_file(log_file)
