from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
from pathlib import Path

from ai_providers import GeminiProvider

load_dotenv()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max request size (video support)
CORS(app)
# esto se puede cambiar en el env pero lo dejo aca hardcoded pq si
MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', 5))
RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', 10))

# rate limit para que no me quemen todos los tokens
rate_limit_storage = {}

conversation_history = {}

# Only Gemini provider is supported (OpenAI/Claude removed)
providers = {
    'gemini': GeminiProvider()
}


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


def conseguir_conversation_history(session_id, max_messages=10):

    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    return conversation_history[session_id][-max_messages:]
def añadir_to_history(session_id, role, content):
    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    conversation_history[session_id].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })

    if len(conversation_history[session_id]) > 50:
        conversation_history[session_id] = conversation_history[session_id][-50:]


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
        
        # Manejo de JSON 
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
            print(f"📸 Imagen recibida: {len(image_data)} chars de base64")
        elif video_file:
            print(f"🎥 Video recibido: {video_file.filename} ({video_file.content_length / 1024 / 1024:.2f}MB)")
        else:
            print("📭 Ni imagen ni video")
        
        # algunas validaciones basicas
        if not user_message and not image_data:
            return jsonify({'error': 'manda algo loco'}), 400
        if len(user_message) > 4000:
            return jsonify({'error': 'mensaje muy largo, corta un toque'}), 400
        if provider_name not in providers:
            return jsonify({'error': 'ese provider no existe brother'}), 400
        # Guardar video temporalmente si existe
        video_path = None
        if video_file:
            import tempfile
            temp_dir = tempfile.gettempdir()
            video_path = os.path.join(temp_dir, video_file.filename)
            video_file.save(video_path)
            print(f"   ✅ Video guardado en: {video_path}")
        
        try:
            añadir_to_history(session_id, 'user', user_message)
            history = conseguir_conversation_history(session_id)
            provider = providers[provider_name]
            response = provider.generate_response(user_message, model_name, history, image_data=image_data, video_path=video_path)
            if response.get('error'):
                return jsonify(response), 500
            añadir_to_history(session_id, 'assistant', response['message'])
        finally:
            # Limpiar archivo temporal
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                print(f"   🗑️  Video temporal eliminado")
        
        return jsonify(response), 200
    except Exception as e:
        print(f"error en chat: {str(e)}")
        return jsonify({'error': 'Something salio mal pa, intenta de nuevo'}), 500
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
        if session_id in conversation_history:
            conversation_history[session_id] = []
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
    print(f"💾 Rate limit: {MAX_MESSAGES} mensajes cada {RATE_LIMIT_SECONDS}s")
    
    app.run(host='0.0.0.0', port=port, debug=debug)