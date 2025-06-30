from flask import Flask, jsonify
from threading import Thread
import datetime

app = Flask('')

@app.route('/')
def home():
    return "El bot está corriendo!"

@app.route('/health')
def health():
    return jsonify({
        "status": "running",
        "bot_ready": False,
        "last_ready": datetime.datetime.utcnow().isoformat()
    })

def run_webserver():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_webserver)
    t.daemon = True
    t.start()
