## Resumen

El `main.py` de este proyecto es básicamente el analizador de logs de servidor web en formato CLF. El objetivo de esta es servir como una herramienta CLI que extrae estadísticas de archivos de logs sin cargar todo en memoria. 
Para usarlo, se debe ejecutar en la terminal `python3 main.py <ruta_del_archivo_log>` (por ejemplo, `python3 main.py server.log`). Como salida, genera las siguientes estadísticas:
- Total de peticiones.
- Tráfico total transferido (en formato legible: KB, MB, GB).
- Tamaño promedio de respuesta.
- Top 5 IPs más activas (con porcentajes).
- Distribución de códigos de estado HTTP (con porcentajes).

## Importaciones

Para este código, se usaron las siguientes importaciones: `sys`, que se usa para acceder a argumentos de línea de comandos (`sys.argv`) y salir del programa (`sys.exit`); `re`, que es para usar expresiones regulares (regex) y parsear el formato de log; y por último `Counter`, que es un estructura de datos optimizada para contar elementos.

```python
import sys 
import re
from collections import Counter
```

## Patrón de Expresión Regular (Regex)

Este patrón (la constante para parsear el formato CLF) define cómo identificar y extraer datos de cada línea de log. El formato esperado viene siendo `IP - - [timestamp] "METHOD path HTTP/version" status size` (por ejemplo, `192.168.1.1 - - [27/Nov/2025:10:00:00 +0000] "GET /home HTTP/1.1" 200 1234`).

```python
LOG_PATTERN = r'^(\S+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'
```

A continuación, se desglosa de mejor forma este patrón:

- `^`: Inicio de línea (asegura que coincida desde el principio).
- `(\S+)`: GRUPO 1: uno o más caracteres NO-espacio → captura la IP.
- `- -`: Texto literal: dos guiones con espacios (campos RFC1413 y auth).
- `\[`: Corchete literal (escapado porque `[` tiene significado especial en regex).
- `(.*?)`: GRUPO 2: cualquier carácter, modo NO-codicioso (mínimo posible) → timestamp.
- `\]`: Corchete de cierre literal.
- `"`: Comillas literales.
- `(.*?)`: GRUPO 3: cualquier carácter NO-codicioso → "METHOD path HTTP/version".
- `"`: Comillas de cierre.
- `(\d+)`: GRUPO 4: uno o más dígitos → código de estado HTTP (200, 404, etc.).
- `(\d+)`: GRUPO 5: uno o más dígitos → tamaño de respuesta en bytes.
- `$`: Final de línea (asegura que coincida hasta el final).

El prefijo `r` es una raw string, la cual evita que Python interprete `\` como escape. Si este prefijo, se necesitaría escribir `\\[` en vez de `\[`.

## Funciones Auxiliares

```python
def format_bytes(size):
```

Esta función convierte bytes a formato legible para humanos (B, KB, MB). El algoritmo consiste en dividir repetidamente por 1024 hasta que el número sea < 1024, lo que iría incrementando la etiqueta de unidad en cada división.
El argumento `size()` permite una cantidad de bytes, la cual es un float. Retorna un string que indica el tamaño formateado con 2 decimales y su unidad. 

```python
format_bytes(500) # "500.00 B"
format_bytes(2048) # "2.00 KB"
format_bytes(5242880) # "5.00 MB"
```

Dentro de esta función, se definen algunas variables clave para su correcta ejecución. Por ejemplo, se tiene la variable `power`, la cual define que $1024 \ bytes = 1 \ KB$ (estándar binario IEC, no decimal SI). Se define además, una variable `n` como cero, el cuál indica el índice de la unidad actual (0=B, 1=KB, 2=MB, 3=GB). Directamente, el diccionario `power_labels` mapea el índice con la etiqueta de la unidad correspondiente.

```python
power = 2**10 
n = 0
power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}
```

Se define un bucle `while`, el cual funciona de la siguiente manera: mientras el tamaño sea mayor a 1024, divide y sube de unidad (por ejemplo, `2048/1024 = 2 KB`, sale del bucle). Por lo que divide el tamaño por 1024 e incrementa el índice de la unidad.

```python
while size > power:
	size /= power
	n += 1
```

Por último, retorna en un formato de dos decimales.

```python
return f"{size:.2f} {power_labels[n]}"
```

## Función Principal de Procesamiento

```python
def process_log_file(file_path):
print(f"--- Iniciando analisis de: {file_path} ---\n")
```

Esta función procesa un archivo de logs línea por línea y genera estadísticas. Algunas de las ventajas de este enfoque son:
- No carga todo el archivo en memoria, lo cual es eficiente para logs gigantes.
- Procesa cada línea inmediatamente y la descarta.
- Usa `Counter` para acumular estadísticas de forma eficiente.
Utiliza como argumento la variable `file_path` (string), la cual es la ruta del archivo de logs a analizar. Este no retorna nada, imprime directamente en la consola.

Pasando a la inicialización de acumuladores dentro la función anterior, se definen un par de variables: `total_request` es un contador simple, ya que cuenta cuántas líneas válidas se procesaron; `total_bytes` es una acumulador que suma todos los tamaños de respuesta (en bytes).
El módulo `Counter` anteriormente importado se hace presente. `Counter` es un diccionario especializado en contar elementos. Este no necesita verificar si la clave existe antes de incrementar, lo cual es una ventaja sobre un diccionario normal.
La variable `ip_counter` utiliza este modulo para contar cuántas veces aparece cada IP, al igual que `status_counter`, la cual cuenta cuántas veces aparece cada código HTTP.

```python
total_requests = 0
total_bytes = 0
ip_counter = Counter()
status_counter = Counter()
```

Se implementa además, un bloque de manejo de errores con `try-except`, el cual atrapa errores comunes para que el programa no se "crashee" sin explicación.
El gestor de contexto `with` se implementa para cerrar el archivo automáticamente al salir. Establece un modo lectura con `r` (read) y un `encoding='utf-8'` para soportar caracteres internacionales.

```python
try:
	with open(file_path, 'r', encoding='utf-8') as f:
```

## Iteración Línea por Línea 

```python
for line in f:
```

Esta es la clave para la eficiencia. Este `for` hace que no se cargue todo el archivo en memoria. Python lee línea por línea bajo demanda, lo que permite procesar archivos de Terabytes con poca RAM.
Dentro de este bucle, se define la variable `line` con el módulo `line.strip()`, el cual elimina espacios, tabulaciones y saltos de línea al inicio/final.
Para la validación estos saltos de línea vacías, se define una condición, la cual es `True` si `line == ""`, o sea, un string vacío.
Gracias a `continue`, se salta a la siguiente iteración del bucle.

```python
line = line.strip()
if not line:
	continue
```

## Aplicación de Regex

Para aplicar el regex, se define una variable, con un valor igual al módulo `re.match(patron, texto)`. Este intenta hacer coincidir el patrón desde el inicio, y devuelve el objeto `Match` si coincide, `None` en caso contrario. Este lo sigue una condición en el caso de que el regex haya coincidido (la línea tiene el formato correcto). 
Una diferencia notable con el módulo `re.search()` para este caso es que `match` solo busca al inicio, mientras que `search` busca en toda la línea. 

```python
match = re.match(LOG_PATTERN, line)
if match:
```

## Extracción de Grupos Capturados

Dentro de la condición `if` anterior se definen varias variables con el módulo de `match.group(n)`, el cual devuelve el contenido del grupo N del regex. Los grupos se enumeran desde 1 y no desde 0, ya que este último devuelve toda la coincidencia completa.

```python
ip = match.group(1) # GRUPO 1: IP del cliente
status = match.group(4) # GRUPO 4: código de estado HTTP (string)
size_str = match.group(5) # GRUPO 5: tamaño en bytes (string)
```

## Actualización de Estadísticas

Se incrementan los contadores previamente definidos. La variable `total_bytes` es un caso especial de incremento, puesto que su argumento `size_str` es un string `"1234"`, por lo que se necesita `int()` para sumar. Es posible que este `int()` pueda lanzar `ValueError` si el string no es numérico, pero este se atrapa más adelante.

```python
total_requests += 1
ip_counter[ip] += 1
status_counter[status] += 1
total_bytes += int(size_str)
```

En el caso que la línea no coincida con el patrón (`else`), la ignoraría silenciosamente. En una próxima actualización, se van a loggear estas líneas en un archivo de errores.

```python
else:
	continue
```

## Generación de Reporte (Salida)

Esta es la parte que se muestra en la terminal, la salida. Para ello, existen muchos `print()`distintos que envuelven casos específicos o simplemente arrojan aquellos resultados previamente procesados por la lógica. Partiendo por un bloque de condición, el cual valida el caso borde de archivo vacío. Su objetivo es funcionar como una programación defensiva, que sale de la función sin devolver nada (`return None` implícito).

```python
if total_requests == 0:
	print("El archivo esta vacio o no se encontraron lineas validas.")
	return
```

En caso que `total_request =! 0`, la secuencia sigue su curso normal. Se hace un cálculo de métricas derivadas, el cual es una división entre el total de bytes y el total de peticiones, resultando un promedio del tipo `float`.

```python
avg_size = total_bytes / total_requests
```

Con las estadísticas recopiladas hasta ahora, empiezan los primeros `print()`. Se imprimen tanto el total de peticiones (`total_requests`), tráfico total (`total_bytes`) y el tamaño promedio de las peticiones (`avg_size`). Estos últimos usan la función helper para un formato legible (B, KB, MB, etc.).

```python
print(f"Total de peticiones  : {total_requests}")
print(f"Trafico total        : {format_bytes(total_bytes)}")
print(f"Tamano promedio      : {format_bytes(avg_size)}")
```

Seguido, se define un bucle `for` para imprimir un top cinco de las IPs más activas, usando el módulo `.most_common(n)` para devolver la lista de tuplas `[(elemento, count), ...]` ordenada por count. Por ejemplo, `[('192.168.1.1', 3500), ('10.0.0.1', 2800), ...]`.
Dentro del `for`, se calcula un porcentaje. Finalmente, se imprime en un formato `string` que alinea `ip` a la izquierda con 15 caracteres de ancho.

```python
print("\n--- Top 5 IPs (Clientes mas activos) ---")

for ip, count in ip_counter.most_common(5):
	percentage = (count / total_requests) * 100
	print(f"{ip:<15} : {count} peticiones ({percentage:.1f}%)")
```

Terminado este top, se crea otro bucle `for` para la distribución de códigos de estado HTTP. Se usa el módulo `sorted(dict.items())` para ordenar las tuplas `(clave, valor)` por clave. Por ejemplo, `Counter({'200': 5000, '404': 300, '500': 100} → [('200', 5000), ('404', 300), ('500', 100)]`, lo cual muestra los códigos en orden numérico. Una alternativa también es usar `most.common()` para ordenar por frecuencia (más común primero).
Dentro del `for` se calculan los porcentajes correspondientes y se alinea `count` a la izquierda con 5 caracteres. Hace que los porcentajes se alineen verticalmente.

```python
print("\n--- Distribucion de Codigos de Estado ---")

for status, count in sorted(status_counter.items()):
	percentage = (count / total_requests) * 100
	print(f"Status {status}     : {count:<5} ({percentage:.1f}%)")
```

Por último, se definen múltiples bloques `except` para el manejo de excepciones y captura de errores esperados. Primero aquellos más específicos, luego los genéricos
El primer `except` maneja un error específico, el cual es cuando el archivo no existe en la ruta especificada. Se lanza cuando `open()` no puede encontrar el archivo.

```python
except FileNotFoundError:
	print(f"Error: El archivo '{file_path}' no existe.")
```

El segundo `except` maneja un error de conversión de tipos. Ocurre si `int(size_str)` falla. Por ejemplo, cuando una línea tiene texto en vez de un número en el campo `size`.

```python
except ValueError:
	print("Error: Se encontro un dato no numerico donde se esperaba un numero.")
```

El último `except` captura cualquier otro error no anticipado. Estos errores son guardados como objeto en la variable `e`, el cual contiene información sobre qué salió mal.

```python
except Exception as e:
	print(f"Ocurrio un error inesperado: {e}")
```

## Punto de Entrada del Programa

Un patrón común en Python es el distinguir entre "ejecutar" vs "importar". La variable especial `__name__` es asignada por Python para evitar que el código se ejecute accidentalmente al importar el módulo. 

```python
if __name__ == "__main__":
```

## Validación de Argumentos de Línea de Comandos

Básicamente más formalidades de los códigos y sus interacciones al ejecutarlos en terminal. Ya que `sys.argv` es una lista con todos los argumentos pasados al script, al colocarlo dentro de la condicional `if`, se valida que el usuario haya pasado exactamente 1 argumento (además del nombre del script). Si la validación falla, mostrará un mensaje de asistencia.
Finalmente, `sys.exit(codigo)` termina el programa inmediatamente, dependiendo del código de salida:
- 0 = éxito (todo está bien).
- 1-255 = error (diferentes tipos de errores).
Los scripts que llamen a este programa pueden verificar el código de salida.

```python
if len(sys.argv) != 2:
	print("Uso correcto: python3 main.py <ruta_del_log>")
	sys.exit(1)
```

## Extracción del Argumento y Ejecución

Si se llega hasta aquí, la validación ha sido un éxito: se tiene exactamente 1 argumento. El módulo `sys.argv[]` extrae la ruta del archivo (segundo elemento de la lista). 
Se llama a la función principal con la ruta proporcionada. El procesamiento completo ocurre dentro de `process_log_file()`. Al terminar este, el programa finaliza naturalmente y el código de salida implícito es 0 (éxito).

```python
log_file = sys.argv[1]
process_log_file(log_file)
```