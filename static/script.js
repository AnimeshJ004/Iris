/* ═══════════════════════════════════════════════════════════════════
   IRIS AI ASSISTANT — Frontend Application
   ═══════════════════════════════════════════════════════════════════ */

// ── State ────────────────────────────────────────────────────────────
const state = {
    currentSessionId: null,
    sessions: [],
    voiceEnabled: false,
    isProcessing: false,
    recognition: null,
    isListening: false,
};

// ── DOM Elements ─────────────────────────────────────────────────────
const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
    messagesContainer: $('#messagesContainer'),
    welcomeScreen:     $('#welcomeScreen'),
    commandInput:      $('#commandInput'),
    sendBtn:           $('#sendBtn'),
    voiceInputBtn:     $('#voiceInputBtn'),
    voiceToggleBtn:    $('#voiceToggleBtn'),
    voiceIcon:         $('#voiceIcon'),
    newChatBtn:        $('#newChatBtn'),
    sessionsList:      $('#sessionsList'),
    chatTitle:         $('#chatTitle'),
    themeToggleBtn:    $('#themeToggleBtn'),
    themeIcon:         $('#themeIcon'),
    clearAllBtn:       $('#clearAllBtn'),
    mobileMenuBtn:     $('#mobileMenuBtn'),
    sidebar:           $('#sidebar'),
    sidebarOverlay:    $('#sidebarOverlay'),
    inputWrapper:      $('#inputWrapper'),
};


// ── Initialize ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initInput();
    initVoice();
    initSidebar();
    initSuggestions();
    loadSessions();
});


// ═══════════════════════════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════════════════════════

function initTheme() {
    const saved = localStorage.getItem('iris-theme') || 'dark';
    setTheme(saved);

    dom.themeToggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        setTheme(current === 'dark' ? 'light' : 'dark');
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('iris-theme', theme);
    dom.themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
}


// ═══════════════════════════════════════════════════════════════════
// INPUT HANDLING
// ═══════════════════════════════════════════════════════════════════

function initInput() {
    // Auto-resize textarea
    dom.commandInput.addEventListener('input', () => {
        autoResizeTextarea();
        updateSendButton();
    });

    // Enter to send, Shift+Enter for newline
    dom.commandInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Send button
    dom.sendBtn.addEventListener('click', handleSend);
}

function autoResizeTextarea() {
    const ta = dom.commandInput;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 150) + 'px';
}

function updateSendButton() {
    const hasText = dom.commandInput.value.trim().length > 0;
    dom.sendBtn.classList.toggle('active', hasText);
}

async function handleSend() {
    const text = dom.commandInput.value.trim();
    if (!text || state.isProcessing) return;

    // Ensure we have a session
    if (!state.currentSessionId) {
        await createNewSession(text.substring(0, 40));
    }

    // Hide welcome screen
    if (dom.welcomeScreen) {
        dom.welcomeScreen.classList.add('hidden');
    }

    // Add user message
    addMessage('user', text);

    // Clear input
    dom.commandInput.value = '';
    dom.commandInput.style.height = 'auto';
    updateSendButton();

    // Send to backend
    await sendCommand(text);
}


// ═══════════════════════════════════════════════════════════════════
// MESSAGING
// ═══════════════════════════════════════════════════════════════════

function addMessage(sender, text, animate = true) {
    const msg = document.createElement('div');
    msg.className = `message ${sender}`;
    if (!animate) msg.style.animation = 'none';

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const avatarContent = sender === 'user' ? 'U' : '✦';
    const senderName = sender === 'user' ? 'You' : 'Iris';

    msg.innerHTML = `
        <div class="message-avatar">${avatarContent}</div>
        <div class="message-content">
            <div class="message-sender">
                ${senderName}
                <span class="message-timestamp">${timeStr}</span>
            </div>
            <div class="message-body"></div>
        </div>
    `;

    const body = msg.querySelector('.message-body');

    if (sender === 'assistant') {
        body.innerHTML = renderMarkdown(text);
        addCopyButtons(body);
    } else {
        body.textContent = text;
    }

    dom.messagesContainer.appendChild(msg);
    scrollToBottom();

    return msg;
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="message-avatar" style="background: var(--accent-gradient); color: white; font-size: 0.75rem;">✦</div>
        <div class="message-content">
            <div class="message-sender" style="color: var(--accent-mid);">Iris</div>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    dom.messagesContainer.appendChild(indicator);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
    });
}


// ═══════════════════════════════════════════════════════════════════
// BACKEND COMMUNICATION
// ═══════════════════════════════════════════════════════════════════

async function sendCommand(command) {
    state.isProcessing = true;
    showTypingIndicator();

    try {
        // Try streaming first
        const response = await fetch('/api/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                command: command,
                session_id: state.currentSessionId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        removeTypingIndicator();

        // Create message bubble for streaming
        const msg = addMessage('assistant', '');
        const body = msg.querySelector('.message-body');
        let fullText = '';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let renderTimeout = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                if (renderTimeout) clearTimeout(renderTimeout);
                body.innerHTML = renderMarkdown(fullText);
                addCopyButtons(body);
                scrollToBottom();
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            // Process SSE lines
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.chunk) {
                            fullText += data.chunk;
                            
                            // Throttle rendering to ~10fps to avoid freezing the UI
                            if (!renderTimeout) {
                                renderTimeout = setTimeout(() => {
                                    body.innerHTML = renderMarkdown(fullText);
                                    addCopyButtons(body);
                                    scrollToBottom();
                                    renderTimeout = null;
                                }, 100);
                            }
                        }
                        if (data.done) {
                            // Streaming complete
                        }
                    } catch (e) {
                        // Skip malformed JSON
                    }
                }
            }
        }

        // Voice output if enabled
        if (state.voiceEnabled && fullText) {
            speakText(fullText);
        }

    } catch (error) {
        console.error('Stream error, falling back to regular API:', error);
        removeTypingIndicator();

        // Fallback to non-streaming API
        try {
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: command,
                    session_id: state.currentSessionId,
                }),
            });
            const data = await res.json();

            if (data.response) {
                addMessage('assistant', data.response);
                if (state.voiceEnabled) speakText(data.response);
            } else if (data.error) {
                addMessage('assistant', `⚠️ ${data.error}`);
            }
        } catch (e) {
            addMessage('assistant', '⚠️ Sorry, I couldn\'t connect to the server. Please check that the backend is running.');
        }
    }

    state.isProcessing = false;
}


// ═══════════════════════════════════════════════════════════════════
// MARKDOWN RENDERING
// ═══════════════════════════════════════════════════════════════════

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
        });
        return marked.parse(text);
    }
    // Fallback: basic text with line breaks
    return text.replace(/\n/g, '<br>');
}

function addCopyButtons(container) {
    container.querySelectorAll('pre').forEach((pre) => {
        // Don't add duplicate buttons
        if (pre.querySelector('.code-copy-btn')) return;

        const btn = document.createElement('button');
        btn.className = 'code-copy-btn';
        btn.textContent = 'Copy';
        btn.addEventListener('click', () => {
            const code = pre.querySelector('code')?.textContent || pre.textContent;
            navigator.clipboard.writeText(code).then(() => {
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }, 2000);
            });
        });
        pre.style.position = 'relative';
        pre.appendChild(btn);
    });
}


// ═══════════════════════════════════════════════════════════════════
// VOICE
// ═══════════════════════════════════════════════════════════════════

function initVoice() {
    // Voice output toggle
    const savedVoice = localStorage.getItem('iris-voice') === 'true';
    state.voiceEnabled = savedVoice;
    updateVoiceUI();

    dom.voiceToggleBtn.addEventListener('click', () => {
        state.voiceEnabled = !state.voiceEnabled;
        localStorage.setItem('iris-voice', state.voiceEnabled);
        updateVoiceUI();
    });

    // Voice input
    dom.voiceInputBtn.addEventListener('click', toggleVoiceInput);
}

function updateVoiceUI() {
    dom.voiceIcon.textContent = state.voiceEnabled ? '🔊' : '🔇';
    dom.voiceToggleBtn.classList.toggle('active', state.voiceEnabled);
}

function toggleVoiceInput() {
    if (state.isListening) {
        stopVoiceInput();
        return;
    }

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        addMessage('assistant', '⚠️ Speech recognition is not supported in this browser. Try Chrome.');
        return;
    }

    state.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    state.recognition.lang = 'en-US';
    state.recognition.interimResults = true;
    state.recognition.maxAlternatives = 1;

    state.recognition.onstart = () => {
        state.isListening = true;
        dom.voiceInputBtn.classList.add('voice-active');
        dom.voiceInputBtn.textContent = '⏹';
    };

    state.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        dom.commandInput.value = transcript;
        autoResizeTextarea();
        updateSendButton();

        // Auto-send on final result
        if (event.results[0].isFinal) {
            handleSend();
        }
    };

    state.recognition.onerror = (event) => {
        console.error('Speech error:', event.error);
        if (event.error !== 'aborted') {
            addMessage('assistant', '⚠️ Couldn\'t hear you clearly. Please try again.');
        }
    };

    state.recognition.onend = () => {
        state.isListening = false;
        dom.voiceInputBtn.classList.remove('voice-active');
        dom.voiceInputBtn.textContent = '🎤';
    };

    state.recognition.start();
}

function stopVoiceInput() {
    if (state.recognition) {
        state.recognition.stop();
    }
}

function speakText(text) {
    if (!('speechSynthesis' in window)) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Strip markdown for cleaner speech
    const cleanText = text
        .replace(/```[\s\S]*?```/g, 'code block omitted')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/#{1,6}\s/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/[_~]/g, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
}


// ═══════════════════════════════════════════════════════════════════
// SESSIONS
// ═══════════════════════════════════════════════════════════════════

function initSidebar() {
    dom.mobileMenuBtn.addEventListener('click', toggleSidebar);
    dom.sidebarOverlay.addEventListener('click', closeSidebar);
    dom.newChatBtn.addEventListener('click', () => createNewSession());
    dom.clearAllBtn.addEventListener('click', clearAllChats);
}

function toggleSidebar() {
    dom.sidebar.classList.toggle('open');
    dom.sidebarOverlay.classList.toggle('visible');
}

function closeSidebar() {
    dom.sidebar.classList.remove('open');
    dom.sidebarOverlay.classList.remove('visible');
}

async function loadSessions() {
    try {
        const res = await fetch('/api/sessions');
        const data = await res.json();
        state.sessions = data.sessions || [];
        renderSessions();

        // Auto-select latest session or show welcome
        if (state.sessions.length > 0) {
            switchToSession(state.sessions[0].session_id);
        }
    } catch (e) {
        console.log('Could not load sessions:', e);
    }
}

async function createNewSession(title = 'New Chat') {
    try {
        const res = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title }),
        });
        const data = await res.json();

        state.currentSessionId = data.session_id;
        state.sessions.unshift({
            session_id: data.session_id,
            title: data.title,
            created_at: new Date().toISOString(),
        });

        renderSessions();
        clearMessages();
        dom.chatTitle.textContent = title;
        closeSidebar();
    } catch (e) {
        // Offline fallback — generate a local ID
        state.currentSessionId = 'local-' + Date.now();
        dom.chatTitle.textContent = title;
    }
}

async function switchToSession(sessionId) {
    state.currentSessionId = sessionId;
    clearMessages();
    renderSessions();
    closeSidebar();

    // Update title
    const session = state.sessions.find(s => s.session_id === sessionId);
    dom.chatTitle.textContent = session?.title || 'Chat';

    // Load history
    try {
        const res = await fetch(`/api/history?session_id=${sessionId}`);
        const data = await res.json();

        if (data.conversations && data.conversations.length > 0) {
            if (dom.welcomeScreen) dom.welcomeScreen.classList.add('hidden');

            data.conversations.forEach(conv => {
                addMessage('user', conv.user_command, false);
                addMessage('assistant', conv.assistant_response, false);
            });
        }
    } catch (e) {
        console.log('Could not load history:', e);
    }
}

async function deleteSession(sessionId) {
    try {
        await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
    } catch (e) {
        console.log('Could not delete session on server:', e);
    }

    state.sessions = state.sessions.filter(s => s.session_id !== sessionId);
    renderSessions();

    if (state.currentSessionId === sessionId) {
        state.currentSessionId = null;
        clearMessages();
        if (state.sessions.length > 0) {
            switchToSession(state.sessions[0].session_id);
        } else {
            dom.chatTitle.textContent = 'New Chat';
        }
    }
}

function renderSessions() {
    dom.sessionsList.innerHTML = '';

    state.sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = `session-item ${session.session_id === state.currentSessionId ? 'active' : ''}`;

        item.innerHTML = `
            <span class="session-icon">💬</span>
            <span class="session-title">${escapeHtml(session.title)}</span>
            <button class="session-delete" title="Delete chat">✕</button>
        `;

        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('session-delete')) {
                switchToSession(session.session_id);
            }
        });

        item.querySelector('.session-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(session.session_id);
        });

        dom.sessionsList.appendChild(item);
    });
}

function clearMessages() {
    // Remove all messages and typing indicators, keep welcome screen
    const messages = dom.messagesContainer.querySelectorAll('.message, .typing-indicator');
    messages.forEach(m => m.remove());

    // Show welcome screen if it exists
    if (dom.welcomeScreen) {
        dom.welcomeScreen.classList.remove('hidden');
    }
}

async function clearAllChats() {
    if (!confirm('Delete all conversations? This cannot be undone.')) return;

    try {
        // Delete each session
        for (const session of state.sessions) {
            await fetch(`/api/sessions/${session.session_id}`, { method: 'DELETE' });
        }
    } catch (e) {
        console.log('Error clearing chats:', e);
    }

    state.sessions = [];
    state.currentSessionId = null;
    renderSessions();
    clearMessages();
    dom.chatTitle.textContent = 'New Chat';
}


// ═══════════════════════════════════════════════════════════════════
// SUGGESTIONS
// ═══════════════════════════════════════════════════════════════════

function initSuggestions() {
    $$('.suggestion-card').forEach(card => {
        card.addEventListener('click', () => {
            const text = card.getAttribute('data-suggestion');
            dom.commandInput.value = text;
            autoResizeTextarea();
            updateSendButton();
            handleSend();
        });
    });
}


// ═══════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}



