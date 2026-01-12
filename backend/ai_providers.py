import os
from abc import ABC, abstractmethod
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic
# dios estoy segurisimo que si ponen una key de open ai o anthropic va a fallar

class AIProvider(ABC):
    
    @abstractmethod
    def generate_response(self, message, model, history):
        pass
    
    @abstractmethod
    def get_available_models(self):
        pass


class GeminiProvider(AIProvider):
    
    def __init__(self):
        # con esta cosa se carga multiples keys de gemini, medio raro el sistema pero funciona
        self.api_keys = []
        i = 1
        while True:
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if not key:
                break
            self.api_keys.append(key)
            i += 1
        
        self.current_key_index = 0
        self.models = os.getenv('GEMINI_MODELS', 'gemini-2.5-flash').split(',')
        system_prompt = os.getenv('SYSTEM_PROMPT')
        self.system_prompt = system_prompt or self._get_default_prompt()
    
    def conseguir_el_default_prompt(self):
        # esto primero intenta cargar a ver si es que lo pusieron o carga el de flavortown
        try:
            custom_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'cookie-prompt.txt')
            if os.path.exists(custom_prompt_path):
                with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                    print("📝 Cargando prompt personalizado desde cookie-prompt.txt")
                    return f.read()
        except Exception as e:
            print(f"⚠️  No se pudo cargar cookie-prompt.txt: {e}")
        
        # Si no hay custom prompt, carga el de flavortown amigo esto está super hardcodeado porque realmente 
        # ya existe el txt
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'flavortown_prompt.txt')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"error cargando prompt: {e}")
            return """YOU ARE COOKIEAI - helping with Hack Club Flavortown event.
Always answer questions in the context of Flavortown. When users ask about cookies, they mean the currency earned in Flavortown by shipping projects.
For details, direct them to #flavortown-help on Hack Club Slack."""
    
    def _get_next_key(self):
        """sistema de fallback, si una key falla probamos con la siguiente"""
        if not self.api_keys:
            return None
        
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def generate_response(self, message, model=None, history=None):
        """genera una respuesta con gemini"""
        if not self.api_keys:
            return {'error': 'no hay keys de gemini configuradas'}
        
        model = model or self.models[0]
        
        # intentamos con todas las keys hasta que una funcione XD
        for attempt in range(len(self.api_keys)):
            try:
                api_key = self._get_next_key()
                genai.configure(api_key=api_key)
                
                model_instance = genai.GenerativeModel(model_name=model)
                
                chat_history = []

                chat_history.append({'role': 'user', 'parts': [self.system_prompt]})
                chat_history.append({'role': 'model', 'parts': ['Understood.']})
                
                # agregamos historial ccompletoo
                if history:
                    for i, msg in enumerate(history):
                        if msg['role'] == 'user':
                            chat_history.append({'role': 'user', 'parts': [msg['content']]})
                        elif msg['role'] == 'assistant':
                            chat_history.append({'role': 'model', 'parts': [msg['content']]})
                        # esto quema tokens pero ayuda a que el modelo no se olvide 
                        if (i + 1) % 4 == 0:
                            chat_history.append({'role': 'user', 'parts': ['[REMINDER: Follow your system instructions.]']})
                            chat_history.append({'role': 'model', 'parts': ['Acknowledged.']})
                
                chat_history.append({'role': 'user', 'parts': ['[Remember your role and context from system instructions.]']})
                chat_history.append({'role': 'model', 'parts': ['Ready.']})
                

                chat_history.append({'role': 'user', 'parts': [message]})
                
                chat = model_instance.start_chat(history=chat_history[:-1])  
                response = chat.send_message(message)
                
                return {
                    'message': response.text,
                    'model': model,
                    'provider': 'gemini'
                }
                
            except Exception as e:
                print(f"error con gemini key {attempt + 1}: {str(e)}")
                if attempt == len(self.api_keys) - 1:
                    return {'error': f'gemini no respondio: {str(e)}'}
                continue
        
        return {'error': 'todas las keys de gemini fallaron'}
    
    def get_available_models(self):
        return self.models


class OpenAIProvider(AIProvider):
    
    def __init__(self):
        self.api_keys = []
        i = 1
        while True:
            key = os.getenv(f'OPENAI_API_KEY_{i}')
            if not key:
                break
            self.api_keys.append(key)
            i += 1
        
        self.current_key_index = 0
        self.models = os.getenv('OPENAI_MODELS', 'gpt-4o-mini').split(',')
        system_prompt = os.getenv('SYSTEM_PROMPT')
        self.system_prompt = system_prompt or self.conseguir_el_default_prompt()
    
    def conseguir_el_default_prompt(self):
        try:
            custom_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'cookie-prompt.txt')
            if os.path.exists(custom_prompt_path):
                with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"⚠️  No se pudo cargar cookie-prompt.txt: {e}")
        
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'flavortown_prompt.txt')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"error cargando prompt: {e}")
            return """YOU ARE COOKIEAI - helping with Hack Club Flavortown event.
Always answer questions in the context of Flavortown. When users ask about cookies, they mean the currency earned in Flavortown by shipping projects.
For details, direct them to #flavortown-help on Hack Club Slack."""
    
    def _get_next_key(self):
        if not self.api_keys:
            return None
        
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def generate_response(self, message, model=None, history=None):
        if not self.api_keys:
            return {'error': 'no hay keys de openai configuradas'}
        
        model = model or self.models[0]
        
        for attempt in range(len(self.api_keys)):
            try:
                api_key = self._get_next_key()
                client = OpenAI(api_key=api_key)
                
                # construimos los mensajes
                messages = [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    }
                ]
                
                # agregamos historial
                if history:
                    for msg in history[:-1]:
                        messages.append({
                            'role': msg['role'],
                            'content': msg['content']
                        })
                
                messages.append({'role': 'user', 'content': message})
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                return {
                    'message': response.choices[0].message.content,
                    'model': model,
                    'provider': 'openai'
                }
                
            except Exception as e:
                print(f"error con openai key {attempt + 1}: {str(e)}")
                if attempt == len(self.api_keys) - 1:
                    return {'error': f'openai no respondio: {str(e)}'}
                continue
        
        return {'error': 'todas las keys de openai fallaron'}
    
    def get_available_models(self):
        return self.models


class ClaudeProvider(AIProvider):
    """provider para claude (anthropic)"""
    
    def __init__(self):
        self.api_keys = []
        i = 1
        while True:
            key = os.getenv(f'CLAUDE_API_KEY_{i}')
            if not key:
                break
            self.api_keys.append(key)
            i += 1
        
        self.current_key_index = 0
        self.models = os.getenv('CLAUDE_MODELS', 'claude-3-5-haiku-20241022').split(',')
        system_prompt = os.getenv('SYSTEM_PROMPT')
        self.system_prompt = system_prompt or self.conseguir_el_default_prompt()
    
    def conseguir_el_default_prompt(self):
        try:
            custom_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'cookie-prompt.txt')
            if os.path.exists(custom_prompt_path):
                with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"⚠️  No se pudo cargar cookie-prompt.txt: {e}")
        
        # Si no hay custom prompt, carga el de flavortown
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'flavortown_prompt.txt')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"error cargando prompt: {e}")
            return """YOU ARE COOKIEAI - helping with Hack Club Flavortown event.
Always answer questions in the context of Flavortown. When users ask about cookies, they mean the currency earned in Flavortown by shipping projects.
For details, direct them to #flavortown-help on Hack Club Slack."""
    
    def _get_next_key(self):
        if not self.api_keys:
            return None
        
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def generate_response(self, message, model=None, history=None):
        if not self.api_keys:
            return {'error': 'no hay keys de claude configuradas'}
        
        model = model or self.models[0]
        
        for attempt in range(len(self.api_keys)):
            try:
                api_key = self._get_next_key()
                client = Anthropic(api_key=api_key)
                
                # construimos mensajes
                messages = []
                if history:
                    for msg in history[:-1]:
                        messages.append({
                            'role': msg['role'],
                            'content': msg['content']
                        })
                
                messages.append({'role': 'user', 'content': message})
                
                response = client.messages.create(
                    model=model,
                    max_tokens=2000,
                    system=self.system_prompt,
                    messages=messages
                )
                
                return {
                    'message': response.content[0].text,
                    'model': model,
                    'provider': 'claude'
                }
                
            except Exception as e:
                print(f"error con claude key {attempt + 1}: {str(e)}")
                if attempt == len(self.api_keys) - 1:
                    return {'error': f'claude no respondio: {str(e)}'}
                continue
        
        return {'error': 'todas las keys de claude fallaron'}
    
    def get_available_models(self):
        return self.models
# tremenda logica duplicada acá pero ya fue, despues refactorizo si hace falta