from flask import Flask, jsonify, render_template
import json
import os

app = Flask(__name__)

# --- RUTAS DE LA API (Para maquinas/frontend) ---


@app.route('/api/datos')
def obtener_datos():
    """
    Lee el JSON generado por main.py y lo expone como una API REST.
    """
    if not os.path.exists('reporte.json'):
        # Si el usuario no ha corrido main.py, devolvemos un error HTTP 404
        return jsonify({"error": "El archivo reporte.json no existe. Ejecuta main.py primero."}), 404

    with open('reporte.json', 'r', encoding='utf-8') as f:
        datos = json.load(f)

    return jsonify(datos)

# --- RUTAS DE LA INTERFAZ WEB (Para humanos) ---


@app.route('/')
def index():
    """
    Página principal. Renderiza el Dashboard HTML.
    """
    # render_template busca automáticamente dentro de la carpeta 'templates/'
    return render_template('index.html')


if __name__ == '__main__':
    # Arrancamos el servidor en modo debug (se reinicia solo si cambias el codigo)
    # Escucha en el puerto 5000
    print("Iniciando servidor Backend...")
    app.run(debug=True, host='0.0.0.0', port=5000)
