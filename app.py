from flask import Flask, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from collections import defaultdict
import os
import json
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aleksin-games-v7-super-secret-key-2026'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# БАЗА ДАННЫХ
def init_db():
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboards 
                 (game TEXT, username TEXT, score INTEGER, date TEXT, PRIMARY KEY(game, username))''')
    c.execute('''CREATE TABLE IF NOT EXISTS online_users 
                 (username TEXT PRIMARY KEY, last_seen TEXT)''')
    conn.commit()
    conn.close()

leaderboards = defaultdict(list)
online_users = set()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/ws')
def ws_endpoint():
    return "WebSocket server running!"

@socketio.on('connect')
def handle_connect():
    print('👤 Новый игрок подключился')
    emit('status', {'message': 'Подключен к ALEKSIN GAMES!'})

@socketio.on('disconnect')
def handle_disconnect():
    print('👤 Игрок отключился')

@socketio.on('score')
def handle_score(data):
    print(f'🎮 {data["username"]} забил {data["score"]} в {data["game"]}')
    
    # Сохраняем в БД
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    game_key = data['game']
    c.execute("INSERT OR REPLACE INTO leaderboards (game, username, score, date) VALUES (?, ?, ?, ?)",
              (game_key, data['username'], data['score'], datetime.now().isoformat()))
    conn.commit()
    
    # Загружаем топ-10
    c.execute("SELECT username, score FROM leaderboards WHERE game=? ORDER BY score DESC LIMIT 10", (game_key,))
    top_scores = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]
    leaderboards[game_key] = top_scores
    conn.close()
    
    # Рассылаем всем
    emit('leaderboards', {'data': dict(leaderboards)}, broadcast=True)

@socketio.on('online_status')
def handle_online(data):
    if data['online']:
        online_users.add(data['username'])
        print(f'👋 {data["username"]} онлайн')
    else:
        online_users.discard(data['username'])
        print(f'👋 {data["username"]} оффлайн')
    
    emit('online_users', {'users': list(online_users)}, broadcast=True)

@socketio.on('chat')
def handle_chat(data):
    message = {
        'username': data['username'],
        'message': data['message'],
        'time': datetime.now().strftime('%H:%M:%S')
    }
    print(f'💬 {data["username"]}: {data["message"]}')
    emit('chat', message, broadcast=True)

@socketio.on('heartbeat')
def handle_heartbeat():
    pass  # Просто пингов для keep-alive

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
