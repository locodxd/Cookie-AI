from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
from pathlib import Path

from ai_providers import GeminiProvider, OpenAIProvider, ClaudeProvider

load_dotenv()

app = Flask(__name__)
CORS(app)

# === CONFIG ===
MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', 5))
RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', 10))

# rate limit para que no me quemen todos los tokens
rate_limit_storage = {}

conversation_history = {}

# inicializamos los providers
providers = {
    'gemini': GeminiProvider(),
    'openai': OpenAIProvider(),
    'claude': ClaudeProvider()
}


def check_rate_limit(ip_address):
    """che, fijate si no esta spameando mucho"""
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


def get_conversation_history(session_id, max_messages=10):

    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    return conversation_history[session_id][-max_messages:]


def add_to_history(session_id, role, content):
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
        # sacamos la IP para el rate limiting
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # verificamos rate limit
        allowed, wait_time = check_rate_limit(ip_address)
        if not allowed:
            return jsonify({
                'error': f'tranqui pa, espera {wait_time} segundos',
                'wait_time': wait_time
            }), 429
        
        data = request.json
        user_message = data.get('message', '').strip()
        provider_name = data.get('provider', 'gemini').lower()
        model_name = data.get('model')
        session_id = data.get('session_id', 'default')
        
        # validaciones basicas
        if not user_message:
            return jsonify({'error': 'manda algo loco'}), 400
        
        if len(user_message) > 4000:
            return jsonify({'error': 'mensaje muy largo, corta un toque'}), 400
        
        if provider_name not in providers:
            return jsonify({'error': 'ese provider no existe che'}), 400
        
        add_to_history(session_id, 'user', user_message)
        
        history = get_conversation_history(session_id)
        
        provider = providers[provider_name]
        response = provider.generate_response(user_message, model_name, history)
        
        if response.get('error'):
            return jsonify(response), 500
        
        add_to_history(session_id, 'assistant', response['message'])
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"error en chat: {str(e)}")
        return jsonify({'error': 'algo salio mal pa, intenta de nuevo'}), 500


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
