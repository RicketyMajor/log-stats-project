import sys
import re
import argparse
import json
import statistics
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# [FASE 5] Regex actualizado para capturar la latencia al final (grupo 6)
LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+) (\d+)$'


def format_bytes(size):
    """Convierte bytes a unidades legibles (KB, MB, GB)."""
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def export_results_to_json(data, filename):
    """[FASE 4] Exporta el diccionario de resultados a un archivo JSON."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n[INFO] Datos exportados exitosamente a JSON: {filename}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo exportar el JSON: {e}")


def generate_charts(ip_counter, status_counter, hour_counter):
    """[FASE 2A] Genera reportes estaticos (PNG) con Matplotlib."""
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
    """[FASE 2B] Genera Dashboard interactivo (HTML) con Plotly."""
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


def process_log_file(file_path, flags):
    """Motor principal de procesamiento de logs."""
    print(f"--- Iniciando analisis de: {file_path} ---\n")

    total_requests = 0
    total_bytes = 0

    # Contadores
    ip_counter = Counter()
    status_counter = Counter()
    method_counter = Counter()
    path_counter = Counter()
    hour_counter = Counter()

    # [FASE 5] Nuevas estructuras para rendimiento y seguridad
    latencies = []
    security_audit = Counter()

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
                    # [FASE 5] Capturamos la latencia
                    latency_str = match.group(6)

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

                    # Agregacion Basica
                    total_requests += 1
                    ip_counter[ip] += 1
                    status_counter[status] += 1
                    total_bytes += int(size_str)
                    method_counter[method] += 1
                    path_counter[path] += 1
                    hour_counter[current_hour] += 1

                    # [FASE 5] Agregacion de Latencia
                    latencies.append(int(latency_str))

                    # [FASE 5] Auditoria de Seguridad (Detectar errores de cliente/servidor)
                    if status.startswith("4") or status.startswith("5"):
                        security_audit[ip] += 1

        if total_requests == 0:
            print("Archivo vacio o formato invalido.")
            return

        # --- CALCULOS MATEMATICOS AVANZADOS (FASE 5) ---
        if latencies:
            avg_latency = statistics.mean(latencies)
            p50_latency = statistics.median(latencies)
            try:
                # Intenta usar quantiles (Python 3.8+)
                p90_latency = statistics.quantiles(latencies, n=10)[8]
                p99_latency = statistics.quantiles(latencies, n=100)[98]
            except AttributeError:
                # Fallback manual para versiones antiguas de Python
                latencies_sorted = sorted(latencies)
                p90_latency = latencies_sorted[int(
                    len(latencies_sorted) * 0.9)]
                p99_latency = latencies_sorted[int(
                    len(latencies_sorted) * 0.99)]
        else:
            avg_latency = p50_latency = p90_latency = p99_latency = 0

        # ==========================================
        # IMPRESION DE REPORTES EN TERMINAL (ASCII)
        # ==========================================
        print(f"Procesadas {total_requests} lineas.")
        avg_size = total_bytes / total_requests
        print(f"Trafico total        : {format_bytes(total_bytes)}")
        print(f"Tamano promedio      : {format_bytes(avg_size)}")

        # [FASE 5] Print de Rendimiento
        print("\n--- Rendimiento del Servidor (Latencia) ---")
        print(f"Promedio : {avg_latency:.2f} ms")
        print(f"Mediana  : {p50_latency:.2f} ms (El 50% de las peticiones)")
        print(
            f"p90      : {p90_latency:.2f} ms (El 90% es mas rapido que esto)")
        print(f"p99      : {p99_latency:.2f} ms (El 1% mas lento)")

        print("\n--- Top 5 IPs ---")
        for ip, count in ip_counter.most_common(5):
            percentage = (count / total_requests) * 100
            print(f"{ip:<15} : {count} peticiones ({percentage:.1f}%)")

        print("\n--- Top Rutas Visitadas ---")
        for path, count in path_counter.most_common(5):
            print(f"{path:<20} : {count} visitas")

        print("\n--- Horas Pico de Trafico ---")
        print(f"{'Hora':<5} | {'Peticiones':<10} | {'Barra Visual'}")
        print("-" * 40)
        for hour, count in sorted(hour_counter.items()):
            bar = "*" * (count // 50)
            print(f"{hour:<5} | {count:<10} | {bar}")

        # [FASE 5] Print de Seguridad
        print("\n--- Auditoria de Seguridad (IPs sospechosas) ---")
        suspicious_ips = security_audit.most_common(3)
        if not suspicious_ips:
            print("No se detectaron errores significativos.")
        else:
            print(f"{'IP Atacante':<15} | {'Errores':<8} | {'Nivel de Riesgo'}")
            print("-" * 45)
            for ip, errors in suspicious_ips:
                risk = "ALTO" if errors > 500 else "MEDIO"
                print(f"{ip:<15} | {errors:<8} | {risk}")

        # ==========================================
        # INTEROPERABILIDAD Y EXPORTACION (FASE 3 Y 4)
        # ==========================================

        # 1. Exportar a JSON
        if flags.json:
            report_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_analyzed": file_path,
                "summary": {
                    "total_requests": total_requests,
                    "total_bytes": total_bytes,
                    "avg_size_bytes": round(avg_size, 2)
                },
                "performance_ms": {
                    "avg": round(avg_latency, 2),
                    "p50": round(p50_latency, 2),
                    "p90": round(p90_latency, 2),
                    "p99": round(p99_latency, 2)
                },
                "top_ips": dict(ip_counter.most_common(10)),
                "top_paths": dict(path_counter.most_common(10)),
                "methods": dict(method_counter),
                "status_codes": dict(status_counter),
                "security_alerts": dict(suspicious_ips)
            }
            export_results_to_json(report_data, flags.json)

        # 2. Generar Graficos Visuales
        if not flags.no_plot:
            print("\n")  # Salto de linea para que se vea limpio
            generate_charts(ip_counter, status_counter, hour_counter)
            generate_html_report(hour_counter, status_counter)
        else:
            print("\n[INFO] Salida gráfica omitida por el usuario (--no-plot)")

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no existe.")
    except Exception as e:
        print(f"Ocurrio un error critico durante el procesamiento: {e}")


if __name__ == "__main__":
    # Configuracion de la CLI
    parser = argparse.ArgumentParser(
        description="Analizador de Logs (SRE/SecOps). Mide trafico, latencia y seguridad."
    )

    parser.add_argument("log_file", help="Ruta al archivo de log a analizar")

    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Omite la generacion de graficos (PNG/HTML)."
    )

    parser.add_argument(
        "--json",
        help="Exporta los resultados estructurados a un archivo JSON (ej: output.json)"
    )

    args = parser.parse_args()
    process_log_file(args.log_file, args)
