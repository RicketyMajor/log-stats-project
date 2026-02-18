## Logs-Stats

## Introducción

Los archivos grandes generados por servidores no pueden ser abiertos en un procesador de texto común (como Excel o Bloc de Notas). Hablamos de archivos de más de 500GB. Imaginemos un clúster de servidores de una empresa grande como Spotify o Netflix, las cuales generan cantidades inmensas de logs por hora. Si uno de estos archivos fuese abierto con Excel, lo más probable es que la RAM explotaría y la interfaz gráfica se congelaría. Se necesita una herramienta quirúrgica que pueda entrar, procesar ese torrente de datos línea por línea con un coste de memoria bajo, extraer las métricas clave y otorgar un resumen en el menor tiempo posible.

El objetivo del proyecto es construir un Stream Processor rudimentario. Se debe aprender a procesar datos infinitos con recursos finitos (como la RAM). Visto así ,es comparable con un micro-modelo de cómo funcionan herramientas gigantes como Apache Spark o Logstash.

## SRE Log Analyzer & Web Dashboard

Herramienta de análisis quirúrgico y monitoreo de logs de servidor orientada a Site Reliability Engineering y Seguridad.

## ¿Qué problema resuelve?

Los archivos de logs generados por clústeres de servidores en producción (como en Spotify o Netflix) pueden pesar cientos de gigabytes diarios. Intentar abrir estos archivos con procesadores de texto comunes o cargarlos directamente en memoria congelará el sistema operativo.

Esta herramienta actúa como un Stream Processor rudimentario. Procesa torrentes de datos línea por línea con un coste de memoria mínimo ($O(1)$ de RAM adicional), extrayendo métricas clave de rendimiento, seguridad y tráfico en milisegundos. Es un micro-modelo de los principios detrás de herramientas a gran escala como Apache Spark o Logstash.

## Arquitectura Interna

El alto rendimiento de esta herramienta se debe al uso intensivo de la clase `Counter` de Python y estructuras de datos optimizadas. La agregación de IPs y rutas ocurre en tiempo constante $O(1)$. El cálculo de los "Top N" elementos más frecuentes (ej. Top 5 IPs) evita ordenar listas masivas, logrando una complejidad temporal eficiente de $O(N \log K)$.

## Instalación y Configuración

```bash
# 1. Clonar el repositorio
git clone [https://github.com/tu-usuario/logs-stats-project.git](https://github.com/tu-usuario/logs-stats-project.git)
cd logs-stats-project

# 2. Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac o WSL

# 3. Instalar dependencias
pip install -r requirements.txt

```

## Uso de la Herramienta

1. **Generar Datos de Prueba**
   Si no tienes un archivo .log real a mano, puedes usar el generador sintético incluido para crear 10,000 registros con latencias y errores controlados:

```bash
python3 generate_data.py
# Generará el archivo: server.log
```

2. **Modo CLI**
   El motor de análisis principal se ejecuta desde la terminal.

```bash
python3 main.py server.log
# Ejecución estándar (Genera texto en consola y gráficos estáticos/HTML)
```

```bash
python3 main.py server.log --no-plot
# Modo Headless (Ideal para servidores sin entorno gráfico)
```

```bash
python3 main.py server.log --json reporte.json --no-plot
# Modo API/Exportación (Guarda los resultados estructurados)
```

3. **Modo Dashboard**
   Para visualizar los datos de forma interactiva, asegúrate de haber generado el archivo reporte.json (ver comando anterior) y levanta el servidor backend:

```bash
python3 app.py
# Vizualización en tiempo real en http://localhost:5000
```

## Ejemplo de Salida

```bash
--- Rendimiento del Servidor (Latencia) ---
Promedio : 124.50 ms
Mediana  : 45.00 ms (El 50% de las peticiones)
p90      : 512.00 ms (El 90% es mas rapido que esto)
p99      : 1850.00 ms (El 1% mas lento)

--- Auditoria de Seguridad (IPs sospechosas) ---
IP Atacante     | Errores  | Nivel de Riesgo
---------------------------------------------
192.168.1.200   | 842      | ALTO
8.8.8.8         | 412      | MEDIO
```
