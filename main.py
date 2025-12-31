import sys
import re
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt

LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'


def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def generate_charts(ip_counter, status_counter, hour_counter):
    print("--- Generando reportes visuales (PNG)... ---")

    # 1. Grafico de Barras: Top 10 IPs
    # Preparamos los datos: Separamos las IPs (eje X) de los conteos (eje Y)
    top_ips = ip_counter.most_common(10)
    x_values = [ip for ip, count in top_ips]
    y_values = [count for ip, count in top_ips]

    # Creamos la figura
    plt.figure(figsize=(10, 6))  # Tamano en pulgadas (ancho, alto)
    plt.bar(x_values, y_values, color='skyblue')  # Tipo de grafico: Barra
    plt.title('Top 10 IPs mas activas')
    plt.xlabel('Direccion IP')
    plt.ylabel('Numero de Peticiones')
    # Rotamos las etiquetas del eje X para que se lean bien
    plt.xticks(rotation=45)
    plt.tight_layout()  # Ajuste automatico para que no se corten textos

    # Guardamos en disco
    plt.savefig('reporte_ips.png')
    plt.close()  # Importante: Cerrar la figura para liberar memoria
    print("-> Generado: reporte_ips.png")

    # 2. Grafico de Torta (Pie Chart): Codigos de Estado
    # Filtramos para mostrar solo los importantes (si hay muchos codigos raros, el grafico se ve mal)
    labels = list(status_counter.keys())
    sizes = list(status_counter.values())

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Distribucion de Codigos de Estado HTTP')

    plt.savefig('reporte_status.png')
    plt.close()
    print("-> Generado: reporte_status.png")


def process_log_file(file_path):
    print(f"--- Iniciando analisis de: {file_path} ---\n")
    total_requests = 0
    total_bytes = 0
    ip_counter = Counter()
    status_counter = Counter()
    method_counter = Counter()
    path_counter = Counter()
    hour_counter = Counter()

    try:

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = re.match(LOG_PATTERN, line)

                if match:
                    ip = match.group(1)
                    timestamp_str = match.group(2)
                    request_str = match.group(3)
                    status = match.group(4)
                    size_str = match.group(5)

                    if len(request_str.split()) == 3:
                        method, path, protocol = request_str.split()
                    else:
                        method, path = ("UNKNOWN", "UNKNOWN")

                    try:
                        current_hour = timestamp_str.split(':')[1]
                    except IndexError:
                        current_hour = "00"

                    total_requests += 1
                    ip_counter[ip] += 1

                    status_counter[status] += 1
                    total_bytes += int(size_str)
                    method_counter[method] += 1
                    path_counter[path] += 1
                    hour_counter[current_hour] += 1
                else:
                    continue

        if total_requests == 0:
            return
        print(f"Procesadas {total_requests} lineas.")

        generate_charts(ip_counter, status_counter, hour_counter)

        avg_size = total_bytes / total_requests

        print(f"Total de peticiones  : {total_requests}")
        print(f"Trafico total        : {format_bytes(total_bytes)}")
        print(f"Tamano promedio      : {format_bytes(avg_size)}")

        print("\n--- Top 5 IPs ---")

        for ip, count in ip_counter.most_common(5):
            percentage = (count / total_requests) * 100

            print(f"{ip:<15} : {count} peticiones ({percentage:.1f}%)")

        print("\n--- Top Rutas Visitadas ---")
        for path, count in path_counter.most_common(5):
            print(f"{path:<20} : {count} visitas")

        print("\n--- Metodos HTTP ---")
        for method, count in method_counter.most_common():
            print(f"{method:<10} : {count}")

        print("\n--- Horas Pico de Trafico ---")
        # Ordenamos por hora (00, 01, 02...) no por cantidad
        print(f"{'Hora':<5} | {'Peticiones':<10} | {'Barra Visual'}")
        print("-" * 40)
        for hour, count in sorted(hour_counter.items()):
            # Generamos una pequeña barra visual con asteriscos
            # Escalamos: 1 asterisco por cada 50 peticiones aprox (para que quepa en pantalla)
            bar = "*" * (count // 50)
            print(f"{hour:<5} | {count:<10} | {bar}")

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
