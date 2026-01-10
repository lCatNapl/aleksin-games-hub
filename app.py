from flask import Flask, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aleksin-games-v7-super-secret-2026'
CORS(app)

# ❌ УБИРАЕМ async_mode - используем дефолтный режим
socketio = SocketIO(app, cors_allowed_origins="*")

leaderboards = defaultdict(list)
online_users = set()

def init_db():
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboards 
                 (game TEXT, username TEXT, score INTEGER, date TEXT, 
                  PRIMARY KEY(game, username))''')
    c.execute('''CREATE TABLE IF NOT EXISTS online_users 
                 (username TEXT PRIMARY KEY, last_seen TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/ws')
def ws_info():
    return "🚀 ALEKSIN GAMES WebSocket готов!"

@socketio.on('connect')
def connect():
    print('👤 Подключился:', request.sid)
    emit('status', {'message': '✅ Подключен к серверам Тулы!'})

@socketio.on('disconnect')
def disconnect():
    print('👤 Отключился:', request.sid)

@socketio.on('score')
def handle_score(data):
    print(f'🎮 {data["username"]} | {data["game"]}: {data["score"]}')
    
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboards VALUES (?, ?, ?, ?)",
              (data['game'], data['username'], data['score'], datetime.now().isoformat()))
    conn.commit()
    
    # Топ-10 по игре
    c.execute("SELECT username, score FROM leaderboards WHERE game=? ORDER BY score DESC LIMIT 10", 
              (data['game'],))
    top10 = [{'username': r[0], 'score': r[1]} for r in c.fetchall()]
    leaderboards[data['game']] = top10
    conn.close()
    
    emit('leaderboards', {'data': dict(leaderboards)}, broadcast=True)

@socketio.on('online_status')
def handle_online(data):
    if data['online']:
        online_users.add(data['username'])
    else:
        online_users.discard(data['username'])
    
    print(f'👥 Онлайн: {len(online_users)}')
    emit('online_users', {'users': list(online_users)}, broadcast=True)

@socketio.on('chat')
def handle_chat(data):
    msg = {
        'username': data['username'],
        'message': data['message'][:200],
        'time': datetime.now().strftime('%H:%M')
    }
    print(f'💬 [{msg["time"]}] {msg["username"]}: {msg["message"]}')
    emit('chat', msg, broadcast=True)

@socketio.on('heartbeat')
def heartbeat():
    pass

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
