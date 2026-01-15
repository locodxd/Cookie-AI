import os
import time
from abc import ABC, abstractmethod
import google.generativeai as genai
from PIL import Image
import io
import base64

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
        raw_models = os.getenv('GEMINI_MODELS', 'gemini-2.5-flash')
        self.models = [m.strip() for m in raw_models.split(',') if m.strip()]
        system_prompt = os.getenv('SYSTEM_PROMPT')
        self.system_prompt = system_prompt or self._get_default_prompt()
    
    def _get_default_prompt(self):
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
        if not self.api_keys:
            return None
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def generate_response(self, message, model=None, history=None, image_data=None, video_path=None):
        if not self.api_keys:
            return {'error': 'no hay keys de gemini configuradas'}
        
        model = model or self.models[0]
        
        # con esto se asume q todos los modelos son multimodales, si no lo son gg 
        
        # Intentar con el modelo pedido primero, luego con otros si falla
        models_to_try = [model]
        for alt in self.models:
            if alt != model:
                models_to_try.append(alt)
        
        for try_model in models_to_try:
            for attempt in range(len(self.api_keys)):
                try:
                    api_key = self._get_next_key()
                    genai.configure(api_key=api_key)
                    
                    # Usar system_instruction directamente en el modelo (más limpio)
                    model_instance = genai.GenerativeModel(
                        model_name=try_model,
                        system_instruction=self.system_prompt
                    )
                    
                    parts = []
                    if message:
                        parts.append(message)
                    
                    if image_data:
                        try:
                            decoded = base64.b64decode(image_data)
                            if len(decoded) < 100:
                                raise ValueError("imagen muy chica o corrupta")
                            
                            # Abrir imagen desde bytes
                            img_bytes = io.BytesIO(decoded)
                            img = Image.open(img_bytes)
                            
                            if img.mode in ('RGBA', 'LA', 'P'):
                                # Crear fondo blanco
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                                img = background
                            elif img.mode not in ('RGB', 'L'):
                                img = img.convert('RGB')
                            
                            max_size = 2048
                            if img.width > max_size or img.height > max_size:
                                ratio = min(max_size / img.width, max_size / img.height)
                                new_size = (int(img.width * ratio), int(img.height * ratio))
                                img = img.resize(new_size, Image.Resampling.LANCZOS)
                                print(f"🔽 Imagen redimensionada a {new_size}")
                            
                            img_io = io.BytesIO()
                            img.save(img_io, format='JPEG', quality=85, optimize=True)
                            img_io.seek(0)
                            
                            final_img = Image.open(img_io)
                            parts.append(final_img)
                            
                            print(f"✅ Imagen procesada: {final_img.size}, modo: {final_img.mode}, ~{len(img_io.getvalue())//1024}KB")
                        except Exception as img_error:
                            print(f"❌ Error procesando imagen: {img_error}")
                            import traceback
                            traceback.print_exc()
                            return {'error': f'No se pudo procesar la imagen: {str(img_error)[:100]}'}
                    
                    if video_path:
                        try:
                            print(f" Subiendo video a Gemini: {video_path}")
                            # Dejamos que Gemini detecte el mime_type por la extensión
                            video_file = genai.upload_file(path=video_path)
                            print(f" Video subido: {video_file.name}. Procesando...")
                            
                            # Polling para esperar a que el video esté listo (ACTIVE)
                            # Esto es CRUCIAL para videos en Gemini
                            max_retries = 60 # 60 segundos de espera
                            for _ in range(max_retries):
                                file_info = genai.get_file(video_file.name)
                                if file_info.state.name == "ACTIVE":
                                    print(" ✅ Video listo (Estado: ACTIVE)")
                                    break
                                elif file_info.state.name == "FAILED":
                                    raise ValueError("El procesamiento del video falló en los servidores de Gemini")
                                
                                time.sleep(1)
                            else:
                                raise ValueError("Timeout esperando el procesamiento del video")

                            parts.append(video_file)
                            print(f" Video adjuntado exitosamente")
                        except Exception as video_error:
                            print(f" Error subiendo video: {video_error}")
                            import traceback
                            traceback.print_exc()
                            return {'error': f'No se pudo procesar el video: {str(video_error)[:100]}'}

                    if not parts:
                        return {'error': 'mandá algo pa'}
                    
                    # Formatear historial asegurando que alterne roles correctamente.
                    # Como vamos a usar send_message(), el historial debe terminar en un mensaje del 'model'.
                    formatted_history = []
                    if history:
                        # Buscamos el último mensaje del asistente para cerrar el historial ahí
                        last_model_idx = -1
                        for i in range(len(history) - 1, -1, -1):
                            if history[i]['role'] == 'assistant' or history[i]['role'] == 'model':
                                last_model_idx = i
                                break
                        
                        if last_model_idx != -1:
                            # Incluimos hasta el último mensaje del modelo
                            for msg in history[:last_model_idx + 1]:
                                role = 'user' if msg['role'] == 'user' else 'model'
                                # Evitar mensajes vacíos en el historial
                                content = msg.get('content', '').strip()
                                if content:
                                    formatted_history.append({'role': role, 'parts': [content]})
                    
                    print(f" 📜 Historial formateado con {len(formatted_history)} mensajes")
                    
                    # La forma oficial más estable es usar start_chat si hay historia
                    chat_session = model_instance.start_chat(history=formatted_history)
                    response = chat_session.send_message(parts)

                    if not response or not response.text:
                        raise ValueError("Respuesta vacía del modelo")
                    
                    if try_model != model:
                        print(f"✨ Respuesta usando modelo alternativo: {try_model}")
                    
                    return {
                        'message': response.text,
                        'model': try_model,
                        'provider': 'gemini'
                    }
                except Exception as e:
                    error_str = str(e).lower()
                    print(f" ❌ Error con {try_model} (key {attempt + 1}): {str(e)}")
                    
                    # Si recibimos un 500 o error de servidor de Google, podríamos querer reintentar
                    # pero si es un error de formato (400), mejor saltar o fallar.
                    if "400" in error_str or "invalid" in error_str:
                        return {'error': f'Error en el formato del mensaje: {str(e)}'}
                    
                    if image_data and ('no soporta' in error_str or 'not support' in error_str or 'vision' in error_str):
                        print(f"   ⚠️  {try_model} no soporta imágenes, probando con otro...")
                        break  
                    
                    if attempt == len(self.api_keys) - 1:
                        # Todas las keys fallaron con este modelo, intentar con el siguiente, se nota la pobreza kajdskajkd
                        break
                    continue
            

            if try_model == models_to_try[-1]:
                break
            else:
                print(f"   Intentando con siguiente modelo...")
        
        return {'error': 'Todos los modelos de gemini fallaron. Intenta luego.'}
    
    def get_available_models(self):
        return self.models
# tremenda logica duplicada acá pero ya fue, despues refactorizo si hace falta