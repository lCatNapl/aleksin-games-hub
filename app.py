from flask import Flask, send_file, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'aleksin-games-2026-super-secret'
CORS(app)

# Простая БД в памяти
users_db = {}
scores_db = {}
chat_messages = []

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return send_file('index.html')

@app.route('/status')
def status():
    username = session.get('username')
    return jsonify({'logged_in': bool(username), 'username': username or 'Гость'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if len(username) < 3:
        return jsonify({'ok': False, 'error': 'Имя 3+ символа!'})
    
    if username in users_db:
        return jsonify({'ok': False, 'error': 'Пользователь существует!'})
    
    # Хешируем пароль
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    users_db[username] = password_hash
    
    session['username'] = username
    return jsonify({'ok': True})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if username in users_db and users_db[username] == password_hash:
        session['username'] = username
        return jsonify({'ok': True})
    else:
        return jsonify({'ok': False, 'error': 'Неправильный логин/пароль'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'ok': True})

@app.route('/save_score', methods=['POST'])
def save_score():
    username = session.get('username', 'Гость')
    data = request.json
    
    key = f"{data['game']}_{data['difficulty']}_{username}"
    scores_db[key] = {
        'username': username,
        'game': data['game'],
        'difficulty': data['difficulty'],
        'score': data['score'],
        'date': datetime.now().isoformat()
    }
    
    return jsonify({'ok': True})

@app.route('/top10/<game>/<diff>')
def top10(game, diff):
    game_scores = []
    for key, score in scores_db.items():
        if score['game'] == game and score['difficulty'] == diff:
            game_scores.append(score)
    
    # Топ-10
    top_scores = sorted(game_scores, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(top_scores)

@app.route('/user_scores/<username>')
def user_scores(username):
    user_scores = {}
    total = 0
    
    for key, score in scores_db.items():
        if score['username'] == username:
            game_key = f"best{score['game'].title()}{score['difficulty'].title()}"
            user_scores[game_key] = max(user_scores.get(game_key, 0), score['score'])
            total += score['score']
    
    user_scores['totalScore'] = total
    user_scores['totalGames'] = len([s for s in scores_db.values() if s['username'] == username])
    return jsonify(user_scores)

# ✅ ЧАТ
@app.route('/chat/messages')
def chat_messages():
    return jsonify(chat_messages[-50:])  # Последние 50 сообщений

@app.route('/chat/send', methods=['POST'])
def chat_send():
    username = session.get('username', 'Гость')
    data = request.json
    message = data.get('message', '').strip()
    
    if message and len(message) <= 200:
        chat_messages.append({
            'username': username,
            'message': message,
            'time': datetime.now().strftime('%H:%M'),
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({'ok': True})

@app.errorhandler(404)
@app.errorhandler(500)
def errors(e):
    return send_file('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
