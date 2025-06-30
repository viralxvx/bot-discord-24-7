from flask import Flask, jsonify, request
import atexit
from threading import Thread
from .config import bot
from .state_management import save_state
from .utils import Session

app = Flask('')

@app.route('/')
def home():
    return "El bot está corriendo!"

@app.route('/health')
def health():
    return jsonify({
        "status": "running",
        "bot_ready": bot.is_ready(),
        "last_ready": datetime.datetime.utcnow().isoformat()
    })

@app.route('/state', methods=['GET'])
def get_state():
    api_key = request.args.get("api_key")
    if api_key != os.environ.get("API_KEY", "your-secret-key"):
        return jsonify({"error": "Unauthorized"}), 401
    session = Session()
    try:
        state = session.query(State).first() or {}
        return jsonify(state.faltas_dict if state else {})
    finally:
        session.close()

atexit.register(lambda: save_state(log=True))

def run_webserver():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_webserver)
    t.daemon = True
    t.start()
