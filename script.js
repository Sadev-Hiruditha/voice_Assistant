
// ─── State ───────────────────────────────────────────────
let recognition = null;
let synth = window.speechSynthesis;
let isListening = false;
let isSpeaking = false;
let thinkingEl = null;

// ─── Speech Recognition Setup ────────────────────────────
function initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;
    const r = new SpeechRecognition();
    r.lang = 'en-US';
    r.continuous = false;
    r.interimResults = false;
    r.maxAlternatives = 1;

    r.onresult = e => {
        const cmd = e.results[0][0].transcript.trim();
        stopListening();
        appendMsg('user', cmd);
        processCommand(cmd, true);  // true = voice, route to Python
    };
    r.onerror = e => {
        stopListening();
        setStatus('error', 'Mic error: ' + e.error);
        speak("Sorry, I had trouble hearing you. Please try again.");
    };
    r.onend = () => { if (isListening) stopListening(); };
    return r;
}

// ─── Status helpers ───────────────────────────────────────
function setStatus(state, text) {
    const badge = document.getElementById('statusBadge');
    const label = document.getElementById('statusText');
    badge.className = 'status-badge ' + state;
    label.textContent = text;
    const orb = document.getElementById('orb');
    orb.className = 'orb' + (state === 'listening' ? ' listening' : state === 'speaking' ? ' speaking' : '');
}

// ─── Listen controls ──────────────────────────────────────
function startListening() {
    if (isListening) return;
    recognition = initRecognition();
    if (!recognition) {
        appendMsg('assistant', '⚠️ Your browser does not support the Web Speech API. Try Chrome or Edge.');
        return;
    }
    isListening = true;
    document.getElementById('listenBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;
    setStatus('listening', 'Listening… 🎤');
    speak("How can I assist you?", () => recognition.start());
}

function stopListening() {
    isListening = false;
    if (recognition) { try { recognition.stop(); } catch (_) { } }
    document.getElementById('listenBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    setStatus('ready', 'Ready to assist you');
}

// ─── TTS ──────────────────────────────────────────────────
function speak(text, cb) {
    synth.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate = 1; utt.pitch = 1; utt.volume = 1;
    utt.lang = 'en-US';
    utt.onstart = () => { isSpeaking = true; setStatus('speaking', 'Speaking… 🔊'); };
    utt.onend = () => {
        isSpeaking = false;
        if (!isListening) setStatus('ready', 'Ready to assist you');
        if (cb) cb();
    };
    synth.speak(utt);
}

// ─── Quick-command text input ─────────────────────────────
function sendText(text) {
    if (isListening) stopListening();
    appendMsg('user', text);
    processCommand(text, false);  // false = button click, JS handles locally
}

// ─── Intent detection (mirrors Python logic) ─────────────
function detectIntent(cmd) {
    const t = cmd.toLowerCase();
    if (/wikipedia|wiki/.test(t)) return 'wikipedia';
    if (/play|song|youtube/.test(t)) return 'play_music';
    if (/notepad|note pad/.test(t)) return 'open_notepad';
    if (/microsoft word|\bword\b/.test(t)) return 'open_word';
    if (/\btime\b/.test(t)) return 'time';
    if (/\bdate\b|today/.test(t)) return 'date';
    if (/browser|chrome|firefox/.test(t)) return 'open_browser';
    if (/search|google|look up/.test(t)) return 'search';
    if (/exit|quit|shutdown|goodbye|bye/.test(t)) return 'exit';
    return 'ai';
}

// ─── Command processor ────────────────────────────────────
// Voice commands → always go to Flask (Python opens browser/YouTube server-side)
// Chip buttons  → handled locally in JS (direct click = no popup block)
function processCommand(cmd, fromVoice = true) {
    if (fromVoice) {
        // Let Python handle everything — no popup blocking issue
        callFlask(cmd);
    } else {
        // Button click: JS can safely open tabs
        const intent = detectIntent(cmd);
        const handlers = {
            wikipedia: handleWikipedia,
            play_music: handlePlayMusic,
            open_notepad: handleOpenNotepad,
            open_word: handleOpenWord,
            time: handleTime,
            date: handleDate,
            open_browser: handleOpenBrowser,
            search: handleSearch,
            exit: handleExit,
            ai: handleAI
        };
        (handlers[intent] || handleAI)(cmd);
    }
}

// ─── Handlers ─────────────────────────────────────────────
function handleTime(_) {
    const t = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    reply(`The current time is ${t}.`);
}
function handleDate(_) {
    const d = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    reply(`Today is ${d}.`);
}
function handleOpenBrowser(_) {
    window.open('https://google.com', '_blank');
    reply('Opening Google in a new tab.');
}
function handleSearch(cmd) {
    const q = cmd.replace(/search|google|look up/gi, '').trim();
    if (!q) { reply("What would you like me to search for?"); return; }
    window.open(`https://www.google.com/search?q=${encodeURIComponent(q)}`, '_blank');
    reply(`Searching Google for "${q}".`);
}
function handlePlayMusic(cmd) {
    const song = cmd.replace(/play|music|song|youtube/gi, '').trim();
    if (!song) { reply("What song would you like me to play?"); return; }
    window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(song)}`, '_blank');
    reply(`Opening YouTube for "${song}".`);
}
function handleOpenNotepad(_) {
    reply("Opening Notepad is a desktop action. On Windows, press ⊞ Win + R and type notepad. Alternatively, I can open a simple text editor here.");
}
function handleOpenWord(_) {
    reply("Opening Microsoft Word is a desktop action. On Windows, search for 'Word' in the Start menu, or use Office Online at office.com.");
}
function handleWikipedia(cmd) {
    const q = cmd.replace(/wikipedia|wiki/gi, '').trim();
    if (!q) { reply("What would you like me to search on Wikipedia?"); return; }
    window.open(`https://en.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(q)}`, '_blank');
    callAI(`Give me a brief 2-sentence Wikipedia-style summary about: ${q}`);
}
function handleExit(_) {
    reply("Goodbye! Have a great day! 👋");
    setTimeout(() => setStatus('ready', 'Session ended.'), 2000);
}
function handleAI(cmd) { callAI(cmd); }

// ─── Respond helper ───────────────────────────────────────
function reply(text) {
    removeThinking();
    appendMsg('assistant', text);
    speak(text);
}

// ─── Flask backend call (for voice commands) ─────────────
async function callFlask(prompt) {
    showThinking();
    setStatus('speaking', 'Thinking…');
    try {
        const res = await fetch('/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: prompt })
        });
        const data = await res.json();
        reply(data.response || "Sorry, I couldn't get a response.");
    } catch (e) {
        removeThinking();
        const errMsg = "Can't reach the Python server. Is app.py running?";
        appendMsg('assistant', errMsg);
        speak(errMsg);
        setStatus('error', 'Server error');
    }
}


async function callAI(prompt) {
    showThinking();
    setStatus('speaking', 'Thinking…');
    try {
        // 👇 Calls your Python Flask backend
        const res = await fetch('/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: prompt })
        });
        const data = await res.json();
        reply(data.response || "I'm sorry, I couldn't generate a response.");
    } catch (e) {
        removeThinking();
        const errMsg = "I'm having trouble connecting to the Python server.";
        appendMsg('assistant', errMsg);
        speak(errMsg);
        setStatus('error', 'Server connection error');
    }
}

// ─── Log helpers ──────────────────────────────────────────
function appendMsg(role, text) {
    const body = document.getElementById('logBody');
    document.getElementById('emptyState')?.remove();

    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML = `
    <div class="msg-icon">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="msg-content">
      <div class="msg-label">${role === 'user' ? 'You' : 'Assistant'}</div>
      <div class="msg-text">${text}</div>
    </div>`;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

function showThinking() {
    removeThinking();
    const body = document.getElementById('logBody');
    document.getElementById('emptyState')?.remove();
    thinkingEl = document.createElement('div');
    thinkingEl.className = 'msg assistant';
    thinkingEl.id = 'thinking';
    thinkingEl.innerHTML = `
    <div class="msg-icon">🤖</div>
    <div class="msg-content">
      <div class="msg-label">Assistant</div>
      <div class="thinking"><span></span><span></span><span></span></div>
    </div>`;
    body.appendChild(thinkingEl);
    body.scrollTop = body.scrollHeight;
}

function removeThinking() {
    document.getElementById('thinking')?.remove();
    thinkingEl = null;
}

function clearLog() {
    const body = document.getElementById('logBody');
    body.innerHTML = '<div class="empty-state" id="emptyState">No messages yet. Click "Start Listening" or a quick command.</div>';
}

function quitApp() {
    stopListening();
    synth.cancel();
    speak("Goodbye!");
    setStatus('ready', 'Session ended.');
    document.getElementById('listenBtn').disabled = true;
    document.querySelectorAll('.chip').forEach(c => c.disabled = true);
}

// Orb click = start listening
document.getElementById('orb').addEventListener('click', startListening);

// Greet on load
window.addEventListener('load', () => {
    setTimeout(() => {
        appendMsg('assistant', 'Hello! I\'m your AI Voice Assistant. Click the microphone or use a quick command to get started. I can tell you the time, search the web, play music, answer questions, and more!');
    }, 500);
});
