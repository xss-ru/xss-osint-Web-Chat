from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from datetime import datetime, date
import json
import os
import random

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'xss-osint-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}
messages = []
last_reset_date = date.today()

LOGFILE = 'sok.txt'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xss-osint Web-Chat</title>
    <link rel="stylesheet" href="/web.css">
    <style>
        @media (max-width: 768px) {
            body::before {
                content: 'This chat is only available on desktop devices.';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: #000;
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                z-index: 9999;
                text-align: center;
                padding: 20px;
            }
            .container, .chat-app {
                display: none !important;
            }
        }
    </style>
</head>
<body>
    <div class="background-image"></div>
    <div class="container">
        <div class="login-screen" id="loginScreen">
            <div class="login-modal">
                <div class="login-header">
                    <div class="app-logo">
                        <img src="/one.jpg" alt="Logo" class="logo-img">
                    </div>
                    <h1>xss-osint Web-Chat</h1>
                    <p>secure communication platform</p>
                </div>
                <div class="login-form">
                    <input type="text" id="usernameInput" placeholder="enter username" maxlength="20" autofocus>
                    <button id="joinBtn">enter chat</button>
                    <div class="login-info">
                        <span class="online-count">0 online</span>
                        <span class="security">encrypted</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="chat-app" id="chatApp" style="display: none;">
            <div class="chat-header">
                <div class="header-left">
                    <div class="chat-title">
                        <div class="chat-avatar">
                            <img src="/one.jpg" alt="Chat" class="avatar">
                        </div>
                        <div class="title-text">
                            <h2>xss-osint Web-Chat</h2>
                            <p id="onlineCount">0 online</p>
                        </div>
                    </div>
                </div>
                <div class="header-right">
                    <button class="logout-btn" id="logoutBtn" title="Logout">
                        <span>logout</span>
                    </button>
                </div>
            </div>

            <div class="messages-container" id="messagesContainer">
                <div class="welcome-message">
                    <div class="message">
                        <div class="message-content">
                            <div class="message-header">
                                <span class="message-author">system</span>
                                <span class="message-time">just now</span>
                            </div>
                            <div class="message-text">
                                welcome to xss-osint web-chat. all communications are logged.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="message-input-area">
                <div class="input-wrapper">
                    <input type="text" id="messageInput" placeholder="type message..." autocomplete="off">
                    <button class="send-btn" id="sendBtn">send</button>
                </div>
                <div class="input-info">
                    <span class="time" id="currentTime">--:--:--</span>
                    <span class="messages-count" id="messageCount">0 messages</span>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="/web.js"></script>
</body>
</html>
'''

def check_and_reset_log():
    global last_reset_date
    today = date.today()
    if today != last_reset_date:
        try:
            if os.path.exists(LOGFILE):
                os.remove(LOGFILE)
            last_reset_date = today
        except Exception as e:
            print(f"log reset error: {e}")

def log_message(ip, ua, timestamp, text):
    try:
        check_and_reset_log()
        with open(LOGFILE, 'a', encoding='utf-8') as f:
            log_entry = f"{ip},{ua},{timestamp},{text}\n"
            f.write(log_entry)
    except Exception as e:
        print(f"log error: {e}")

def remove_user_messages(username):
    global messages
    messages = [msg for msg in messages if msg.get('username') != username]

@socketio.on('connect')
def handle_connect():
    try:
        ip = request.remote_addr
        ua = request.headers.get('User-Agent', 'unknown')
        timestamp = datetime.now().isoformat()
        log_message(ip, ua, timestamp, "CONNECT")
    except Exception as e:
        print(f"connect log error: {e}")
    emit('user_count', {'count': len(users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    try:
        ip = request.remote_addr
        ua = request.headers.get('User-Agent', 'unknown')
        timestamp = datetime.now().isoformat()
        username = users.get(request.sid, 'unknown')
        log_message(ip, ua, timestamp, f"DISCONNECT: {username}")
    except Exception as e:
        print(f"disconnect log error: {e}")
    
    if request.sid in users:
        username = users[request.sid]
        del users[request.sid]
        remove_user_messages(username)
        emit('user_left', {'username': username, 'count': len(users)}, broadcast=True)

@socketio.on('join')
def handle_join(data):
    username = data['username']
    users[request.sid] = username
    
    try:
        ip = request.remote_addr
        ua = request.headers.get('User-Agent', 'unknown')
        timestamp = datetime.now().isoformat()
        log_message(ip, ua, timestamp, f"JOIN: {username}")
    except Exception as e:
        print(f"join log error: {e}")
    
    emit('user_joined', {'username': username, 'count': len(users)}, broadcast=True)
    emit('load_messages', {'messages': messages})

@socketio.on('send_message')
def handle_message(data):
    username = users.get(request.sid, 'anonymous')
    timestamp = datetime.now().strftime('%H:%M')
    message_text = data['message']
    
    message_data = {
        'username': username,
        'message': message_text,
        'timestamp': timestamp
    }
    messages.append(message_data)
    
    try:
        ip = request.remote_addr
        ua = request.headers.get('User-Agent', 'unknown')
        log_timestamp = datetime.now().isoformat()
        log_message(ip, ua, log_timestamp, f"MESSAGE [{username}]: {message_text}")
    except Exception as e:
        print(f"message log error: {e}")
    
    if len(messages) > 200:
        messages.pop(0)
    
    emit('new_message', message_data, broadcast=True)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/onion.jpg')
def serve_onion():
    return send_from_directory('.', 'onion.jpg')

@app.route('/one.jpg')
def serve_one():
    return send_from_directory('.', 'one.jpg')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)