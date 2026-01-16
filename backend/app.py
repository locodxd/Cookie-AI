from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import time
import json
import io
import base64
import shutil
from pathlib import Path
from ai_providers import GeminiProvider
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from dotenv import load_dotenv
from json_store import JsonChatStore
from PIL import Image


load_dotenv()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 
CORS(app)
# esto se puede cambiar en el env pero lo dejo aca hardcoded pq si
MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', 5))
RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', 10))

# rate limit para que no me quemen todos los tokens
rate_limit_storage = {}
chat_rate_limit_storage = {}
providers = {
    'gemini': GeminiProvider()
}

STORE_DIR = os.getenv("STORE_DIR", "data/store")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
PERSIST_VIDEOS = os.getenv("PERSIST_VIDEOS", "true").lower() == "true"
MAX_SESSION_MESSAGES = int(os.getenv("MAX_SESSION_MESSAGES", 200))
store = JsonChatStore(
    root_dir=STORE_DIR,
    compact_every_events=int(os.getenv("STORE_COMPACT_EVERY", 25)),
    compact_if_wal_kb=int(os.getenv("STORE_COMPACT_WAL_KB", 512)),
    max_messages_per_session=MAX_SESSION_MESSAGES,
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "images").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "videos").mkdir(parents=True, exist_ok=True)


def check_rate_limiting_por_ips(ip_address):
    current_time = datetime.now()
    
    if ip_address not in rate_limit_storage:
        rate_limit_storage[ip_address] = {
            'messages': [],
            'reset_time': current_time + timedelta(seconds=RATE_LIMIT_SECONDS)
        }
    
    user_data = rate_limit_storage[ip_address]
    
    user_data['messages'] = [
        msg_time for msg_time in user_data['messages']
        if current_time - msg_time < timedelta(seconds=RATE_LIMIT_SECONDS)
    ]
    
    if len(user_data['messages']) >= MAX_MESSAGES:
        time_until_reset = (user_data['messages'][0] + timedelta(seconds=RATE_LIMIT_SECONDS) - current_time).seconds
        return False, time_until_reset
    
    user_data['messages'].append(current_time)
    return True, 0


def check_rate_limiting_por_chat(session_id):
    WINDOW_SECONDS = int(os.getenv('CHAT_RATE_WINDOW', 3600))  # window to count messages (default 1h)
    now = datetime.now()

    if session_id not in chat_rate_limit_storage:
        chat_rate_limit_storage[session_id] = {'messages': []}

    data = chat_rate_limit_storage[session_id]
    data['messages'] = [t for t in data['messages'] if now - t < timedelta(seconds=WINDOW_SECONDS)]
    count = len(data['messages']) + 1 
    if count <= 2:
        data['messages'].append(now)
        return True, 0

    required_wait = RATE_LIMIT_SECONDS * (count - 2)
    last_time = data['messages'][-1] if data['messages'] else None
    if last_time:
        elapsed = (now - last_time).total_seconds()
    else:
        elapsed = float('inf')

    if elapsed < required_wait:
        wait = int(required_wait - elapsed) + 1
        return False, wait

    data['messages'].append(now)
    return True, 0

def save_image_base64(image_data: str, session_id: str) -> str:
    decoded = base64.b64decode(image_data)
    if len(decoded) < 100:
        raise ValueError("imagen muy chica o corrupta")

    img = Image.open(io.BytesIO(decoded))

    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    max_size = 2048
    if img.width > max_size or img.height > max_size:
        ratio = min(max_size / img.width, max_size / img.height)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)

    sess_dir = UPLOAD_DIR / "images" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)

    fname = f"img_{int(time.time()*1000)}.jpg"
    out_path = sess_dir / fname

    img.save(out_path, format="JPEG", quality=85, optimize=True)

    return str(out_path.relative_to(UPLOAD_DIR))
def persist_video_file(temp_video_path: str, session_id: str, original_name: str | None) -> str:
    src = Path(temp_video_path)
    sess_dir = UPLOAD_DIR / "videos" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(original_name or "") or f"video_{int(time.time()*1000)}.mp4"
    dst = sess_dir / f"{int(time.time()*1000)}_{safe_name}"

    shutil.copy2(src, dst)
    return str(dst.relative_to(UPLOAD_DIR))
def conseguir_conversation_history(session_id, max_messages=10):
    return store.get_history(session_id, limit=max_messages)
def añadir_to_history(session_id, role, content, attachments=None, model=None):
    store.append_message(session_id, role, content, attachments=attachments, model=model)
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        allowed, wait_time = check_rate_limiting_por_ips(ip_address)
        if not allowed:
            return jsonify({
                'error': f'tranqui pa, espera {wait_time} segundos',
                'wait_time': wait_time
            }), 429
        if request.is_json:
            data = request.json
            user_message = data.get('message', '').strip()
            image_data = data.get('image')
            provider_name = data.get('provider', 'gemini').lower()
            model_name = data.get('model')
            session_id = data.get('session_id', 'default')
            video_file = None
        else:
            user_message = request.form.get('message', '').strip()
            image_data = None
            provider_name = request.form.get('provider', 'gemini').lower()
            model_name = request.form.get('model')
            session_id = request.form.get('session_id', 'default')
            video_file = request.files.get('video')
        if image_data:
            print(f" Imagen recibida: {len(image_data)} chars de base64")
        elif video_file:
            print(f" Video recibido: {video_file.filename}")
        else:
            print(" Ni imagen ni video")
        if not user_message and not image_data:
            return jsonify({'error': 'manda algo loco'}), 400
        if len(user_message) > 4000:
            return jsonify({'error': 'mensaje muy largo, corta un toque'}), 400
        if provider_name not in providers:
            return jsonify({'error': 'ese provider no existe brother'}), 400

        allowed_chat, wait_chat = check_rate_limiting_por_chat(session_id)
        if not allowed_chat:
            return jsonify({'error': f'limite por chat, espera {wait_chat}s', 'wait_time': wait_chat}), 429

        attachments = {}

        if image_data:
            try:
                rel = save_image_base64(image_data, session_id)
                attachments["image"] = rel
            except Exception as e:
                return jsonify({"error": f"No se pudo guardar la imagen: {str(e)[:120]}"}), 400

        video_path = None
        persisted_video_rel = None

        if video_file:
            temp_dir = tempfile.gettempdir()
            filename = secure_filename(video_file.filename) or f"video_{int(time.time())}.mp4"
            video_path = os.path.join(temp_dir, filename)
            video_file.save(video_path)
            print(f"   Video guardado en: {video_path}")

            if PERSIST_VIDEOS:
                try:
                    persisted_video_rel = persist_video_file(video_path, session_id, video_file.filename)
                    attachments["video"] = persisted_video_rel
                except Exception as e:
                    print(f" No se pudo persistir video: {e}")

        try:
            añadir_to_history(session_id, 'user', user_message, attachments=attachments)
            history = conseguir_conversation_history(session_id, max_messages=10)
            provider = providers[provider_name]
            response = provider.generate_response(user_message, model_name, history, image_data=image_data, video_path=video_path)
            if response.get('error'):
                return jsonify(response), 500
            añadir_to_history(session_id, 'assistant', response['message'], model=response.get('model'))
        finally:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                print(f"     Video temporal eliminado")
        
        return jsonify(response), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"error en chat: {str(e)}")
        return jsonify({'error': f'Algo salio mal pa: {str(e)}'}), 500
@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        models = {}
        for provider_name, provider in providers.items():
            models[provider_name] = provider.get_available_models()
        
        return jsonify(models), 200
    except Exception as e:
        print(f"error obteniendo modelos: {str(e)}")
        return jsonify({'error': 'no se pudieron cargar los modelos'}), 500
@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        store.clear_session(session_id)
        return jsonify({'message': 'historial borrado'}), 200
    except Exception as e:
        return jsonify({'error': 'no se pudo borrar el historial'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'todo piola',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"🍪 CookieAI corriendo en puerto {port}")
    print(f" Rate limit: {MAX_MESSAGES} mensajes cada {RATE_LIMIT_SECONDS}s")
    
    app.run(host='0.0.0.0', port=port, debug=debug)