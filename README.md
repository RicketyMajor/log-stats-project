## Documentación

Los archivos grandes generados por servidores no pueden ser abiertos en un procesador de texto común (como Excel o Bloc de Notas). Hablamos de archivos de más de 500GB. Imaginemos un clúster de servidores de una empresa grande como Spotify o Netflix, las cuales generan cantidades inmensas de logs por hora. Si uno de estos archivos fuese abierto con Excel, lo más probable es que la RAM explotaría y la interfaz gráfica se congelaría. Se necesita una herramienta quirúrgica que pueda entrar, procesar ese torrente de datos línea por línea con un coste de memoria bajo, extraer las métricas clave y otorgar un resumen en el menor tiempo posible.

El objetivo del proyecto es construir un Stream Processor rudimentario. Se debe aprender a procesar datos infinitos con recursos finitos (como la RAM). Visto así ,es comparable con un micro-modelo de cómo funcionan herramientas gigantes como Apache Spark o Logstash.

## Parte 1: Primeras pruebas con datos generados aleatoriamente

#### generate_data.py

Más importante que la herramienta en sí, son los datos que se van a procesar. El CLI debe poder procesar un archivo de logs de servidor web, y para no hundirnos en la inmensidad de los datos, se generará un archivo `.log` con datos controlados, pero aleatorios. La idea es convertir este archivo en los cimientos de la herramienta analizadora. Para eso, se creó un script en Python llamado `generate_data.py` (ver en [generate_data.py](documentation/generate_data.py.md)): este genera archivos de logs falsos en formato Common Log Format, lo cuál es muy útil para pruebas y nos ahorra la necesidad de utilizar logs reales de producción (por ahora). El formato es el siguiente:

```bash
IP - - [timestamp] "METHOD path HTTP/1.1" status size
```

Formato similar al de Apache. Un ejemplo de cómo de cómo quedan es el siguiente:

```bash
192.168.1.1 - - [27/Nov/2025:10:00:00 +0000] "GET /home HTTP/1.1" 200 1234
```

Cada log contiene la siguiente información:

- IP ficticia. La idea es simular que diferentes clientes se conectan al servidor. Incluye rangos privados y una pública.
- Códigos de estado HTTP:
  - 200 (Petición exitosa).
  - 404 (Not found - Recurso no encontrado).
  - 500 (Internal Server Error) - Error del servidor.
  - 301 (Mover Permanently) - Redirección permanente.
- Rutas/URLs que simulan diferentes recursos del servidor web:
  - /home - (Página principal).
  - /about - (Página "About me").
  - /contact - (Página de contacto).
  - /api/login - (Endpoint API de autenticación).
  - /assets/logo.png - (Recurso estático, como una imagen).
- Métodos HTTP:
  - GET.
  - POST.
  - PUT.
- Un tamaño de respuesta aleatorio, de entre 100 a 5000 bytes.

La creación de estos datos sintéticos fue un éxito, y se generaron diez mil de estos logs en un archivo llamado `server.log`. Este es un fragmento de algunos logs aleatorios:

```bash
8.8.8.8 - - [29/Nov/2025:15:17:13 +0000] "PUT /about HTTP/1.1" 200 1103
172.16.0.5 - - [29/Nov/2025:15:17:13 +0000] "PUT /api/login HTTP/1.1" 200 4370
192.168.1.1 - - [29/Nov/2025:15:17:13 +0000] "PUT /about HTTP/1.1" 200 1099
8.8.8.8 - - [29/Nov/2025:15:17:13 +0000] "PUT /home HTTP/1.1" 500 1376
192.168.1.1 - - [29/Nov/2025:15:17:13 +0000] "GET /assets/logo.png HTTP/1.1" 301 3937
```

#### main.py

Con el archivo `server.log` listo para analizar, se creó el `main.py` (ver en [main.py](documentation/main.py-parte_1_y_2.md)) nombre temporal, ya que por ahora está todo centralizado en este). Este es un analizador de logs de servidor web en formato similar al anterior código (CLF), y que actúa como una herramienta que extrae estadísticas de archivos de logs sin cargar todo en memoria. Esto es sumamente importante dada la introducción del principio: los ejemplos vistos aquí tan solo contienen diez mil logs, y un archivo de un servidor grande puede contener cientos de veces esas cifras. Cargar todo eso en la memoria sería una sentencia de muerte (para el PC, claro).

Este script, luego de analizar los logs línea por línea, entrega una serie de estadísticas en la terminal. Estas son:

- Total de peticiones.
- Tráfico total transferido (en formato legible: KB, MB, GB).
- Tamaño promedio de respuesta.
- Un top de las 5 IPs más activas (con porcentajes).
- Distribución de códigos de estado HTTP (con porcentajes).

¿Qué ventaja tiene esto? Además de no cargar todo en memoria (lo cual es eficiente para logs gigantes), este procesa cada línea inmediatamente y la descarta. Todo gracias a la clase `Counter`, la acumula estadísticas de forma eficiente. De hecho, casi todo el funcionamiento se lo debemos a esta clase. Dentro de la clase `Counter` se encuentran:

- Un Hash Map implícito. Gracias a la línea `ip_counter[ip] += 1`, Python calcula el hash de la IP, va a esa dirección de memoria y le suma 1. Esta operación es $O(1)$, o sea, que el tiempo es constante, por lo que no importa si se procesaron 20 líneas o cinco millones de estas, el tiempo para sumar un contador es el mismo.
- Por último, un Heap implícito. Cuando se llama a `most_common(5)`, la clase `Counter` no ordena toda la lista de IPs, eso sería un $O(N \log N)$ muy lento para estos casos. En lugar de eso, utiliza un algoritmo basado en Heaps para encontrar solo los K elementos más grandes, o sea, un mucho más eficiente $O(N \log K)$.

Para usar este script, basta con cargar el archivo python en la terminal:

```bash
python3 main.py <ruta_del_archivo_log>
```

Usando el archivo `.log` generado por el código `genrate_data.py`, quedaría algo así:

```bash
python3 main.py server.log
```

Esto es un ejemplo de lo que retornaría en terminal:

```bash
--- Iniciando analisis de: server.log ---

Total de peticiones  : 10000
Trafico total        : 24.24 MB
Tamano promedio      : 2.48 KB

--- Top 5 IPs (Clientes mas activos) ---
192.168.1.200   : 2030 peticiones (20.3%)
172.16.0.5      : 2024 peticiones (20.2%)
192.168.1.1     : 2007 peticiones (20.1%)
10.0.0.1        : 1988 peticiones (19.9%)
8.8.8.8         : 1951 peticiones (19.5%)

--- Distribucion de Codigos de Estado ---
Status 200     : 4989  (49.9%)
Status 301     : 1695  (17.0%)
Status 404     : 1702  (17.0%)
Status 500     : 1614  (16.1%)
```

## Parte 2: Más estadísticas

Luego de establecer una base sólida del programa para su función principal, empieza el camino y búsqueda de la escalabilidad, mantenibilidad y un aporte de valor real. Para ello, se debe empezar reforzando estos cimientos y refinar la estrategia de parsing actual. Para eso se implementó:

- **Horas Pico:** Ahora los logs simulan días completos (de 00:00 a 23:59). en consecuencia, el analizador también procesa las horas de cada log.
- **Mejoras en las extracciones de datos:** Se separó el método de la ruta y se convierte el texto de las fechas en objetos de tiempo real.
- **Mejoras en la visualización de los datos:** Además de agregar más información a la salida (como un top de rutas visitadas y de métodos HTTP), las horas pico arrojan una barra visual que simula un gráfico, de manera que sea más cómodo a la vista divisar aquellas horas del día en que se hacen más peticiones.

Actualmente, los logs se ven así:

```python
192.168.1.1 - - [07/Dec/2025:09:40:17 +0000] "PUT /assets/js/app.js HTTP/1.1" 503 1100
192.168.1.1 - - [07/Dec/2025:16:30:45 +0000] "GET /assets/js/app.js HTTP/1.1" 500 1261
192.168.1.200 - - [07/Dec/2025:04:43:35 +0000] "GET /admin HTTP/1.1" 404 1750
192.168.1.1 - - [07/Dec/2025:22:43:38 +0000] "GET /contact HTTP/1.1" 200 4441
```

Gracias a módulos de aleatoriedad, cada log se enriquece con más información que lo hace distinto al resto, de manera que las estadísticas varían aún más. Este es un ejemplo de salida del nuevo analizador:

```bash
--- Iniciando analisis de: server.log ---

Total de peticiones  : 10000
Trafico total        : 23.96 MB
Tamano promedio      : 2.45 KB

--- Top 5 IPs ---
10.0.0.1        : 2040 peticiones (20.4%)
192.168.1.200   : 2015 peticiones (20.2%)
192.168.1.1     : 1985 peticiones (19.9%)
172.16.0.5      : 1981 peticiones (19.8%)
8.8.8.8         : 1979 peticiones (19.8%)

--- Top Rutas Visitadas ---
/assets/css/style.css : 1336 visitas
/about               : 1285 visitas
/api/login           : 1279 visitas
/contact             : 1251 visitas
/api/products        : 1244 visitas

--- Metodos HTTP ---
GET        : 4988
DELETE     : 1702
PUT        : 1699
POST       : 1611

--- Horas Pico de Trafico ---
Hora  | Peticiones | Barra Visual
----------------------------------------
00    | 421        | ********
01    | 417        | ********
02    | 405        | ********
03    | 386        | *******
04    | 404        | ********
05    | 421        | ********
06    | 415        | ********
07    | 428        | ********
08    | 418        | ********
09    | 438        | ********
10    | 392        | *******
11    | 410        | ********
12    | 428        | ********
13    | 416        | ********
14    | 402        | ********
15    | 454        | *********
16    | 399        | *******
17    | 423        | ********
18    | 416        | ********
19    | 367        | *******
20    | 407        | ********
21    | 445        | ********
22    | 427        | ********
23    | 461        | *********

--- Distribucion de Codigos de Estado ---
Status 200     : 2541  (25.4%)
Status 201     : 833   (8.3%)
Status 400     : 809   (8.1%)
Status 401     : 811   (8.1%)
Status 403     : 801   (8.0%)
Status 404     : 1670  (16.7%)
Status 500     : 872   (8.7%)
Status 502     : 811   (8.1%)
Status 503     : 852   (8.5%)
```

Los datos siguen siendo controlados, pero el objetivo será pasar de la simulación a la realidad.
