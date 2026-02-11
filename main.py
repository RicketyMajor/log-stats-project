import sys
import re
import argparse  # [FASE 3] Importamos la librería para gestionar argumentos
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    """Genera reportes estaticos (PNG) con Matplotlib (Fase 2A)"""
    print("--- Generando reportes visuales (PNG)... ---")

    # 1. Grafico de Barras: Top 10 IPs
    top_ips = ip_counter.most_common(10)
    x_values = [ip for ip, count in top_ips]
    y_values = [count for ip, count in top_ips]

    plt.figure(figsize=(10, 6))
    plt.bar(x_values, y_values, color='skyblue')
    plt.title('Top 10 IPs mas activas')
    plt.xlabel('Direccion IP')
    plt.ylabel('Numero de Peticiones')
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('reporte_ips.png')
    plt.close()
    print("-> Generado: reporte_ips.png")

    # 2. Grafico de Torta: Codigos de Estado
    labels = list(status_counter.keys())
    sizes = list(status_counter.values())

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Distribucion de Codigos de Estado HTTP')

    plt.savefig('reporte_status.png')
    plt.close()
    print("-> Generado: reporte_status.png")


def generate_html_report(hour_counter, status_counter):
    """Genera Dashboard interactivo (HTML) con Plotly (Fase 2B)"""
    print("--- Generando dashboard interactivo (HTML)... ---")

    # 1. Preparacion de datos
    hours_sorted = sorted(hour_counter.items())
    x_hours = [h for h, count in hours_sorted]
    y_requests = [count for h, count in hours_sorted]

    labels_status = list(status_counter.keys())
    values_status = list(status_counter.values())

    # 2. Creacion del Lienzo (Subplots)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Trafico por Hora (24h)", "Distribucion de Errores"),
        specs=[[{"type": "xy"}, {"type": "domain"}]]
    )

    # 3. Añadir Trazas
    fig.add_trace(
        go.Bar(x=x_hours, y=y_requests,
               name="Peticiones", marker_color='indigo'),
        row=1, col=1
    )

    fig.add_trace(
        go.Pie(labels=labels_status, values=values_status,
               name="Status", hole=.4),
        row=1, col=2
    )

    # 4. Estetica Global
    fig.update_layout(
        title_text="Dashboard de Analisis de Logs - Servidor Principal",
        template="plotly_dark",
        showlegend=True
    )

    # 5. Guardar
    fig.write_html("dashboard.html")
    print("-> Generado: dashboard.html (Abrelo en tu navegador)")


def process_log_file(file_path, flags):  # [FASE 3] Ahora recibimos 'flags'
    print(f"--- Iniciando analisis de: {file_path} ---\n")
    total_requests = 0
    total_bytes = 0

    # Contadores
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

                    # Separar Metodo y Ruta
                    if len(request_str.split()) == 3:
                        method, path, protocol = request_str.split()
                    else:
                        method, path = ("UNKNOWN", "UNKNOWN")

                    # Extraer Hora
                    try:
                        current_hour = timestamp_str.split(':')[1]
                    except IndexError:
                        current_hour = "00"

                    # Agregacion
                    total_requests += 1
                    ip_counter[ip] += 1
                    status_counter[status] += 1
                    total_bytes += int(size_str)
                    method_counter[method] += 1
                    path_counter[path] += 1
                    hour_counter[current_hour] += 1

        if total_requests == 0:
            print("Archivo vacio.")
            return

        # --- SECCION DE REPORTES (TEXTO ASCII) ---
        print(f"Procesadas {total_requests} lineas.")
        avg_size = total_bytes / total_requests
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

        print("\n--- Horas Pico de Trafico (ASCII) ---")
        print(f"{'Hora':<5} | {'Peticiones':<10} | {'Barra Visual'}")
        print("-" * 40)
        for hour, count in sorted(hour_counter.items()):
            bar = "*" * (count // 50)
            print(f"{hour:<5} | {count:<10} | {bar}")

        print("\n--- Distribucion de Codigos de Estado ---")
        for status, count in sorted(status_counter.items()):
            percentage = (count / total_requests) * 100
            print(f"Status {status}     : {count:<5} ({percentage:.1f}%)")

        # [FASE 3] LOGICA CONDICIONAL DE GRAFICOS
        if not flags.no_plot:
            # Solo generamos gráficos si el usuario NO usó --no-plot
            generate_charts(ip_counter, status_counter, hour_counter)
            generate_html_report(hour_counter, status_counter)
        else:
            print("\n[INFO] Salida gráfica omitida por el usuario (--no-plot)")

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no existe.")
    except ValueError:
        print("Error: Se encontro un dato no numerico donde se esperaba un numero.")
    except Exception as e:
        print(f"Ocurrio un error inesperado: {e}")


if __name__ == "__main__":
    # [FASE 3] Configuración de argparse
    parser = argparse.ArgumentParser(
        description="Analizador de Logs de Servidor (CLF). Genera reportes de trafico y seguridad."
    )

    # Argumento posicional (obligatorio): El archivo
    parser.add_argument("log_file", help="Ruta al archivo de log a analizar")

    # Argumento opcional (flag): --no-plot
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Si se usa, no genera graficos (PNG/HTML). Ideal para servidores sin interfaz."
    )

    # Argumento opcional: --json (Preparacion para Fase 4)
    parser.add_argument(
        "--json",
        help="Exportar resultados a un archivo JSON (ej: --json output.json)"
    )

    # Parsear argumentos
    args = parser.parse_args()

    # Ejecutar logica pasando los argumentos parseados
    process_log_file(args.log_file, args)
