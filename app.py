from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)
DATA_FILE = 'games_data.json'
sessions = {}

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        'users': {'test': {'password': '123456'}},
        'leaderboards': {'snake': {'easy':{}, 'normal':{}, 'hard':{}}, 'guess': {'easy':{}, 'normal':{}, 'hard':{}}},
        'tournament': {},
        'chat': []
    }

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def get_user():
    token = request.headers.get('Authorization')
    return sessions.get(token)

@app.route('/')
def index():
    try:
        return open('index.html').read()
    except:
        return '<h1>🚀 ALEKSIN GAMES v5.4</h1>'

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if len(username) < 3 or len(password) < 4:
        return jsonify({'success': False, 'error': 'Логин ≥3, пароль ≥4 символа'})
    
    all_data = load_data()
    if username in all_data['users']:
        return jsonify({'success': False, 'error': 'Пользователь существует'})
    
    all_data['users'][username] = {'password': password}
    save_data(all_data)
    
    token = f"token_{username}_{int(datetime.now().timestamp())}"
    sessions[token] = username
    return jsonify({'success': True, 'user': username, 'token': token})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    all_data = load_data()
    if username in all_data['users'] and all_data['users'][username]['password'] == password:
        token = f"token_{username}_{int(datetime.now().timestamp())}"
        sessions[token] = username
        return jsonify({'success': True, 'user': username, 'token': token})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/api/leaderboards/<game>/<difficulty>')
def get_leaderboard(game, difficulty):
    data = load_data()
    return jsonify(data['leaderboards'].get(game, {}).get(difficulty, {}))

@app.route('/api/scores', methods=['POST'])
def save_score():
    user = get_user()
    if not user:
        return jsonify({'success': False, 'error': 'Войди в аккаунт'}), 401
    
    data = request.get_json()
    all_data = load_data()
    game = data.get('game', 'unknown')
    diff = data.get('difficulty', 'easy')
    score = data.get('score', 0)
    
    if game not in all_data['leaderboards']:
        all_data['leaderboards'][game] = {}
    if diff not in all_data['leaderboards'][game]:
        all_data['leaderboards'][game][diff] = {}
    all_data['leaderboards'][game][diff][user] = max(
        all_data['leaderboards'][game][diff].get(user, 0), score
    )
    save_data(all_data)
    return jsonify({'success': True})

@app.route('/api/tournament', methods=['GET', 'POST'])
def tournament():
    data = load_data()
    if request.method == 'POST':
        user = get_user()
        if not user:
            return jsonify({'success': False, 'error': 'Войди в аккаунт'}), 401
        score = request.get_json().get('score', 0)
        data['tournament'][user] = data['tournament'].get(user, 0) + score
        save_data(data)
        return jsonify({'success': True})
    return jsonify(data['tournament'])

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    data = load_data()
    if request.method == 'POST':
        user = get_user()
        if not user:
            return jsonify({'success': False, 'error': 'Войди в аккаунт'}), 401
        msg = request.get_json().get('message', '')
        data['chat'].append({
            'user': user, 
            'message': msg[:100], 
            'time': datetime.now().strftime('%H:%M')
        })
        data['chat'] = data['chat'][-50:]
        save_data(data)
        return jsonify({'success': True})
    return jsonify(data['chat'])

@app.route('/api/tournament/reset', methods=['POST'])
def reset_tournament():
    data = load_data()
    data['tournament'] = {}
    save_data(data)
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
