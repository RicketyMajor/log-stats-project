import random
import time
from datetime import datetime, timedelta

FILE_NAME = "server.log"
NUM_LINES = 10000

IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.5", "192.168.1.200", "8.8.8.8"]
STATUS_CODES = [
    200,
    200,
    200,
    201,
    400,
    401,
    403,
    404,
    404,
    500,
    502,
    503
]

PATHS = [
    "/home",
    "/about",
    "/contact",
    "/api/login",
    "/api/products",
    "/assets/css/style.css",
    "/assets/js/app.js",
    "/admin"
]
METHODS = ["GET", "GET", "GET", "POST", "PUT", "DELETE"]

print(
    f"Generando {FILE_NAME} con {NUM_LINES} lineas distribuidas en 24 horas...")

with open(FILE_NAME, "w", encoding="utf-8") as f:
    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for _ in range(NUM_LINES):
        ip = random.choice(IPS)
        random_seconds = random.randint(0, 24 * 60 * 60)
        current_time = start_time + timedelta(seconds=random_seconds)
        timestamp = current_time.strftime("%d/%b/%Y:%H:%M:%S +0000")
        method = random.choice(METHODS)
        path = random.choice(PATHS)
        status = random.choice(STATUS_CODES)
        size = random.randint(100, 5000)
        line = f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size}\n'
        f.write(line)

print("Archivo creado.")
