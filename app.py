from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = 'games_data.json'
current_sessions = {'test_token': 'test'}  # Дефолтный токен для теста

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
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

@app.route('/')
def index():
    try:
        return open('index.html').read()
    except:
        return '''
<!DOCTYPE html><html><body><h1>🚀 ALEKSIN GAMES v5.2</h1>
<p>Файл index.html не найден. Загрузи все 3 файла в корень!</p></body></html>'''

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', 'test')
    password = data.get('password', '123456')
    
    # ✅ ЛЮБОЙ ЛОГИН РАБОТАЕТ ДЛЯ ТЕСТА
    token = f"aleksin_{username}_{int(datetime.now().timestamp())}"
    current_sessions[token] = username
    
    return jsonify({
        'success': True, 
        'user': username, 
        'token': token,
        'status': 'Сервер работает!'
    })

@app.route('/api/leaderboards/<game>/<difficulty>')
def get_leaderboard(game, difficulty):
    data = load_data()
    return jsonify(data['leaderboards'].get(game, {}).get(difficulty, {}))

@app.route('/api/tournament', methods=['GET', 'POST'])
def tournament():
    data = load_data()
    if request.method == 'POST':
        try:
            score = request.get_json().get('score', 0)
            user = 'test'  # Гостевой режим
            data['tournament'][user] = data['tournament'].get(user, 0) + score
            save_data(data)
        except:
            pass
        return jsonify({'success': True})
    return jsonify(data['tournament'])

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    data = load_data()
    if request.method == 'POST':
        try:
            msg = request.get_json().get('message', '')
            data['chat'].append({
                'user': 'Гость', 
                'message': msg[:100], 
                'time': datetime.now().strftime('%H:%M')
            })
            data['chat'] = data['chat'][-50:]
            save_data(data)
        except:
            pass
        return jsonify({'success': True})
    return jsonify(data['chat'])

@app.route('/api/test')
def test():
    return jsonify({'status': '✅ Сервер работает!', 'time': datetime.now().isoformat()})

@app.route('/api/tournament/reset')
def reset_tournament():
    data = load_data()
    data['tournament'] = {}
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/scores', methods=['POST'])
def save_score():
    try:
        data = request.get_json()
        all_data = load_data()
        game = data.get('game', 'unknown')
        diff = data.get('difficulty', 'easy')
        score = data.get('score', 0)
        
        if game not in all_data['leaderboards']:
            all_data['leaderboards'][game] = {}
        if diff not in all_data['leaderboards'][game]:
            all_data['leaderboards'][game][diff] = {}
        all_data['leaderboards'][game][diff]['Гость'] = max(
            all_data['leaderboards'][game][diff].get('Гость', 0), score
        )
        save_data(all_data)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
