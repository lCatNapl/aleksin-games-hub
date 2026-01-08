from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-admin-2026'
CORS(app, supports_credentials=True)

DATA_FILE = 'games_data.json'
current_sessions = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'users': {'test': {'password': '123456', 'total': 0}},
        'leaderboards': {'snake': {'easy':{}, 'normal':{}, 'hard':{}}, 'guess': {'easy':{}, 'normal':{}, 'hard':{}}},
        'tournament': {},
        'chat': [],
        'stats': {}
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token not in current_sessions:
            return jsonify({'success': False, 'error': 'Не авторизован'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == 'test' and data.get('password') == '123456':
        token = f"aleksin_{data['username']}_{int(datetime.now().timestamp())}"
        current_sessions[token] = data['username']
        return jsonify({'success': True, 'user': data['username'], 'token': token})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token in current_sessions:
        del current_sessions[token]
    return jsonify({'success': True})

@app.route('/api/scores', methods=['POST'])
@login_required
def save_score():
    data = request.json
    all_data = load_data()
    game = data['game']
    diff = data['difficulty']
    score = data['score']
    user = current_sessions[request.headers.get('Authorization')]
    
    if game not in all_data['leaderboards']:
        all_data['leaderboards'][game] = {}
    if diff not in all_data['leaderboards'][game]:
        all_data['leaderboards'][game][diff] = {}
    all_data['leaderboards'][game][diff][user] = max(
        all_data['leaderboards'][game][diff].get(user, 0), score
    )
    save_data(all_data)
    return jsonify({'success': True})

@app.route('/api/leaderboards/<game>/<difficulty>')
def get_leaderboard(game, difficulty):
    all_data = load_data()
    return jsonify(all_data['leaderboards'].get(game, {}).get(difficulty, {}))

@app.route('/api/tournament', methods=['GET', 'POST'])
def tournament():
    all_data = load_data()
    if request.method == 'POST':
        token = request.headers.get('Authorization')
        if not token or token not in current_sessions:
            return jsonify({'success': False}), 401
        user = current_sessions[token]
        score = request.json['score']
        all_data['tournament'][user] = all_data['tournament'].get(user, 0) + score
        save_data(all_data)
        return jsonify({'success': True})
    return jsonify(all_data['tournament'])

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    all_data = load_data()
    if request.method == 'POST':
        token = request.headers.get('Authorization')
        if not token or token not in current_sessions:
            return jsonify({'success': False}), 401
        msg = {
            'user': current_sessions[token],
            'message': request.json['message'],
            'time': datetime.now().strftime('%H:%M:%S')
        }
        all_data['chat'].append(msg)
        all_data['chat'] = all_data['chat'][-100:]
        save_data(all_data)
        return jsonify({'success': True})
    return jsonify(all_data['chat'][-50:])

@app.route('/api/tournament/reset', methods=['POST'])
@login_required
def reset_tournament():
    all_data = load_data()
    all_data['tournament'] = {}
    save_data(all_data)
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
