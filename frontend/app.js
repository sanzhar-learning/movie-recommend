const loginScreen = document.getElementById('login-screen');
const chatScreen = document.getElementById('chat-screen');
const loginForm = document.getElementById('login-form');
const chatForm = document.getElementById('chat-form');
const usernameInput = document.getElementById('username-input');
const messageInput = document.getElementById('message-input');
const messagesDiv = document.getElementById('messages');
const userLabel = document.getElementById('user-label');
const resetBtn = document.getElementById('reset-btn');

let username = '';

loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    username = usernameInput.value.trim();
    if (!username) return;

    loginScreen.classList.add('hidden');
    chatScreen.classList.remove('hidden');
    userLabel.textContent = username;
    messageInput.focus();

    sendMessage('hello');
});

resetBtn.addEventListener('click', () => {
    addMessage('reset', 'user');
    sendMessage('reset');
});

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = messageInput.value.trim();
    if (!msg) return;
    messageInput.value = '';

    addMessage(msg, 'user');
    sendMessage(msg);
});

async function sendMessage(text) {
    const typing = addTyping();

    try {
        const resp = await fetch('/api/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, message: text }),
        });
        const data = await resp.json();
        typing.remove();

        if (data.clear_chat) {
            messagesDiv.innerHTML = '';
        }
        addBotMessage(data.reply, data.movies || []);
    } catch (err) {
        typing.remove();
        addMessage('Something went wrong. Please try again.', 'bot');
    }
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.textContent = text;
    messagesDiv.appendChild(div);
    scrollToBottom();
    return div;
}

function addBotMessage(text, movies) {
    const div = document.createElement('div');
    div.className = 'message bot';

    // Parse markdown bold
    const html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    div.innerHTML = html;

    // Add movie cards if present
    if (movies.length > 0) {
        const cards = document.createElement('div');
        cards.className = 'movie-cards';
        movies.forEach((m) => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            const poster = m.poster_url
                ? `<img src="${m.poster_url}" alt="${m.title}">`
                : `<div style="height:200px;background:#222;display:flex;align-items:center;justify-content:center;color:#555">No Poster</div>`;
            const rating = m.vote_average ? `⭐ ${m.vote_average.toFixed(1)}` : '';
            card.innerHTML = `
                ${poster}
                <div class="info">
                    <div class="title">${m.title}</div>
                    <div class="meta">ID: ${m.id} ${rating}</div>
                </div>
            `;
            cards.appendChild(card);
        });
        div.appendChild(cards);
    }

    messagesDiv.appendChild(div);
    scrollToBottom();
}

function addTyping() {
    const div = document.createElement('div');
    div.className = 'message bot typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    messagesDiv.appendChild(div);
    scrollToBottom();
    return div;
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
