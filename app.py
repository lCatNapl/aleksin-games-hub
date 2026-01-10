from flask import Flask, send_file, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'aleksin-games-2026-super-secret-key-666'
CORS(app, supports_credentials=True)

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
    username = session.get('username', 'Гость')
    return jsonify({'logged_in': username != 'Гость', 'username': username})

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if len(username) < 3:
            return jsonify({'ok': False, 'error': 'Имя 3+ символа!'})
        
        if username in users_db:
            return jsonify({'ok': False, 'error': 'Пользователь существует!'})
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        users_db[username] = password_hash
        session['username'] = username
        return jsonify({'ok': True})
    except:
        return jsonify({'ok': False, 'error': 'Ошибка сервера'})

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username in users_db and users_db[username] == password_hash:
            session['username'] = username
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'error': 'Неправильный логин/пароль'})
    except:
        return jsonify({'ok': False, 'error': 'Ошибка сервера'})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/save_score', methods=['POST'])
def save_score():
    try:
        username = session.get('username', 'Гость')
        data = request.get_json()
        game = data.get('game', 'unknown')
        difficulty = data.get('difficulty', 'easy')
        score = int(data.get('score', 0))
        
        key = f"{game}_{difficulty}_{username}"
        scores_db[key] = {
            'username': username,
            'game': game,
            'difficulty': difficulty,
            'score': score,
            'date': datetime.now().isoformat()
        }
        return jsonify({'ok': True})
    except:
        return jsonify({'ok': True})

@app.route('/top10/<game>/<diff>')
def top10(game, diff):
    game_scores = []
    for score_data in scores_db.values():
        if score_data['game'] == game and score_data['difficulty'] == diff:
            game_scores.append(score_data)
    
    top_scores = sorted(game_scores, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(top_scores)

@app.route('/user_scores/<username>')
def user_scores(username):
    user_scores = {}
    total = 0
    
    for score_data in scores_db.values():
        if score_data['username'] == username:
            game_key = f"best{score_data['game'].title()}{score_data['difficulty'].title()}"
            user_scores[game_key] = max(user_scores.get(game_key, 0), score_data['score'])
            total += score_data['score']
    
    user_scores['totalScore'] = total
    return jsonify(user_scores)

@app.route('/chat/messages')
def chat_messages_api():
    return jsonify(chat_messages[-50:])

@app.route('/chat/send', methods=['POST'])
def chat_send():
    try:
        username = session.get('username', 'Гость')
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if message and len(message) <= 200:
            chat_messages.append({
                'username': username,
                'message': message,
                'time': datetime.now().strftime('%H:%M'),
                'timestamp': datetime.now().isoformat()
            })
        return jsonify({'ok': True})
    except:
        return jsonify({'ok': False})

@app.errorhandler(404)
@app.errorhandler(500)
def errors(e):
    return send_file('index.html'), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
