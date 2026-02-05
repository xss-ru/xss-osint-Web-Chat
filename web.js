const socket = io();

let username = '';

const loginScreen = document.getElementById('loginScreen');
const chatApp = document.getElementById('chatApp');
const usernameInput = document.getElementById('usernameInput');
const joinBtn = document.getElementById('joinBtn');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const logoutBtn = document.getElementById('logoutBtn');
const messagesContainer = document.getElementById('messagesContainer');
const onlineCount = document.getElementById('onlineCount');
const currentTimeElement = document.getElementById('currentTime');
const messageCountElement = document.getElementById('messageCount');

function updateTime() {
    const now = new Date();
    const time = now.toTimeString().split(' ')[0];
    currentTimeElement.textContent = time;
}

setInterval(updateTime, 1000);
updateTime();

joinBtn.addEventListener('click', joinChat);
usernameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') joinChat();
});

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

logoutBtn.addEventListener('click', () => {
    socket.disconnect();
    chatApp.style.display = 'none';
    loginScreen.style.display = 'flex';
    username = '';
    clearMessages();
});

function joinChat() {
    const name = usernameInput.value.trim();
    if (name) {
        username = name;
        socket.emit('join', { username: name });
        loginScreen.style.display = 'none';
        chatApp.style.display = 'flex';
        messageInput.focus();
    }
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        socket.emit('send_message', { message: message });
        messageInput.value = '';
    }
}

function clearMessages() {
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="message">
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">system</span>
                        <span class="message-time">just now</span>
                    </div>
                    <div class="message-text">
                        disconnected from chat
                    </div>
                </div>
            </div>
        </div>
    `;
    updateMessageCount();
}

socket.on('connect', () => {
    console.log('connected');
});

socket.on('disconnect', () => {
    console.log('disconnected');
});

socket.on('user_count', (data) => {
    onlineCount.textContent = `${data.count} online`;
});

socket.on('user_joined', (data) => {
    onlineCount.textContent = `${data.count} online`;
    if (data.username !== username) {
        addSystemMessage(`${data.username} joined`);
    }
    updateMessageCount();
});

socket.on('user_left', (data) => {
    onlineCount.textContent = `${data.count} online`;
    addSystemMessage(`${data.username} left`);
    removeUserMessages(data.username);
    updateMessageCount();
});

socket.on('load_messages', (data) => {
    clearMessages();
    const welcome = messagesContainer.querySelector('.welcome-message');
    data.messages.forEach(msg => {
        if (msg.username !== username) {
            addMessage(msg);
        }
    });
    updateMessageCount();
    scrollToBottom();
});

socket.on('new_message', (data) => {
    addMessage(data);
    scrollToBottom();
    updateMessageCount();
});

function addMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';

    const isCurrentUser = data.username === username;
    const displayName = isCurrentUser ? 'you' : data.username;

    const messageText = data.message.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">${displayName}</span>
                <span class="message-time">${data.timestamp}</span>
            </div>
            <div class="message-text">${messageText}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';

    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">system</span>
                <span class="message-time">just now</span>
            </div>
            <div class="message-text">${text}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function removeUserMessages(username) {
    const messages = messagesContainer.querySelectorAll('.message');
    messages.forEach(msg => {
        const author = msg.querySelector('.message-author');
        if (author && author.textContent === username) {
            msg.remove();
        }
    });
}

function updateMessageCount() {
    const count = messagesContainer.querySelectorAll('.message').length;
    messageCountElement.textContent = `${count} messages`;
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}