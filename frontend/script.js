// amigo este archivo fue un desastre de hacerlo, es un frankestein de codigo
// asi que perdon por el desorden

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
    "How do I redeem my cookies?",
    "Can I work on multiple projects?"

];
const PLACEHOLDERS_AFTER_FIRST = [
    "Thank you",
    "Can you explain more?",
    "That's interesting",
    "I have another question...",
    "Can you give an example?",
    "How does that work?",
    "What are the benefits?",
    "Can you elaborate?",
    "What's the next step?",
    "How can I improve?",
    "Any tips?",
    "Oh, I see",
    "Got it!",
    "Makes sense",
    "Cool, thanks!",
    "Appreciate it!",
    "That's helpful",
    "Thanks for the info!",
    "Great, thank you!",
    "Thanks for explaining!",
    "Very informative!",
    "Learned something new!",
    "Brilliant, thanks!",
    "That was quick, thanks!",
    "You're the best!"
];

let firstMessageSent = false;
const NEW_CHAT_RATE_BASE = 10;
const NEW_CHAT_RATE_WINDOW = 60 * 60; 

function _getNewChatTimestamps() {
    try {
        const raw = localStorage.getItem('cookieai_newchat_times') || '[]';
        return JSON.parse(raw).map(t => Number(t)).filter(Boolean);
    } catch (e) {
        return [];
    }
}

function _saveNewChatTimestamps(arr) {
    localStorage.setItem('cookieai_newchat_times', JSON.stringify(arr));
}

function canCreateNewChat() {
    const now = Date.now();
    const windowMs = NEW_CHAT_RATE_WINDOW * 1000;
    let times = _getNewChatTimestamps().filter(ts => now - ts < windowMs);
    const count = times.length + 1; 

    if (count <= 2) {
        return { allowed: true, wait: 0, count };
    }

    const requiredWait = NEW_CHAT_RATE_BASE * (count - 2);
    const last = times.length ? times[times.length - 1] : 0;
    const elapsed = last ? Math.floor((now - last) / 1000) : Infinity;

    if (elapsed < requiredWait) {
        return { allowed: false, wait: requiredWait - elapsed, count };
    }

    return { allowed: true, wait: 0, count };
}
function recordNewChatCreation() {
    const now = Date.now();
    const windowMs = NEW_CHAT_RATE_WINDOW * 1000;
    let times = _getNewChatTimestamps().filter(ts => now - ts < windowMs);
    times.push(now);
    _saveNewChatTimestamps(times);
}

function disableNewChatButtonFor(seconds) {
    if (!newChatBtn) return;
    const origText = newChatBtn.textContent;
    newChatBtn.disabled = true;
    let remaining = seconds;
    newChatBtn.textContent = `+ new chat (${remaining}s)`;
    const iv = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
            clearInterval(iv);
            newChatBtn.disabled = false;
            newChatBtn.textContent = origText;
        } else {
            newChatBtn.textContent = `+ new chat (${remaining}s)`;
        }
    }, 1000);
}

function getCurrentPlaceholders() {
    return firstMessageSent ? PLACEHOLDERS_AFTER_FIRST : PLACEHOLDERS;
}

async function typeWriterEffect(element, getTexts) {
    while (true) {
        const texts = getTexts();
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

function updateModeButtons() {
    if (!modeThinkingBtn || !modeInstantBtn) return;
    if (currentMode === 'instant') {
        modeInstantBtn.classList.add('mode-active');
        modeThinkingBtn.classList.remove('mode-active');
    } else {
        modeThinkingBtn.classList.add('mode-active');
        modeInstantBtn.classList.remove('mode-active');
    }
}

function getPreferredModelsForMode(mode) {
    return mode === 'instant' ? MODEL_MODES.instant : MODEL_MODES.thinking;
}

function isModelRateLimited(model) {
    if (!model) return false;
    const entry = rateLimitedModels.get(model);
    if (!entry) return false;
    if (Date.now() - entry.since > entry.cooldownMs) {
        rateLimitedModels.delete(model);
        return false;
    }
    return true;
}

function markModelRateLimited(model, seconds = 30) {
    if (!model) return;
    const cooldownMs = Math.max(1, seconds) * 1000;
    rateLimitedModels.set(model, { since: Date.now(), cooldownMs });
}

function pickModelForMode(models, mode) {
    const preferred = getPreferredModelsForMode(mode);
    for (const pref of preferred) {
        const found = models.find(m => (m === pref || m.trim() === pref.trim()) && !isModelRateLimited(m));
        if (found) return found;
    }
    for (const pref of preferred) {
        const found = models.find(m => m.includes(pref) && !isModelRateLimited(m));
        if (found) return found;
    }
    const firstOk = models.find(m => !isModelRateLimited(m));
    return firstOk || null;
}

function setMode(mode, { silent = false } = {}) {
    currentMode = mode === 'instant' ? 'instant' : 'thinking';
    updateModeButtons();
    const selected = updateModelSelect();
    if (!selected && !silent) {
        addSystemMessage('No models available for this mode.');
    }
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

let chats = JSON.parse(localStorage.getItem('cookieai_chats')) || [];
let currentChatId = localStorage.getItem('cookieai_current_chat');
let currentProvider = 'gemini';
let currentModel = null;
let currentMode = 'thinking';
let availableModels = {};
let isLoading = false;
let selectedImageBase64 = null; // esto añade soporte al adjuntar imagenes, esto 
// está siendo testeado con Gemini Vision por ahora
let selectedVideoFile = null; // esto igual está en otro lugar pero ya fue lo dejo todo hecho mr 

const MODEL_MODES = {
    thinking: [
        'gemini-2.5-flash-preview-09-2025',
        'gemini-2.5-flash'
    ],
    instant: [
        'gemini-2.5-flash-lite-preview-09-2025',
        'gemini-2.5-flash-lite'
    ]
};

const rateLimitedModels = new Map();
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
const videoInput = document.getElementById('video-input');
const attachInput = document.getElementById('attach-input');
const attachBtn = document.getElementById('attach-btn');
const imagePreview = document.getElementById('image-preview');
const imagePreviewContainer = document.getElementById('image-preview-container');
const removeImageBtn = document.getElementById('remove-image');
const modeThinkingBtn = document.getElementById('mode-thinking');
const modeInstantBtn = document.getElementById('mode-instant');
const modeToggle = document.getElementById('mode-toggle');
// nunca mas voy a escribir const luego de esto
document.addEventListener('DOMContentLoaded', () => {
    loadModels();
    setupEventListeners();
    renderChatsList();
    loadCurrentChat();
    autoResizeTextarea();
    updateModeButtons();
    
    typeWriterEffect(messageInput, getCurrentPlaceholders);
});
function setupEventListeners() {
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (messageInput) messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    if (providerSelect) providerSelect.addEventListener('change', (e) => {
        currentProvider = e.target.value;
        updateModelSelect();
    });

    if (modelSelect) {
        modelSelect.addEventListener('change', (e) => {
            currentModel = e.target.value;
        });
        modelSelect.addEventListener('click', () => {
            if (!availableModels[currentProvider] || availableModels[currentProvider].length === 0) {
                console.log("no hay modelos, cargando al clickear...");
                loadModels(2);
            }
        });
    }

    if (clearBtn) clearBtn.addEventListener('click', clearChat);
    if (toggleSidebarBtn) toggleSidebarBtn.addEventListener('click', toggleSidebar);
    if (newChatBtn) newChatBtn.addEventListener('click', createNewChat);
    if (modeThinkingBtn) modeThinkingBtn.addEventListener('click', () => setMode('thinking'));
    if (modeInstantBtn) modeInstantBtn.addEventListener('click', () => setMode('instant'));
    if (messageInput) messageInput.addEventListener('input', autoResizeTextarea);
    if (attachBtn && attachInput) attachBtn.addEventListener('click', () => attachInput.click());
    if (attachInput) attachInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        if (file.type.startsWith('video/')) {
            if (file.size > 50 * 1024 * 1024) {
                alert('🎥 Video muy pesado (máximo 50MB)');
                attachInput.value = '';
                return;
            }
            
            const video = document.createElement('video');
            video.preload = 'metadata';
            video.onloadedmetadata = () => {
                window.URL.revokeObjectURL(video.src);
                if (video.duration > 30) {
                    alert('🎥 Video muy largo (máximo 30 segundos)');
                    attachInput.value = '';
                    return;
                }
                selectedVideoFile = file;
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0);
                imagePreview.src = canvas.toDataURL();
                imagePreviewContainer.style.display = 'block';
                
                console.log(`🎥 Video listo: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB, ${Math.round(video.duration)}s)`);
            };
            video.src = URL.createObjectURL(file);
        } else if (file.type.startsWith('image/')) {
            processImageFile(file);
        } else {
            alert('Archivo no soportado (imagen o video)');
        }
        
        attachInput.value = '';
    });
    if (imageInput) imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            processImageFile(file);
        }
    });

    if (removeImageBtn) removeImageBtn.addEventListener('click', () => {
        selectedImageBase64 = null;
        selectedVideoFile = null;
        if (imagePreviewContainer) imagePreviewContainer.style.display = 'none';
        if (imageInput) imageInput.value = '';
        if (videoInput) videoInput.value = '';
        if (attachInput) attachInput.value = '';
    });
        if (videoInput) videoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 50 * 1024 * 1024) {
            alert(' Video muy pesado (máximo 50MB)');
            videoInput.value = '';
            return;
        }

        const video = document.createElement('video');
        video.preload = 'metadata';

        video.onloadedmetadata = () => {
            window.URL.revokeObjectURL(video.src);
            if (video.duration > 30) {
                alert(' Video muy largo (máximo 30 segundos)');
                videoInput.value = '';
                return;
            }

            selectedVideoFile = file;
            console.log(`🎥 Video listo: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB, ${Math.round(video.duration)}s)`);
        };

        video.src = URL.createObjectURL(file);
    });

    if (document) document.addEventListener('paste', (e) => {
        const items = e.clipboardData?.items;
        if (!items) return;
        
        for (let item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (!file) continue;
                
                processImageFile(file);
                break; 
            }
        }
    });
    
    // Drag and drop para imágenes y videos
    document.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        chatContainer.style.opacity = '0.7';
    });
    
    document.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        chatContainer.style.opacity = '1';
    });
    
    document.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        chatContainer.style.opacity = '1';
        
        const files = e.dataTransfer?.files;
        if (!files) return;
        
        for (let file of files) {
            if (file.type.startsWith('video/')) {
                console.log('🎥 Video detectado por drag & drop');
                if (file.size > 50 * 1024 * 1024) {
                    alert('🎥 Video muy pesado (máximo 50MB)');
                    return;
                }
                const video = document.createElement('video');
                video.preload = 'metadata';
                video.onloadedmetadata = () => {
                    window.URL.revokeObjectURL(video.src);
                    if (video.duration > 30) {
                        alert('🎥 Video muy largo (máximo 30 segundos)');
                        return;
                    }
                    
                    selectedVideoFile = file;
                    
                    // Extraer primer frame como thumbnail
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0);
                    imagePreview.src = canvas.toDataURL();
                    imagePreviewContainer.style.display = 'block';
                    
                    console.log(`🎥 Video listo (drag): ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB, ${Math.round(video.duration)}s)`);
                };
                video.src = URL.createObjectURL(file);
                break;
            } else if (file.type.startsWith('image/')) {
                console.log('📸 Imagen detectada por drag & drop');
                processImageFile(file);
                break;
            }
        }
    });

    initParallax();
}
function initParallax() {
    const container = document.getElementById('parallax-bg');
    if (!container) return;

    const squares = Array.from(container.querySelectorAll('.parallax-square'));
    if (squares.length === 0) return;

    let winW = window.innerWidth;
    let winH = window.innerHeight;
    let pointerX = 0;
    let pointerY = 0;

    function onMove(e) {
        pointerX = (e.clientX / winW - 0.5);
        pointerY = (e.clientY / winH - 0.5);
    }

    function animate() {
        squares.forEach((sq) => {
            const depth = parseFloat(sq.dataset.depth || '0.04');
            const tx = -pointerX * depth * 120; // horizontal movement
            const ty = -pointerY * depth * 80;  // vertical movement
            const scale = 1 - depth * 0.06;
            sq.style.transform = `translate3d(${tx.toFixed(2)}px, ${ty.toFixed(2)}px, 0) scale(${scale.toFixed(3)})`;
        });
        requestAnimationFrame(animate);
    }

    window.addEventListener('mousemove', onMove);
    window.addEventListener('resize', () => { winW = window.innerWidth; winH = window.innerHeight; });
    requestAnimationFrame(animate);
}

async function processImageFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('eso no es una imagen pa');
        return;
    }

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
            let width = img.width;
            let height = img.height;
            const maxDimension = 1920; 
            
            if (width > maxDimension || height > maxDimension) {
                const ratio = Math.min(maxDimension / width, maxDimension / height);
                width = Math.floor(width * ratio);
                height = Math.floor(height * ratio);
                console.log(`🔽 Redimensionando imagen de ${img.width}x${img.height} a ${width}x${height}`);
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);
        
            canvas.toBlob((blob) => {
                if (!blob) {
                    alert('error procesando imagen');
                    return;
                }

                const compressedSizeKB = blob.size / 1024;
                console.log(`📦 Imagen comprimida: ${compressedSizeKB.toFixed(0)}KB`);
                
                if (blob.size > 5 * 1024 * 1024) {
                    alert('imagen muy pesada incluso después de comprimir (max 5MB)');
                    return;
                }

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
            }, 'image/jpeg', 0.85); 
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
    const rate = canCreateNewChat();
    if (!rate.allowed) {
        addSystemMessage(`Please wait ${rate.wait}s before creating another chat.`);
        disableNewChatButtonFor(rate.wait);
        return;
    }

    recordNewChatCreation();

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

    const nextRate = canCreateNewChat();
    if (!nextRate.allowed) disableNewChatButtonFor(nextRate.wait);
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
                <h2>CookieAI</h2>
                <p>Ask. Stupid. Questions</p>
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
    if (!sidebar) return;
    sidebar.classList.toggle('hidden');
}

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
    if (!modelSelect) return null;
    modelSelect.innerHTML = '';

    const models = availableModels[currentProvider] || [];

    if (models.length === 0) {
        modelSelect.innerHTML = '<option value="">No models</option>';
        return null;
    }

    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = getShortModelName(model);
        modelSelect.appendChild(option);
    });

    let selectedModel = pickModelForMode(models, currentMode);

    if (!selectedModel && currentMode === 'thinking') {
        currentMode = 'instant';
        updateModeButtons();
        selectedModel = pickModelForMode(models, currentMode);
    }

    if (!selectedModel) {
        selectedModel = models[0] || null;
        if (selectedModel) {
            console.log(`  Usando modelo disponible: ${getShortModelName(selectedModel)}`);
        }
    }

    if (selectedModel) {
        currentModel = selectedModel;
        modelSelect.value = currentModel;
    }

    return selectedModel;
}
async function sendMessage() {
    if (isLoading) return;
    const message = messageInput.value.trim();
    if (!message && !selectedImageBase64) return;
    
    if (!firstMessageSent) {
        firstMessageSent = true;
        messageInput.placeholder = ""; 
    }
    
    const chat = getCurrentChat();
    const imageToSend = selectedImageBase64;
    const imageUrlToDisplay = selectedImageBase64 ? `data:image/jpeg;base64,${selectedImageBase64}` : null;
    const videoToSend = selectedVideoFile;
    
    messageInput.value = '';
    autoResizeTextarea();
    
    // limpiar imagen/video despues de un poquito para que no se bugee
    setTimeout(() => {
        selectedImageBase64 = null;
        selectedVideoFile = null;
        imagePreviewContainer.style.display = 'none';
        imageInput.value = '';
        attachInput.value = '';
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

        if (imageToSend) {
            console.log('📸 Enviando imagen:', imageToSend.length, 'chars de base64');
        }
        
        const doRequest = async () => {
            if (videoToSend) {
                const formData = new FormData();
                formData.append('message', message);
                formData.append('video', videoToSend);
                formData.append('provider', currentProvider);
                formData.append('model', currentModel);
                formData.append('session_id', chat.id);

                console.log('📤 Enviando video al servidor...');
                return fetch(`${API_URL}/chat`, {
                    method: 'POST',
                    body: formData
                });
            }

            const requestBody = {
                message: message,
                image: imageToSend || null, // base64 puro pal server
                provider: currentProvider,
                model: currentModel,
                session_id: chat.id
            };

            return fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
        };

        let attempts = currentMode === 'thinking' ? 2 : 1;
        let attempt = 0;

        while (attempt < attempts) {
            const response = await doRequest();
            const contentType = response.headers.get('content-type');

            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Server returned non-JSON response:', text.substring(0, 200));
                removeLoadingMessage(loadingId);
                addSystemMessage(`Error ${response.status}: Video or file might be too large. Max 50MB for videos.`);
                return;
            }

            const data = await response.json();

            if (response.status === 429) {
                markModelRateLimited(currentModel, data.wait_time || 30);
                if (currentMode === 'thinking' && attempt === 0) {
                    setMode('instant', { silent: true });
                    attempt += 1;
                    continue;
                }
                removeLoadingMessage(loadingId);
                showRateLimitWarning(data.wait_time || 0);
                addSystemMessage(`Hold on, wait ${data.wait_time || 0}s`);
                return;
            }

            removeLoadingMessage(loadingId);

            if (!response.ok) {
                addSystemMessage(`Error ${response.status}: ${data.error || 'Server error'}`);
                return;
            }

            if (data.error) {
                addSystemMessage(`Error: ${data.error}`);
                return;
            }

            addMessageToDOM('assistant', data.message, data.model);
            chat.messages.push({
                role: 'assistant',
                content: data.message,
                model: data.model
            });
            saveChats();
            return;
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        console.error('Error al conectar:', error);
        

        if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            addSystemMessage(' No se pudo conectar al servidor. Verifica que el backend esté corriendo.');
        } else if (error.message.includes('NetworkError')) {
            addSystemMessage(' Error de red. Verifica tu conexión a internet.');
        } else {
            addSystemMessage(` Error: ${error.message || 'No se pudo enviar el mensaje'}`);
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
        console.log(' connected:', data.status);
    } catch (error) {
        if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            return checkHealth(retries - 1);
        }
        addSystemMessage('Server offline');
    }
}

checkHealth();