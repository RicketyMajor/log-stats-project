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

# Regex to capture latency at the end
LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+) (\d+)$'

# Functions for data processing and visualization

def format_bytes(size):
    #Converts bytes to human-readable units (KB, MB, GB).
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def export_results_to_json(data, filename):
    #Exports the results dictionary to a JSON file.
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n[INFO] Data successfully exported to JSON: {filename}")
    except Exception as e:
        print(f"\n[ERROR] Could not export JSON: {e}")


def generate_charts(ip_counter, status_counter, hour_counter):
    #Generates static reports (PNG) with Matplotlib.
    print("--- Generating visual reports (PNG)... ---")

    # Bar chart: Top 10 IPs
    top_ips = ip_counter.most_common(10)
    x_values = [ip for ip, count in top_ips]
    y_values = [count for ip, count in top_ips]

    plt.figure(figsize=(10, 6))
    plt.bar(x_values, y_values, color='skyblue')
    plt.title('Top 10 Most Active IPs')
    plt.xlabel('IP Address')
    plt.ylabel('Number of Requests')
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('reporte_ips.png')
    plt.close()
    print("-> Generated: reporte_ips.png")

    # Pie chart: Status Codes
    labels = list(status_counter.keys())
    sizes = list(status_counter.values())

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of HTTP Status Codes')

    plt.savefig('reporte_status.png')
    plt.close()
    print("-> Generated: reporte_status.png")


def generate_html_report(hour_counter, status_counter):
    #Generates an interactive HTML dashboard with Plotly.
    print("--- Generating interactive dashboard (HTML)... ---")

    # Data preparation
    hours_sorted = sorted(hour_counter.items())
    x_hours = [h for h, count in hours_sorted]
    y_requests = [count for h, count in hours_sorted]

    labels_status = list(status_counter.keys())
    values_status = list(status_counter.values())

    # Subplots creation
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Traffic per Hour (24h)", "Error Distribution"),
        specs=[[{"type": "xy"}, {"type": "domain"}]]
    )

    # Add traces
    fig.add_trace(
        go.Bar(x=x_hours, y=y_requests,
               name="Requests", marker_color='indigo'),
        row=1, col=1
    )

    fig.add_trace(
        go.Pie(labels=labels_status, values=values_status,
               name="Status", hole=.4),
        row=1, col=2
    )

    # Global aesthetics
    fig.update_layout(
        title_text="Log Analysis Dashboard - Main Server",
        template="plotly_dark",
        showlegend=True
    )

    # Save
    fig.write_html("dashboard.html")
    print("-> Generated: dashboard.html (Open it in your browser)")


def process_log_file(file_path, flags):
    #Main log processing engine.
    print(f"--- Starting analysis of: {file_path} ---\n")

    total_requests = 0
    total_bytes = 0

    # Counters
    ip_counter = Counter()
    status_counter = Counter()
    method_counter = Counter()
    path_counter = Counter()
    hour_counter = Counter()

    # New structures for performance and security
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
                    # Capture latency
                    latency_str = match.group(6)

                    # Separate Method and Path
                    if len(request_str.split()) == 3:
                        method, path, protocol = request_str.split()
                    else:
                        method, path = ("UNKNOWN", "UNKNOWN")

                    # Extract Hour
                    try:
                        current_hour = timestamp_str.split(':')[1]
                    except IndexError:
                        current_hour = "00"

                    # Basic aggregation
                    total_requests += 1
                    ip_counter[ip] += 1
                    status_counter[status] += 1
                    total_bytes += int(size_str)
                    method_counter[method] += 1
                    path_counter[path] += 1
                    hour_counter[current_hour] += 1

                    # Latency aggregation
                    latencies.append(int(latency_str))

                    # Security audit (Detect client/server errors)
                    if status.startswith("4") or status.startswith("5"):
                        security_audit[ip] += 1

        if total_requests == 0:
            print("Empty or invalid format file.")
            return

        # Advanced mathematical calculations
        if latencies:
            avg_latency = statistics.mean(latencies)
            p50_latency = statistics.median(latencies)
            try:
                # Try using quantiles (Python 3.8+)
                p90_latency = statistics.quantiles(latencies, n=10)[8]
                p99_latency = statistics.quantiles(latencies, n=100)[98]
            except AttributeError:
                # Manual fallback for older Python versions
                latencies_sorted = sorted(latencies)
                p90_latency = latencies_sorted[int(
                    len(latencies_sorted) * 0.9)]
                p99_latency = latencies_sorted[int(
                    len(latencies_sorted) * 0.99)]
        else:
            avg_latency = p50_latency = p90_latency = p99_latency = 0

        # Terminal reports (ASCII)
        print(f"Processed {total_requests} lines.")
        avg_size = total_bytes / total_requests
        print(f"Total traffic        : {format_bytes(total_bytes)}")
        print(f"Average size      : {format_bytes(avg_size)}")

        # Performance print
        print("\n--- Server Performance (Latency) ---")
        print(f"Average : {avg_latency:.2f} ms")
        print(f"Median  : {p50_latency:.2f} ms (50% of requests)")
        print(
            f"p90      : {p90_latency:.2f} ms (90% is faster than this)")
        print(f"p99      : {p99_latency:.2f} ms (The slowest 1%)")

        print("\n--- Top 5 IPs ---")
        for ip, count in ip_counter.most_common(5):
            percentage = (count / total_requests) * 100
            print(f"{ip:<15} : {count} requests ({percentage:.1f}%)")

        print("\n--- Top Visited Routes ---")
        for path, count in path_counter.most_common(5):
            print(f"{path:<20} : {count} visits")

        print("\n--- Peak Traffic Hours ---")
        print(f"{'Hour':<5} | {'Requests':<10} | {'Visual Bar'}")
        print("-" * 40)
        for hour, count in sorted(hour_counter.items()):
            bar = "*" * (count // 50)
            print(f"{hour:<5} | {count:<10} | {bar}")

        # Security print
        print("\n--- Security Audit (Suspicious IPs) ---")
        suspicious_ips = security_audit.most_common(3)
        if not suspicious_ips:
            print("No significant errors detected.")
        else:
            print(f"{'Attacker IP':<15} | {'Errors':<8} | {'Risk Level'}")
            print("-" * 45)
            for ip, errors in suspicious_ips:
                risk = "HIGH" if errors > 500 else "MEDIUM"
                print(f"{ip:<15} | {errors:<8} | {risk}")

        # Interoperability and Export
        
        # Export to JSON
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

        # Generate visual graphics
        if not flags.no_plot:
            print("\n")  # Newline for clean output
            generate_charts(ip_counter, status_counter, hour_counter)
            generate_html_report(hour_counter, status_counter)
        else:
            print("\n[INFO] Graphic output omitted by the user (--no-plot)")

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
    except Exception as e:
        print(f"A critical error occurred during processing: {e}")


if __name__ == "__main__":
    # CLI configuration
    parser = argparse.ArgumentParser(
        description="Log Analyzer (SRE/SecOps). Measures traffic, latency, and security."
    )

    parser.add_argument("log_file", help="Path to the log file to analyze")

    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skips the generation of graphics (PNG/HTML)."
    )

    parser.add_argument(
        "--json",
        help="Exports the structured results to a JSON file (e.g., output.json)"
    )

    args = parser.parse_args()
    process_log_file(args.log_file, args)
