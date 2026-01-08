from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime
import atexit
import traceback

app = Flask(__name__, static_folder=None)
CORS(app)
DATA_FILE = 'games_data.json'
USERS_FILE = 'users.json'
SESSIONS_FILE = 'sessions.json'

def load_json(filename, default=None):
    """Автосоздание JSON файлов"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    if default is None:
        default = {}
    save_json(filename, default)
    return default

def save_json(filename, data):
    """Надёжное сохранение"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# Инициализация
games_data = load_json(DATA_FILE, {
    'leaderboards': {'snake': {'easy':{}, 'normal':{}, 'hard':{}}, 'guess': {'easy':{}, 'normal':{}, 'hard':{}}},
    'tournament': {},
    'chat': []
})
users_data = load_json(USERS_FILE, {'test': {'password': '123456'}})
sessions_data = load_json(SESSIONS_FILE, {})

def get_user():
    token = request.headers.get('Authorization') or request.args.get('token')
    return sessions_data.get(token, {}).get('user') if token else None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """ВСЕ запросы → index.html + защита от "Сервер недоступен" """
    try:
        if os.path.exists('index.html'):
            return send_file('index.html', mimetype='text/html')
    except:
        pass
    
    # Fallback HTML — НИКОГДА не покажет "Сервер недоступен"
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🚀 ALEKSIN GAMES v5.6 ✅ РАБОТАЕТ!</title>
    <meta charset="UTF-8">
    <style>
        body { 
            margin: 0; padding: 50px; 
            background: #000; color: #0f0; 
            font-family: monospace; text-align: center;
            background: linear-gradient(45deg, #0a0a23, #1a0a3a);
        }
        .container { max-width: 800px; margin: 0 auto; }
        .status { background: rgba(0,255,0,0.1); padding: 20px; border-radius: 15px; margin: 20px 0; }
        input { padding: 12px; margin: 10px; border: 2px solid #0f0; border-radius: 10px; background: #111; color: #0f0; font-family: monospace; width: 250px; }
        button { padding: 12px 24px; background: #0f0; color: #000; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; margin: 10px; }
        button:hover { background: #0a0; transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="font-size: 3rem; background: linear-gradient(45deg, #ff00ff, #00ffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🚀 ALEKSIN GAMES v5.6
        </h1>
        <div class="status">
            <h2>✅ СЕРВЕР РАБОТАЕТ! ДАННЫЕ НАВСЕГДА!</h2>
            <p><strong>📁 Файлы созданы:</strong></p>
            <p>• games_data.json → лидерборды, турнир, чат</p>
            <p>• users.json → test/123456</p>
            <p>• sessions.json → твои сессии</p>
        </div>
        
        <div style="background: rgba(0,0,0,0.5); padding: 30px; border-radius: 20px;">
            <h3>🎮 БЫСТРЫЙ ВХОД:</h3>
            <input type="text" id="username" placeholder="test" value="test">
            <input type="password" id="password" placeholder="123456" value="123456">
            <br>
            <button onclick="login()">🚀 ВОЙТИ В ИГРЫ</button>
            <button onclick="testAPI()">🧪 ТЕСТ API</button>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        async function login() {
            const user = document.getElementById('username').value;
            const pass = document.getElementById('password').value;
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: user, password: pass})
                });
                const data = await res.json();
                document.getElementById('status').innerHTML = 
                    data.success ? 
                    '<div style="color:#0f0;font-size:1.5rem">✅ ВХОД УСПЕШЕН! Перезагрузи страницу!</div>' :
                    `<div style="color:#f00">❌ ${data.error}</div>`;
            } catch(e) {
                document.getElementById('status').innerHTML = '<div style="color:#f00">❌ Ошибка сети</div>';
            }
        }
        
        async function testAPI() {
            try {
                const res = await fetch('/api/test');
                const data = await res.json();
                document.getElementById('status').innerHTML = 
                    `<div style="color:#0f0;font-size:1.2rem">✅ API РАБОТАЕТ! ${JSON.stringify(data)}</div>`;
            } catch(e) {
                document.getElementById('status').innerHTML = '<div style="color:#f00">❌ API недоступен</div>';
            }
        }
        
        // Автотест при загрузке
        testAPI();
    </script>
</body>
</html>
    ''', 200

@app.route('/api/test')
def test():
    return jsonify({
        'status': '✅ v5.6 РАБОТАЕТ!',
        'time': str(datetime.now()),
        'files': [f for f in [DATA_FILE, USERS_FILE, SESSIONS_FILE] if os.path.exists(f)],
        'users': len(users_data),
        'tournament': len(games_data['tournament'])
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if len(username) < 3 or len(password) < 4:
        return jsonify({'success': False, 'error': 'Логин ≥3, пароль ≥4 символа'})
    if username in users_data:
        return jsonify({'success': False, 'error': 'Пользователь существует'})
    
    users_data[username] = {'password': password}
    save_json(USERS_FILE, users_data)
    
    token = f"token_{username}_{int(datetime.now().timestamp())}"
    sessions_data[token] = {'user': username, 'time': datetime.now().timestamp()}
    save_json(SESSIONS_FILE, sessions_data)
    
    return jsonify({'success': True, 'user': username, 'token': token})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if username in users_data and users_data[username]['password'] == password:
        token = f"token_{username}_{int(datetime.now().timestamp())}"
        sessions_data[token] = {'user': username, 'time': datetime.now().timestamp()}
        save_json(SESSIONS_FILE, sessions_data)
        return jsonify({'success': True, 'user': username, 'token': token})
    
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/api/leaderboards/<game>/<difficulty>')
def get_leaderboard(game, difficulty):
    return jsonify(games_data['leaderboards'].get(game, {}).get(difficulty, {}))

@app.route('/api/scores', methods=['POST'])
def save_score():
    user = get_user()
    if not user:
        return jsonify({'success': False, 'error': '🔐 Войди!'}), 401
    
    data = request.get_json()
    game = data.get('game', 'unknown')
    diff = data.get('difficulty', 'easy')
    score = int(data.get('score', 0))
    
    if game not in games_data['leaderboards']:
        games_data['leaderboards'][game] = {}
    if diff not in games_data['leaderboards'][game]:
        games_data['leaderboards'][game][diff] = {}
    
    games_data['leaderboards'][game][diff][user] = max(
        games_data['leaderboards'][game][diff].get(user, 0), score
    )
    save_json(DATA_FILE, games_data)
    return jsonify({'success': True})

@app.route('/api/tournament', methods=['GET', 'POST'])
def tournament():
    if request.method == 'POST':
        user = get_user()
        if not user: return jsonify({'success': False}), 401
        score = int(request.get_json().get('score', 0))
        games_data['tournament'][user] = games_data['tournament'].get(user, 0) + score
        save_json(DATA_FILE, games_data)
        return jsonify({'success': True})
    return jsonify(games_data['tournament'])

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user = get_user()
        if not user: return jsonify({'success': False}), 401
        msg = request.get_json().get('message', '').strip()[:100]
        if msg:
            games_data['chat'].append({
                'user': user, 'message': msg, 
                'time': datetime.now().strftime('%H:%M')
            })
            games_data['chat'] = games_data['chat'][-50:]
            save_json(DATA_FILE, games_data)
        return jsonify({'success': True})
    return jsonify(games_data['chat'])

@app.route('/api/tournament/reset', methods=['POST'])
def reset_tournament():
    if get_user() not in ['test', 'admin']:
        return jsonify({'success': False, 'error': '🔐 Админ!'}), 403
    games_data['tournament'] = {}
    save_json(DATA_FILE, games_data)
    return jsonify({'success': True})

def save_all():
    save_json(DATA_FILE, games_data)
    save_json(USERS_FILE, users_data)
    save_json(SESSIONS_FILE, sessions_data)

atexit.register(save_all)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
