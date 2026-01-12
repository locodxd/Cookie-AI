# 🍪 CookieAI

una IA copada para chatear, con varios modelos y providers. 

## que tiene esto

- **frontend minimalista**: Re fachero
- **backend seguro**: rate limiting, fallback de API keys, protecciones basicas
- **multi-provider**: soporta gemini, openai y claude
- **memoria conversacional**: se acuerda de lo que hablaste
- **sin login**: directo al chat, sin boludeces
- **ez-configurator**: setup interactivo super facil
- **custom prompt**: pone tu propio prompt en cookie-prompt.txt
- **vps ready**: guía completa de deployment incluida

## como instalar

### opción 1: ez-configurator (recomendado)

la forma más fácil - el configurador te guía paso a paso:

```bash
git clone https://github.com/locodxd/Cookie-AI.git
cd Cookie-AI
python setup.py
```

el configurador te va a preguntar:
- tus API keys (gemini, openai, claude)
- rate limiting
- puertos del servidor
- y te instala todo automáticamente


### opción 2: manual

si preferis configurar a mano:

#### 1. clona el repo

#### 1. clona el repo

```bash
git clone https://github.com/locodxd/Cookie-AI.git
cd Cookie-AI
```

#### 2. instala las dependencias

#### 2. instala las dependencias

```bash
pip install -r requirements.txt
```

#### 3. configura tus API keys

copia el archivo `.env.example` y renombralo a `.env`:

```bash
cp .env.example .env
```

despues edita el archivo `.env` y pone tus keys:

```env
# pone tus keys acá (pone todas las que tengas para el fallback)
GEMINI_API_KEY_1 2 3 4 hasta el infinito 


# si tenes de openai tambien
OPENAI_API_KEY_1=

# y si tenes de claude
CLAUDE_API_KEY_1=
```


### 4. configura los modelos (opcional)

en el `.env` tambien podes cambiar que modelos aparecen:

```env
GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-flash-lite
OPENAI_MODELS=gpt-4o-mini
CLAUDE_MODELS=claude-3-5-haiku-20241022
```

### 5. ajusta el rate limiting (opcional)

```env
MAX_MESSAGES=5          # cuantos mensajes puede mandar
RATE_LIMIT_SECONDS=10   # cada cuantos segundos se resetea
```

### 6. personaliza el prompt (opcional)

**opción 1: con el configurador**

cuando corres `python setup.py`, te pregunta si queres crear un prompt custom. Si decis que sí, crea `cookie-prompt.txt` donde podes escribir tu prompt.

**opción 2: manual**

crea un archivo `cookie-prompt.txt` en la raíz del proyecto con tu prompt:

```txt
Sos una IA experta en Python que ayuda a hacer readmes, porque realmente da paja hacer eso
```

el backend lo va a cargar automáticamente. si no existe, usa el prompt de Flavortown por default.

**opción 3: via .env**

también podes setear el prompt directo en el `.env`:

```env
SYSTEM_PROMPT=Tu prompt custom aca...
```

prioridad: `.env` > `cookie-prompt.txt` > `flavortown_prompt.txt` (default)

## deployment en VPS

si queres hostear CookieAI en un servidor, el configurador puede crear una guía completa:

```bash
python setup.py
```

cuando te pregunte "Do you want a VPS deployment guide?", decí que sí. esto crea `VPS_GUIDE.md` con:

- instalación en Ubuntu/Debian
- configuración de systemd services
- setup de Nginx reverse proxy
- SSL con Let's Encrypt
- comandos de mantenimiento
- troubleshooting

también podes [ver la guía directamente acá](VPS_GUIDE.md) si ya la generaste.
en caso de cagarla no es mi culpa 
## como ejecutar

### backend

```bash
cd backend
python app.py
```

el servidor va a correr en `http://localhost:5000`

### frontend

simplemente abre el archivo `frontend/index.html` en tu navegador, o si queres usar un server local:

```bash
cd frontend
python -m http.server 8000
```

y entra a `http://localhost:8000`

## estructura del proyecto

```
Cookie-AI/
backend/
app.py              # servidor flask principal
ai_providers.py     # providers de IA (gemini, openai, claude)
frontend/
index.html          # estructura
style.css           # estilos OLED 
script.js           # logica del chat
.env.example            # template para las keys
.gitignore              # para no filtrar nada
requirements.txt        # dependencias python
README.md              # esta cosa que estás leyendo
```

## features

### seguridad

- rate limiting por IP (configurable)
- validacion de inputs
- CORS configurado
- sanitizacion de mensajes
- fallback de API keys (si una falla, usa otra)

### memoria conversacional

la IA se acuerda de la conversacion. usa un `session_id` que se genera automaticamente en el frontend. cada sesion tiene su propio historial.

### multi-provider

podes elegir entre
open AI
gemini
y Anthropic
aunque los modelos que más recomiendo son gemini 2.5 flash lite/flash nomas, gpt 5 nano, 4.1 mini y claude haiku 4.5 si queres algo más fachero
para programar

si una key falla, automaticamente prueba con la siguiente.

## troubleshooting

### "no se pudo conectar al servidor"

- fijate que el backend este corriendo en el puerto 5000
- verifica que no haya ningun firewall bloqueando

### "todas las keys fallaron"

- verifica que las keys en `.env` esten bien escritas
- fijate que tengas credito en las cuentas
- revisa que los nombres de los modelos sean correctos

### "rate limit excedido"

- espera los segundos que te dice
- o cambia los valores en `.env` si es para vos solo

## contribuir

si queres agregar algo o mejorar esto, manda un PR nomas. todo suma.

## licencia

Unlicensed - hace lo que se te cante
## disclaimer

este proyecto es para uso personal/educativo. no me hago responsable si te quedas sin credito de API por spam o lo que sea. usa con cabeza.
este proyecto en especifico es totalmente a parte de flavortown o sea que no es oficial, recuerda que la IA puede alucinar o cosas asi

