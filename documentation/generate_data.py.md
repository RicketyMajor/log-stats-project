## Resumen

Este es un script para generar archivos de logs falsos en formato CLF. El formato generado será de Apache/Nginx:

```bash
    IP - - [timestamp] "METHOD path HTTP/1.1" status size
```

# Parte 1: Generación de logs básicos 
## Importaciones

Para este código, se utilizaron dos importaciones: `random`, que se usa para generar selecciones aleatorias de listas y números; y `time`, para obtener y formatear timestamps (fecha/hora actual).

```python
import random
import time
```

## Constantes y Configuraciones

Para convención de Python, las mayúsculas en las variables indican que son constantes. Esto se resume en que no deben ser modificadas durante la ejecución.

Para el nombre del archivo de salida que se creará (o si ya existe, lo sobrescribirá) se define la constante `FILE_NAME = ""`, seguido de `NUM_LINES = ""`, el cual es la cantidad de líneas de log a generar.

```python
FILE_NAME = "server.log"  
NUM_LINES = 10000
```

Continuando con el universo de datos posibles, se define `IPS = [" ", " ", " "]` con IPs ficticias que simularán diferentes clientes conectándose al servidor. Esto incluye rangos privados (como 192.168.x.x, 10.x.x.x, 172.16.x.x) y una pública (8.8.8.8).

```python
IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.5", "192.168.1.200", "8.8.8.8"]
```

De la misma forma, se define `STATUS_CODES = [ , , ]`, que contendrá los códigos de estado HTTP. Un truco de probabilidad utilizado es que 200 aparece 3 veces, lo que se resume en un 50% de probabilidades de aparición. Esto con el objetivo de simular un servidor saludable donde la mayoría de peticiones tienen éxito.

```python
STATUS_CODES = [
    200,  # OK - Petición exitosa
    200,  # (duplicado para aumentar probabilidad)
    200,  # (duplicado para aumentar probabilidad)
    404,  # Not Found - Recurso no encontrado
    500,  # Internal Server Error - Error del servidor
    301   # Moved Permanently - Redirección permanente
]
```

Por último y parecido a la constante anterior, se define `PATHS = [" " , " " , " "]` con rutas/URLs que simulan diferentes recursos del servidor web.

```python
PATHS = [
    "/home",              # Página principal
    "/about",             # Página "Acerca de"
    "/contact",           # Página de contacto
    "/api/login",         # Endpoint API de autenticación
    "/assets/logo.png"    # Recurso estático (imagen)
]
```

## Generación

El inicio de la generación es simple: es un `print()` de un mensaje que incluye las constantes del nombre del archivo y número de líneas definidas anteriormente.

```python
print(f"Generando {FILE_NAME} con {NUM_LINES} lineas...")
```

Ahora bien, se define el contexto del archivo con `with`, ¿para qué? porque esto garantiza que el archivo se cierre automáticamente, incluso si hay errores. Esto es equivalente a un `f = open(...); try: ...; finally: f.close()`.
El modo "write" (`w`) crea el archivo si no existe, o lo sobrescribe si ya existe.
Por último, `encoding = "utf-8"` especifica una codificación UTF-8, que es el estándar moderno y soporta todos los caracteres.

```python
with open(FILE_NAME, "w", encoding="utf-8") as f:  # 'f' es el objeto file (manejador del archivo)
```

Dentro del `with` se define un bucle que genera `NUM_LINES` líneas (10,000 iteraciones). La variable `_` sirve para indicar que no se usará tal valor. Por último, se define un rango `range(10000)` que genera números 0-9999. Pero estos no serán necesarios, solo se necesita contar.

```python
for _ in range(NUM_LINES):
```

Dentro de este bucle `for` se define una variable `ip`, la cual tiene como valor una función `random.choice()`, que selecciona un elemento aleatorio de la lista de IPs. Cada elemento tiene igual probabilidad excepto en `STATUS_CODES` (donde 200 está triplicado).

```python
ip = random.choice(IPS)
```

Se define la variable `timestamp`, la cual tiene como valor la función `time.strftime()`, la cual tiene como objetivo formatear la hora actual del sistema. 
Todas las líneas tendrán timestamps muy similares, ya que se generan en milisegundos. Por ejemplo,`27/Nov/2025:10:00:00 +0000`

```python
timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
```

La variable `method` tiene una función similar, solo que con los métodos HTTP más comunes (GET: solicitar datos, POST: enviar datos, PUT: actualizar datos).

```python
method = random.choice(["GET", "POST", "PUT"])
```

Lo mismo para las variables `path` y `status`, pero para la ruta/URL del recurso solicitado y código de respuesta HTTP, respectivamente.

```python
path = random.choice(PATHS)  
status = random.choice(STATUS_CODES)
```

La variable `size` es definida con una función distinta, la cual es `random.randint(a, b)`. Este con el objetivo de generar un entero aleatorio entre a y b (inclusive ambos). Este simula el tamaño de la respuesta en bytes (de 100 a 5000 bytes).

```python
size = random.randint(100, 5000)
```

En la variable `line`, se hace la construcción de la línea en formato Common Log Format, el cual es `IP - - [timestamp] "METHOD path HTTP/version" status size`. Los dos guiones `- -` son campos reservados para:
- Identidad del cliente (RFC 1413), la cual casi nunca se usa.
- Usuario autenticado, pero solo si hay autenticación HTTP básica. 
Al final de este, hay un salto de línea `\n`, ya que cada log debe estar en su propia línea.

```python
line = f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size}\n'
```

Finalmente, la función `f.write()` escribe la cadena en el archivo. Ojo que no añade un salto de línea automáticamente, por eso es incluido en la línea de código anterior.

```python
f.write(line)
```

# Parte 2: Implementación de nuevos datos a los logs

## Importaciones

Para esta nueva parte del programa, se integraron dos herramientas específicas del módulo estándar `datetime` para trabajar con el tiempo. Por ejemplo, con `datetime` se manejan las fechas y horas específicas, un punto en el tiempo; con `timedelta` se manejan duraciones o diferencias de tiempo, como un intervalo.

```python
from datetime import datetime, timedelta
```

## Configuración

Las variables clásicas han sido refinadas y se han añadido más variedad.

```python
IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.5", "192.168.1.200", "8.8.8.8"]
STATUS_CODES = [200, 200, 200, 201, 400, 401, 403, 404, 404, 500, 502, 503]
PATHS = ["/home", "/about", "/contact", "/api/login", "/api/products", "/assets/css/style.css", "/assets/js/app.js", "/admin"]
METHODS = ["GET", "GET", "GET", "POST", "PUT", "DELETE"]
```

Se mantiene la repetición de valores para redirigir las estadísticas a unas más controladas. 

## Generación

Este script se modificó para que se distribuyan las peticiones a lo largo de 24 horas. Dentro del `with` se define una nueva variable para esto, llamada `start_time`, el cual utiliza el módulo `datetime.now()` para esto.

```python
with open(FILE_NAME, "w") as f: 
	start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
```

Por último, se modificaron las variables dentro del bucle `for`, simulando una hora aleatoria dentro del día. Se añaden entre 0 y 86,400 segundos (24 horas) a la fecha base.

```python
random_seconds = random.randint(0, 24 * 60 * 60)
current_time = start_time + timedelta(seconds=random_seconds)
timestamp = current_time.strftime("%d/%b/%Y:%H:%M:%S +0000")
```

