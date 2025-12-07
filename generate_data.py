import random
import time

FILE_NAME = "server.log"
NUM_LINES = 10000

IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.5", "192.168.1.200", "8.8.8.8"]

STATUS_CODES = [
    200,
    200,
    200,
    404,
    500,
    301
]

PATHS = [
    "/home",
    "/about",
    "/contact",
    "/api/login",
    "/assets/logo.png"
]

print(f"Generando {FILE_NAME} con {NUM_LINES} lineas...")

with open(FILE_NAME, "w", encoding="utf-8") as f:
    for _ in range(NUM_LINES):
        ip = random.choice(IPS)
        timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
        method = random.choice(["GET", "POST", "PUT"])
        path = random.choice(PATHS)
        status = random.choice(STATUS_CODES)
        size = random.randint(100, 5000)
        line = f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size}\n'
        f.write(line)

print("Archivo creado.")
