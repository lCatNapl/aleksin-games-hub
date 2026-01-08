from flask import Flask, request, jsonify, session
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-admin-2026'
CORS(app)

DATA_FILE = 'games_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
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

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    users = load_data()['users']
    if data['username'] in users and users[data['username']]['password'] == data['password']:
        session['user'] = data['username']
        return jsonify({'success': True, 'user': data['username']})
    return jsonify({'success': False})

@app.route('/api/scores', methods=['POST'])
def save_score():
    if 'user' not in session: return jsonify({'success': False})
    data = request.json
    all_data = load_data()
    game = data['game']
    diff = data['difficulty']
    score = data['score']
    user = session['user']
    
    if game not in all_data['leaderboards']:
        all_data['leaderboards'][game] = {}
    if diff not in all_data['leaderboards'][game]:
        all_data['leaderboards'][game][diff] = {}
    all_data['leaderboards'][game][diff][user] = max(all_data['leaderboards'][game][diff].get(user, 0), score)
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
        if 'user' not in session: return jsonify({'success': False})
        user = session['user']
        score = request.json['score']
        all_data['tournament'][user] = all_data['tournament'].get(user, 0) + score
        save_data(all_data)
        return jsonify({'success': True})
    return jsonify(all_data['tournament'])

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    all_data = load_data()
    if request.method == 'POST':
        if 'user' not in session: return jsonify({'success': False})
        msg = {
            'user': session['user'],
            'message': request.json['message'],
            'time': datetime.now().strftime('%H:%M:%S')
        }
        all_data['chat'].append(msg)
        all_data['chat'] = all_data['chat'][-100:]
        save_data(all_data)
        return jsonify({'success': True})
    return jsonify(all_data['chat'][-50:])

@app.route('/api/tournament/reset', methods=['POST'])
def reset_tournament():
    all_data = load_data()
    all_data['tournament'] = {}
    save_data(all_data)
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
