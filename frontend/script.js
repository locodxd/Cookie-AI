const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000/api' 
    : '/api';

// placeholders aleatorios
const PLACEHOLDERS = [
    "How do I get cookies?",
    "What's a good Flavortown project?",
    "How does Hackatime work?",
    "Can I work on old projects?",
    "What are the age requirements?",
    "How do I track my time?",
    "What's the voting system?",
    "Can I use AI for my project?",
    "How do I ship my project?",
    "What prizes are available?",
    "Can I contribute to open source?",
    "How long does Flavortown run?",
    "What's double-dipping?",
    "How do devlogs work?",
    "Can I make hardware projects?",
    "Why does my project show as Unknown?",
    "How do Shipwrights review projects?",
    "What counts as a shippable project?",
    "Can I update an old project for Flavortown?",
    "How do peer ratings work?",
    "What's the cookie multiplier?",
    "Do I need to make devlogs?",
    "Can I ship a PCB design?",
    "What editors support Hackatime?",
    "How do I join Hack Club Slack?",
    "What happens with customs fees?",
    "Can I suggest new prizes?",
    "What's the difference between flash models?",
    "How many votes does each project get?",
    "Can I work on multiple projects?"
];

// funcion loca para escribir texto como hacker
async function typeWriterEffect(element, texts) {
    while (true) { 
        const text = texts[Math.floor(Math.random() * texts.length)];
        
        for (let i = 0; i <= text.length; i++) {
            element.placeholder = text.substring(0, i);
            await new Promise(r => setTimeout(r, 50 + Math.random() * 50)); 
        }
        await new Promise(r => setTimeout(r, 2000));
        
        for (let i = text.length; i >= 0; i--) {
            element.placeholder = text.substring(0, i);
            await new Promise(r => setTimeout(r, 30));
        }
        await new Promise(r => setTimeout(r, 500));
    }
}


function generateId() {
    return 'chat_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

// funcion para parsear un markdown basico ;3
function parseMarkdown(text) {
    let clean = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;") 
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    clean = clean.replace(/\*(.*?)\*/g, '<i>$1</i>');
    clean = clean.replace(/`(.*?)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 4px; font-family: monospace;">$1</code>');
    clean = clean.replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>');
    clean = clean.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #0084ff; text-decoration: underline;">$1</a>');
    clean = clean.replace(/\n/g, '<br>');

    return clean;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// este el init del script

let chats = JSON.parse(localStorage.getItem('cookieai_chats')) || [];
let currentChatId = localStorage.getItem('cookieai_current_chat');
let currentProvider = 'gemini';
let currentModel = null;
let availableModels = {};
let isLoading = false;
let selectedImageBase64 = null; // esto añade soporte al adjuntar imagenes, esto 
// está siendo testeado con Gemini Vision por ahora

// crear chat inicial si no hay ninguno
if (chats.length === 0) {
    const newChat = {
        id: generateId(),
        title: 'New chat',
        messages: [],
        createdAt: Date.now()
    };
    chats.unshift(newChat);
    currentChatId = newChat.id;
    localStorage.setItem('cookieai_chats', JSON.stringify(chats));
    localStorage.setItem('cookieai_current_chat', currentChatId);
}

const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const providerSelect = document.getElementById('provider-select');
const modelSelect = document.getElementById('model-select');
const clearBtn = document.getElementById('clear-btn');
const rateLimitInfo = document.getElementById('rate-limit-info');
const sidebar = document.getElementById('sidebar');
const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const chatsList = document.getElementById('chats-list');
const imageInput = document.getElementById('image-input');
const attachBtn = document.getElementById('attach-btn');
const imagePreview = document.getElementById('image-preview');
const imagePreviewContainer = document.getElementById('image-preview-container');
const removeImageBtn = document.getElementById('remove-image');
// nunca mas voy a escribir const luego de esto
document.addEventListener('DOMContentLoaded', () => {
    loadModels();
    setupEventListeners();
    renderChatsList();
    loadCurrentChat();
    autoResizeTextarea();
    
    typeWriterEffect(messageInput, PLACEHOLDERS);
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    providerSelect.addEventListener('change', (e) => {
        currentProvider = e.target.value;
        updateModelSelect();
    });
    
    modelSelect.addEventListener('change', (e) => {
        currentModel = e.target.value;
    });

    // si el loco clickea el selector y no hay modelos, intentamos cargar de nuevo
    modelSelect.addEventListener('click', () => {
        if (!availableModels[currentProvider] || availableModels[currentProvider].length === 0) {
            console.log("no hay modelos, cargando al clickear...");
            loadModels(2);
        }
    });
    
    clearBtn.addEventListener('click', clearChat);
    toggleSidebarBtn.addEventListener('click', toggleSidebar);
    newChatBtn.addEventListener('click', createNewChat);
    
    messageInput.addEventListener('input', autoResizeTextarea);
    
    attachBtn.addEventListener('click', () => imageInput.click());
    
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            processImageFile(file);
        }
    });
    
    removeImageBtn.addEventListener('click', () => {
        selectedImageBase64 = null;
        imagePreviewContainer.style.display = 'none';
        imageInput.value = '';
    });
    
    // evento para pegar imágenes con Ctrl+V
    document.addEventListener('paste', (e) => {
        const items = e.clipboardData?.items;
        if (!items) return;
        
        for (let item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (!file) continue;
                
                processImageFile(file);
                break; // solo procesar la primera imagen
            }
        }
    });
}

// Función para procesar y comprimir imágenes
async function processImageFile(file) {
    // validar que sea imagen
    if (!file.type.startsWith('image/')) {
        alert('eso no es una imagen pa');
        return;
    }
    
    // checar que no sea muy pesada (máximo inicial 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('imagen muy pesada (max 10MB)');
        return;
    }
    
    try {
        const img = new Image();
        const reader = new FileReader();
        
        reader.onload = (e) => {
            img.src = e.target.result;
        };
        
        img.onload = () => {
            // Redimensionar si es muy grande
            let width = img.width;
            let height = img.height;
            const maxDimension = 1920; // máximo 1920px en cualquier lado
            
            if (width > maxDimension || height > maxDimension) {
                const ratio = Math.min(maxDimension / width, maxDimension / height);
                width = Math.floor(width * ratio);
                height = Math.floor(height * ratio);
                console.log(`🔽 Redimensionando imagen de ${img.width}x${img.height} a ${width}x${height}`);
            }
            
            // Crear canvas para comprimir
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);
            
            // Convertir a base64 con compresión
            canvas.toBlob((blob) => {
                if (!blob) {
                    alert('error procesando imagen');
                    return;
                }
                
                // Verificar tamaño después de comprimir
                const compressedSizeKB = blob.size / 1024;
                console.log(`📦 Imagen comprimida: ${compressedSizeKB.toFixed(0)}KB`);
                
                if (blob.size > 5 * 1024 * 1024) {
                    alert('imagen muy pesada incluso después de comprimir (max 5MB)');
                    return;
                }
                
                // Convertir blob a base64
                const blobReader = new FileReader();
                blobReader.onload = (event) => {
                    const base64String = event.target.result;
                    const base64Data = base64String.split(',')[1];
                    
                    if (!base64Data || base64Data.length < 100) {
                        alert('imagen vacía o corrupta');
                        return;
                    }
                    
                    selectedImageBase64 = base64Data;
                    imagePreview.src = base64String;
                    imagePreviewContainer.style.display = 'block';
                    console.log('✅ Imagen lista para enviar');
                };
                blobReader.readAsDataURL(blob);
            }, 'image/jpeg', 0.85); // JPEG con calidad 85%
        };
        
        img.onerror = () => {
            alert('error cargando la imagen');
        };
        
        reader.readAsDataURL(file);
    } catch (err) {
        console.error('error procesando imagen:', err);
        alert('no se pudo procesar la imagen');
    }
}



function createNewChat() {
    const newChat = {
        id: generateId(),
        title: 'New chat',
        messages: [],
        createdAt: Date.now()
    };
    
    chats.unshift(newChat);
    currentChatId = newChat.id;
    saveChats();
    renderChatsList();
    loadCurrentChat();
}

function switchChat(chatId) {
    currentChatId = chatId;
    localStorage.setItem('cookieai_current_chat', chatId);
    renderChatsList();
    loadCurrentChat();
}

function getCurrentChat() {
    return chats.find(c => c.id === currentChatId) || chats[0];
}

function saveChats() {
    localStorage.setItem('cookieai_chats', JSON.stringify(chats));
    localStorage.setItem('cookieai_current_chat', currentChatId);
}

function renderChatsList() {
    chatsList.innerHTML = '';
    
    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item';
        if (chat.id === currentChatId) {
            chatItem.classList.add('active');
        }
        
        const titleSpan = document.createElement('span');
        titleSpan.className = 'chat-item-title';
        titleSpan.textContent = chat.title;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'chat-item-delete';
        deleteBtn.textContent = '×';
        deleteBtn.title = 'delete chat';
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteChat(chat.id);
        });
        
        chatItem.appendChild(titleSpan);
        chatItem.appendChild(deleteBtn);
        chatItem.addEventListener('click', () => switchChat(chat.id));
        
        chatsList.appendChild(chatItem);
    });
}

function deleteChat(chatId) {
    if (chats.length === 1) {
        alert('Cannot delete the last chat');
        return;
    }
    
    const index = chats.findIndex(c => c.id === chatId);
    if (index === -1) return;
    
    chats.splice(index, 1);
    
    if (chatId === currentChatId) {
        currentChatId = chats[0].id;
    }
    
    saveChats();
    renderChatsList();
    loadCurrentChat();
}

function loadCurrentChat() {
    const chat = getCurrentChat();
    if (!chat) return;
    
    chatContainer.innerHTML = '';
    
    if (chat.messages.length === 0) {
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🍪</div>
                <h2>Hey! I'm CookieAI</h2>
                <p>what can I help you with?</p>
            </div>
        `;
    } else {
        chat.messages.forEach(msg => {
            if (msg.role === 'user') {
                addMessageToDOM('user', msg.content, null, msg.image);
            } else {
                addMessageToDOM('assistant', msg.content, msg.model);
            }
        });
    }
    
    scrollToBottom();
}

function updateChatTitle(firstMessage) {
    const chat = getCurrentChat();
    if (chat.messages.length === 1) {
        chat.title = firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '');
        saveChats();
        renderChatsList();
    }
}

function toggleSidebar() {
    sidebar.classList.toggle('hidden');
}

// Estas son las funciones principales del chat

async function loadModels(retries = 5, delay = 1000) {
    try {
        console.log(`intentando cargar modelos... (intento ${6-retries})`);
        if (retries === 5) {
            modelSelect.innerHTML = '<option value="">Loading models...</option>';
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const response = await fetch(`${API_URL}/models`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        if (!data || Object.keys(data).length === 0) {
            throw new Error("El server no devolvio modelos");
        }
        
        availableModels = data;
        updateModelSelect();
        console.log(" modelos cargados piola");
    } catch (error) {
        console.error('error cargando modelos:', error);
        
        if (retries > 0) {
            console.log(`Reintentando en ${delay}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay)); 
            return loadModels(retries - 1, delay * 1.5); // backoff exponencial
        }
        
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
        addSystemMessage('Could not load models. Please refresh the page manually.');
    }
}
// algunos modelos de IA tienen nombres larguisimos, aca los acortamos, igual no sé si esto funcionara si es que pone otro modelo
function getShortModelName(modelName) {
    const shortcuts = {
        'gemini-2.5-flash-lite-preview-09-2025': 'flash-lite-preview',
        'gemini-2.5-flash-preview-09-2025': 'flash-preview',
        'gemini-2.5-flash': 'flash',
        'gemini-2.5-flash-lite': 'flash-lite',
        'gpt-4o': 'gpt-4o',
        'gpt-4o-mini': 'gpt-4o-mini',
        'gpt-3.5-turbo': 'gpt-3.5',
        'claude-3-5-sonnet-20241022': 'sonnet-3.5',
        'claude-3-5-haiku-20241022': 'haiku-3.5',
        'claude-3-opus-20240229': 'opus-3'
    };
    
    return shortcuts[modelName] || modelName;
}

function updateModelSelect() {
    modelSelect.innerHTML = '';
    
    const models = availableModels[currentProvider] || [];
    
    if (models.length === 0) {
        modelSelect.innerHTML = '<option value="">No models</option>';
        return;
    }
    
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = getShortModelName(model);
        modelSelect.appendChild(option);
    });
    
    // Orden de preferencia para seleccionar modelo por defecto
    const modelPreferences = [
        'gemini-2.5-flash',                    // Primera opción: gemini-2.5-flash (mejor)
        'gemini-2.5-flash-preview-09-2025',    // Segunda: preview full
        'gemini-2.5-flash-lite',               // Tercera: lite
        'gemini-2.5-flash-lite-preview-09-2025', // Cuarta: preview lite
    ];
    
    let selectedModel = null;
    
    // Buscar el primer modelo que coincida exactamente con nuestras preferencias
    for (const preference of modelPreferences) {
        // Primero intenta match exacto
        let found = models.find(m => m === preference || m.trim() === preference.trim());
        if (found) {
            selectedModel = found;
            console.log(`✅ Modelo seleccionado (exacto): ${getShortModelName(selectedModel)}`);
            break;
        }
    }
    
    // Si no encuentra match exacto, busca por substring (pero ordenado correctamente)
    if (!selectedModel) {
        for (const preference of modelPreferences) {
            let found = models.find(m => m.includes(preference));
            if (found) {
                selectedModel = found;
                console.log(`✅ Modelo seleccionado (parcial): ${getShortModelName(selectedModel)}`);
                break;
            }
        }
    }
    
    // Si no encuentra ninguno preferido, usa el primero disponible
    if (!selectedModel) {
        selectedModel = models[0];
        console.log(`⚠️  Usando modelo disponible: ${getShortModelName(selectedModel)}`);
    }
    
    currentModel = selectedModel;
    modelSelect.value = currentModel;
}
async function sendMessage() {
    if (isLoading) return;
    const message = messageInput.value.trim();
    if (!message && !selectedImageBase64) return;
    
    const chat = getCurrentChat();
    const imageToSend = selectedImageBase64;
    const imageUrlToDisplay = selectedImageBase64 ? `data:image/jpeg;base64,${selectedImageBase64}` : null;
    
    messageInput.value = '';
    autoResizeTextarea();
    
    // limpiar imagen despues de un poquito para que no se bugee
    setTimeout(() => {
        selectedImageBase64 = null;
        imagePreviewContainer.style.display = 'none';
        imageInput.value = '';
    }, 100);
    
    const welcomeMsg = chatContainer.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();
    
    addMessageToDOM('user', message, null, imageUrlToDisplay);
    chat.messages.push({ 
        role: 'user', 
        content: message,
        image: imageUrlToDisplay 
    });
    
    updateChatTitle(message || 'Image');
    isLoading = true;
    sendBtn.disabled = true;
    const loadingId = addLoadingMessage();
    
    try {
        // debug: ver si la imagen se está mandando
        if (imageToSend) {
            console.log('📸 Enviando imagen:', imageToSend.length, 'chars de base64');
        }
        
        const requestBody = {
            message: message,
            image: imageToSend || null, // base64 puro pal server
            provider: currentProvider,
            model: currentModel,
            session_id: chat.id
        };
        
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        const data = await response.json();
        removeLoadingMessage(loadingId);
        
        if (response.status === 429) {
            showRateLimitWarning(data.wait_time);
            addSystemMessage(`Hold on, wait ${data.wait_time}s`);
        } else if (data.error) {
            addSystemMessage(`Error: ${data.error}`);
        } else {
            addMessageToDOM('assistant', data.message, data.model);
            chat.messages.push({ 
                role: 'assistant', 
                content: data.message,
                model: data.model
            });
            saveChats();
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        console.error('Error al conectar:', error);
        
        // mensaje más descriptivo según el error
        if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            addSystemMessage('❌ No se pudo conectar al servidor. Verifica que el backend esté corriendo.');
        } else if (error.message.includes('NetworkError')) {
            addSystemMessage('❌ Error de red. Verifica tu conexión a internet.');
        } else {
            addSystemMessage(`❌ Error: ${error.message || 'No se pudo enviar el mensaje'}`);
        }
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}
function addMessageToDOM(role, content, model = null, imageUrl = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const icon = role === 'user' ? '👤' : '🍪';
    const sender = role === 'user' ? 'you' : 'CookieAI';
    const modelText = model ? `<div class="message-meta">${getShortModelName(model)}</div>` : '';
    
    let contentHtml = '';
    if (imageUrl) {
        contentHtml += `<div class="message-image-wrapper"><img src="${imageUrl}" class="message-image" alt="image"></div>`;
    }
    if (content) {
        contentHtml += parseMarkdown(content);
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">${icon}</span>
            <span class="message-sender">${sender}</span>
        </div>
        <div class="message-content">
            ${contentHtml}
        </div>
        ${modelText}
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}
function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">ℹ️</span>
            <span class="message-sender">system</span>
        </div>
        <div class="message-content">${parseMarkdown(content)}</div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}
function addLoadingMessage() {
    const loadingDiv = document.createElement('div');
    const loadingId = `loading-${Date.now()}`;
    loadingDiv.id = loadingId;
    loadingDiv.className = 'message assistant';
    
    loadingDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">🍪</span>
            <span class="message-sender">CookieAI</span>
        </div>
        <div class="message-content">
            <div class="loading">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(loadingDiv);
    scrollToBottom();
    
    return loadingId;
}

function removeLoadingMessage(loadingId) {
    const loadingMsg = document.getElementById(loadingId);
    if (loadingMsg) loadingMsg.remove();
}
// por si acaso queria probar solo el boton y es bien menso 
async function clearChat() {
    if (!confirm('Are you sure you want to clear everything??')) return;
    
    const chat = getCurrentChat();
    
    try {
        await fetch(`${API_URL}/clear-history`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: chat.id })
        });
        
        chat.messages = [];
        chat.title = 'New chat';
        saveChats();
        renderChatsList();
        loadCurrentChat();
        
    } catch (error) {
        console.error(error);
        addSystemMessage('Could not clear history');
    }
}
function showRateLimitWarning(seconds) {
    rateLimitInfo.textContent = `Wait ${seconds}s`;
    rateLimitInfo.className = 'rate-limit-info rate-limit-warning';
    
    setTimeout(() => {
        rateLimitInfo.textContent = '';
        rateLimitInfo.className = 'rate-limit-info';
    }, seconds * 1000);
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// esto hace q reintente varias veces pq o si no hay que usar f5
async function checkHealth(retries = 3) {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('🍪 connected:', data.status);
    } catch (error) {
        if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            return checkHealth(retries - 1);
        }
        addSystemMessage('Server offline');
    }
}

checkHealth();