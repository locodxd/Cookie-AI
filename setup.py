#!/usr/bin/env python3
"""
CookieAI Ez-Configurator
Configurador interactivo para CookieAI
"""

import os
import sys
import subprocess
import platform

# ASCII Art
COOKIE_ASCII = r"""
   ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗███████╗ █████╗ ██╗
  ██╔════╝██╔═══██╗██╔═══██╗██║ ██╔╝██║██╔════╝██╔══██╗██║
  ██║     ██║   ██║██║   ██║█████╔╝ ██║█████╗  ███████║██║
  ██║     ██║   ██║██║   ██║██╔═██╗ ██║██╔══╝  ██╔══██║██║
  ╚██████╗╚██████╔╝╚██████╔╝██║  ██╗██║███████╗██║  ██║██║
   ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝
"""

SUBTITLE = "                    Ez-Configurator"

def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_header():
    clear_screen()
    print("\033[94m" + COOKIE_ASCII + "\033[0m")  # azul
    print("\033[90m" + SUBTITLE + "\033[0m\n")  # gris

def ask_question(question, default=None, required=True):
    if default:
        prompt = f"{question} [{default}]: "
    else:
        prompt = f"{question}: "
    
    while True:
        answer = input(prompt).strip()
        if not answer and default:
            return default
        if answer or not required:
            return answer
        print(" This field is required!")

def ask_yes_no(question, default=True):
    default_str = "Y/n" if default else "y/N"
    answer = input(f"{question} [{default_str}]: ").strip().lower()
    
    if not answer:
        return default
    return answer in ['y', 'yes', 'si', 's']

def ask_number(question, min_val=None, max_val=None, default=None):
    while True:
        answer = ask_question(question, default=str(default) if default else None, required=False)
        if not answer and default is not None:
            return default
        try:
            num = int(answer)
            if min_val is not None and num < min_val:
                print(f"  Minimum value is {min_val}")
                continue
            if max_val is not None and num > max_val:
                print(f"  Maximum value is {max_val}")
                continue
            return num
        except ValueError:
            print("  Please enter a valid number")

def configure_gemini():
    print("\n🔑 GEMINI API KEYS")
    print("━" * 50)
    print("Get your keys at: https://aistudio.google.com/apikey\n")
    
    keys = []
    key_num = 1
    
    while True:
        key = ask_question(f"Gemini API Key #{key_num}", required=(key_num == 1))
        if not key:
            break
        keys.append(key)
        key_num += 1
        
        if not ask_yes_no("Add another Gemini key?", default=False):
            break
    
    return keys

def configure_models(gemini_keys):
    print("\n🤖 AI MODELS CONFIGURATION")
    print("━" * 50)
    print("⚠️  IMPORTANT: Enter the FULL Gemini model name exactly as the API expects it\n")
    
    gemini_models = []
    # Gemini models
    if gemini_keys:
        print("🔵 Gemini Models")
        print("Examples: gemini-2.5-flash-preview-09-2025, gemini-2.5-flash")
        models_input = ask_question(
            "Enter Gemini model names (comma-separated)", 
            default="gemini-2.5-flash",
            required=True
        )
        gemini_models = [m.strip() for m in models_input.split(',') if m.strip()]
        print(f"✅ {len(gemini_models)} Gemini model(s) configured")
    
    return gemini_models

def configurar_rate_limites_porfavoryonotendriaqueestarhaciendoesto():
    print("\n⏱  RATE LIMITING")
    print("━" * 50)
    print("Configure how many messages users can send\n")
    
    max_messages = ask_number("Maximum messages per time window", min_val=1, default=5)
    time_window = ask_number("Time window in seconds", min_val=1, default=10)
    
    return max_messages, time_window

def configure_server():
    print("\n SERVER CONFIGURATION")
    print("━" * 50)
    
    backend_port = ask_number("Backend port", min_val=1, max_val=65535, default=5000)
    frontend_port = ask_number("Frontend port", min_val=1, max_val=65535, default=8000)
    
    return backend_port, frontend_port

def configure_custom_prompt():
    print("\n CUSTOM SYSTEM PROMPT")
    print("━" * 50)
    print("By default, CookieAI uses the Flavortown assistant prompt.")
    print("You can customize it with your own personality/instructions.\n")
    
    if not ask_yes_no("Do you want to create a custom prompt?", default=False):
        return None
    
    print("\nEnter your custom system prompt (press Enter twice to finish):")
    print("Tip: Define the AI's personality, knowledge, and behavior\n")
    
    lines = []
    empty_count = 0
    
    while empty_count < 2:
        line = input()
        if not line.strip():
            empty_count += 1
        else:
            empty_count = 0
            lines.append(line)
    
    custom_prompt = '\n'.join(lines).strip()
    
    if custom_prompt:
        with open("cookie-prompt.txt", "w", encoding="utf-8") as f:
            f.write(custom_prompt)
        print("\n Custom prompt saved to cookie-prompt.txt")
        return custom_prompt
    
    return None

def mostrar_la_vps_guide():
    print("\n VPS DEPLOYMENT GUIDE")
    print("━" * 50)
    
    if not ask_yes_no("Do you want a VPS deployment guide?", default=False):
        return
    
    guide_content = """# 🚀 CookieAI VPS Deployment Guide

Complete guide to deploy CookieAI on a VPS (Ubuntu/Debian)

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS
- Root or sudo access
- Domain name (optional, for HTTPS)

---

## Step 1: Initial Server Setup

### 1.1 Connect to your VPS

```bash
ssh root@your_server_ip
```

### 1.2 Update system

```bash
apt update && apt upgrade -y
```

### 1.3 Create a user for the app

```bash
adduser cookieai
usermod -aG sudo cookieai
su - cookieai
```

---

## Step 2: Install Dependencies

### 2.1 Install Python 

```bash
sudo apt install python3 python3-pip python3-venv -y
```

### 2.2 Install Git

```bash
sudo apt install git -y
```

---

## Step 3: Clone and Setup CookieAI

### 3.1 Clone repository

```bash
cd ~
git clone https://github.com/locodxd/Cookie-AI.git
cd Cookie-AI
```

### 3.2 Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 Install dependencies

```bash
pip install -r requirements.txt
```

### 3.4 Run configurator

```bash
python setup.py
```

Follow the prompts to configure your API keys and settings.

---

## Step 4: Configure Firewall

### 4.1 Install UFW (if not installed)

```bash
sudo apt install ufw -y
```

### 4.2 Configure firewall rules

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 5000/tcp    # Backend (or your custom port)
sudo ufw allow 8000/tcp    # Frontend (or your custom port)
sudo ufw enable
```

---

## Step 5: Create Systemd Services

### 5.1 Create backend service

```bash
sudo nano /etc/systemd/system/cookieai-backend.service
```

Paste this content:

```ini
[Unit]
Description=CookieAI Backend
After=network.target

[Service]
Type=simple
User=cookieai
WorkingDirectory=/home/cookieai/Cookie-AI
Environment="PATH=/home/cookieai/Cookie-AI/venv/bin"
ExecStart=/home/cookieai/Cookie-AI/venv/bin/python backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Create frontend service

```bash
sudo nano /etc/systemd/system/cookieai-frontend.service
```

Paste this content:

```ini
[Unit]
Description=CookieAI Frontend
After=network.target

[Service]
Type=simple
User=cookieai
WorkingDirectory=/home/cookieai/Cookie-AI/frontend
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 -m http.server 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.3 Enable and start services

```bash
sudo systemctl daemon-reload
sudo systemctl enable cookieai-backend
sudo systemctl enable cookieai-frontend
sudo systemctl start cookieai-backend
sudo systemctl start cookieai-frontend
```

### 5.4 Check status

```bash
sudo systemctl status cookieai-backend
sudo systemctl status cookieai-frontend
```

---

## Step 6: Install Nginx (Recommended)

### 6.1 Install Nginx

```bash
sudo apt install nginx -y
```

### 6.2 Create Nginx configuration

```bash
sudo nano /etc/nginx/sites-available/cookieai
```


### 6.3 Enable site

```bash
sudo ln -s /etc/nginx/sites-available/cookieai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 7: Setup SSL with Let's Encrypt (Optional but Recommended)

### 7.1 Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 7.2 Get SSL certificate

```bash
sudo certbot --nginx -d your_domain.com
```

Follow the prompts. Certbot will automatically configure HTTPS.

### 7.3 Test auto-renewal

```bash
sudo certbot renew --dry-run
```

---

## Step 8: Update frontend API URL

If using a domain, update the frontend to use your domain:

```bash
cd ~/Cookie-AI/frontend
nano script.js
```

Change:
```javascript
const API_URL = 'http://localhost:5000/api';
```

To:
```javascript
const API_URL = 'https://your_domain.com/api';
```

Restart services:
```bash
sudo systemctl restart cookieai-backend
sudo systemctl restart cookieai-frontend
```

---

## Maintenance Commands

### View logs

```bash
# Backend logs
sudo journalctl -u cookieai-backend -f

# Frontend logs
sudo journalctl -u cookieai-frontend -f
```

### Restart services

```bash
sudo systemctl restart cookieai-backend
sudo systemctl restart cookieai-frontend
```

### Update CookieAI

```bash
cd ~/Cookie-AI
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart cookieai-backend
sudo systemctl restart cookieai-frontend
```

### Monitor system resources

```bash
htop
```

---

Made with 🍪 by a teen with onda ya me dio pereza escribir todo el resto 
"""
    
    with open("VPS_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("\n✅ VPS deployment guide created: VPS_GUIDE.md")
    print("   Open this file to follow the step-by-step instructions")

def generate_env_file(config):
    """genera el archivo .env"""
    env_content = "# CookieAI Configuration\n"
    env_content += "# Generated by Ez-Configurator\n\n"
    
    if config['gemini_keys']:
        env_content += "# === GEMINI API KEYS ===\n"
        for i, key in enumerate(config['gemini_keys'], 1):
            env_content += f"GEMINI_API_KEY_{i}={key}\n"
        env_content += "\n"
    
    
    env_content += "# RATE LIMITING \n"
    env_content += f"MAX_MESSAGES={config['max_messages']}\n"
    env_content += f"RATE_LIMIT_SECONDS={config['time_window']}\n\n"
    
    env_content += "# SERVER CONFIG \n"
    env_content += f"BACKEND_PORT={config['backend_port']}\n"
    env_content += f"FRONTEND_PORT={config['frontend_port']}\n\n"
    
    env_content += "#  MODELS \n"
    if config.get('gemini_models'):
        env_content += f"GEMINI_MODELS={','.join(config['gemini_models'])}\n"

    env_content += "\n"
    
    env_content += "# System prompt (leave empty to use default Flavortown prompt)\n"
    if config.get('custom_prompt'):
        env_content += "# Your custom prompt is in cookie-prompt.txt\n"
        env_content += "# The backend will automatically load it if the file exists\n"
    env_content += "SYSTEM_PROMPT=\n"
    
    return env_content

def instalar_dependencias():
    print("\n INSTALLING DEPENDENCIES")
    print("━" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print(" Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install dependencies")
        return False

def crear_scripts_de_inicio_xd(config):
    backend_port = config['backend_port']
    frontend_port = config['frontend_port']
    
    # Script para Windows
    bat_content = f"""@echo off
echo Starting CookieAI...
echo.
echo Backend: http://localhost:{backend_port}
echo Frontend: http://localhost:{frontend_port}
echo.
echo Press Ctrl+C to stop
echo.

start "CookieAI Backend" cmd /k "cd backend && python app.py"
timeout /t 3 /nobreak > nul
start "CookieAI Frontend" cmd /k "cd frontend && python -m http.server {frontend_port}"

echo.
echo ✅ CookieAI is running!
echo Open http://localhost:{frontend_port} in your browser
echo.
pause
"""
    
    # Script para Linux/Mac
    sh_content = f"""#!/bin/bash
echo "Starting CookieAI..."
echo ""
echo "Backend: http://localhost:{backend_port}"
echo "Frontend: http://localhost:{frontend_port}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Iniciar backend en background
cd backend && python3 app.py &
BACKEND_PID=$!

# Esperar a que el backend arranque
sleep 3

# Iniciar frontend
cd ../frontend && python3 -m http.server {frontend_port} &
FRONTEND_PID=$!

echo ""
echo "✅ CookieAI is running!"
echo "Open http://localhost:{frontend_port} in your browser"
echo ""

# Esperar y limpiar al salir
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
"""
    
    with open("start.bat", "w") as f:
        f.write(bat_content)
    
    with open("start.sh", "w") as f:
        f.write(sh_content)
    
    # Hacer ejecutable en Linux/Mac QUE PROBABLEMENTE NADIE USE PERO BUENO
    if platform.system() != 'Windows':
        os.chmod("start.sh", 0o755)
    
    print("✅ Start scripts created!")
    print(f"   - Windows: start.bat")
    print(f"   - Linux/Mac: ./start.sh")

def update_frontend_config(config):
    """actualiza la configuración del frontend con el puerto del backend"""
    backend_port = config['backend_port']
    
    script_path = os.path.join("frontend", "script.js")
    if not os.path.exists(script_path):
        print("⚠️  Warning: frontend/script.js not found")
        return
    
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Porfavor hermano, al final nadie va a usar el setup probablemente, ya no quiero hacer esto
    content = content.replace(
        "const API_URL = 'http://localhost:5000/api';",
        f"const API_URL = 'http://localhost:{backend_port}/api';"
    )
    
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Frontend configured to use backend on port {backend_port}")

def main():
    print_header()
    print("Welcome! Let's configure your CookieAI instance.\n")
    print("━" * 50)
    
    print("\n AI PROVIDERS SELECTION")
    print("━" * 50)
    print("CookieAI will be configured to use Gemini as the sole provider.\n")
    
    use_gemini = ask_yes_no("Configure Gemini (Google)?", default=True)
    if not use_gemini:
        print("\n You need to use Gemini as the provider. Exiting.")
        sys.exit(1)

    config = {}
    
    config['gemini_keys'] = configure_gemini() if use_gemini else []
    
    if not config['gemini_keys']:
        print("\n❌ You need to configure at least one Gemini API key!")
        sys.exit(1)
    
    config['gemini_models'] = configure_models(config['gemini_keys'])

    config['max_messages'], config['time_window'] = configurar_rate_limites_porfavoryonotendriaqueestarhaciendoesto()

    config['backend_port'], config['frontend_port'] = configure_server()
    

    config['custom_prompt'] = configure_custom_prompt()
    
    # Resumen
    print("\n📋 CONFIGURATION SUMMARY")
    print("━" * 50)
    print(f"Gemini keys: {len(config['gemini_keys'])}")
    if config['gemini_models']:
        print(f"  Models: {', '.join(config['gemini_models'])}")
    print(f"Rate limit: {config['max_messages']} messages per {config['time_window']}s")
    print(f"Backend port: {config['backend_port']}")
    print(f"Frontend port: {config['frontend_port']}")
    print("")
    
    if not ask_yes_no("Save this configuration?", default=True):
        print("\n❌ Configuration cancelled")
        sys.exit(0)
    
    # Generar .env
    print("\n💾 SAVING CONFIGURATION")
    print("━" * 50)
    env_content = generate_env_file(config)
    with open(".env", "w") as f:
        f.write(env_content)
    print(" .env file created!")
    
    update_frontend_config(config)

    if ask_yes_no("\nInstall Python dependencies now?", default=True):
        instalar_dependencias()
    
    crear_scripts_de_inicio_xd(config)
    mostrar_la_vps_guide()
    print("\n" + "━" * 50)
    print("✅ SETUP COMPLETE!")
    print("━" * 50)
    print("\nTo start CookieAI:")
    if platform.system() == 'Windows':
        print("  Run: start.bat")
    else:
        print("  Run: ./start.sh")
    
    print(f"\nThen open: http://localhost:{config['frontend_port']}")
    print("\n🍪 Happy hacking!")
    
    if ask_yes_no("\nStart CookieAI now?", default=True):
        print("\nStarting CookieAI...")
        if platform.system() == 'Windows':
            subprocess.Popen(["start.bat"], shell=True)
        else:
            subprocess.Popen(["./start.sh"], shell=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n Error: {e}")
        sys.exit(1)
