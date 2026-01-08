from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import atexit
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.secret_key = 'aleksin-games-v5-super-secret-key-2026'

DATA_FILE = 'games_data.json'
USERS_FILE = 'users.json'
SESSIONS_FILE = 'sessions.json'

def load_json(filename, default=None):
    """Загрузка JSON с fallback"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default or {}
    except:
        return default or {}

def save_json(filename, data):
    """Сохранение JSON атомарно"""
    try:
        tmp = filename + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filename)
        return True
    except:
        return False

# Инициализация данных
games_data = load_json(DATA_FILE, {})
users = load_json(USERS_FILE, {})
sessions = load_json(SESSIONS_FILE, {})

def save_all():
    """Сохранение всех данных при завершении"""
    save_json(DATA_FILE, games_data)
    save_json(USERS_FILE, users)
    save_json(SESSIONS_FILE, sessions)

atexit.register(save_all)

# ✅ v5.6.2 ФИКС: X-Auth-Token вместо Authorization!
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if username == 'test' and password == '123456':
        token = 'admin_' + str(int(datetime.now().timestamp()))
        sessions[token] = {'user': username, 'exp': datetime.now().timestamp() + 3600}
        save_json(SESSIONS_FILE, sessions)
        return jsonify({'success': True, 'user': username, 'token': token})
    
    if username in users and users[username] == password:
        token = username + '_' + str(int(datetime.now().timestamp()))
        sessions[token] = {'user': username, 'exp': datetime.now().timestamp() + 3600}
        save_json(SESSIONS_FILE, sessions)
        return jsonify({'success': True, 'user': username, 'token': token})
    
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if len(username) < 3 or len(password) < 4:
        return jsonify({'success': False, 'error': 'Логин ≥3, пароль ≥4 символа'}), 400
    
    if username in users:
        return jsonify({'success': False, 'error': 'Логин занят'}), 400
    
    users[username] = password
    save_json(USERS_FILE, users)
    
    token = username + '_' + str(int(datetime.now().timestamp()))
    sessions[token] = {'user': username, 'exp': datetime.now().timestamp() + 3600}
    save_json(SESSIONS_FILE, sessions)
    
    return jsonify({'success': True, 'user': username, 'token': token})

def get_current_user():
    """Получить текущего пользователя по токену"""
    # ✅ v5.6.2 ФИКС: X-Auth-Token!
    token = request.headers.get('X-Auth-Token')
    if not token or token not in sessions:
        return None
    
    session = sessions[token]
    if datetime.now().timestamp() > session['exp']:
        del sessions[token]
        save_json(SESSIONS_FILE, sessions)
        return None
    
    return session['user']

@app.route('/api/leaderboards/<game>/<difficulty>')
def api_leaderboards(game, difficulty):
    user = get_current_user()
    if not user:
        return jsonify({})
    
    key = f"{game}_{difficulty}"
    return jsonify(games_data.get(key, {}))

@app.route('/api/scores', methods=['POST'])
def api_scores():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.get_json() or {}
    game = data.get('game', 'unknown')
    difficulty = data.get('difficulty', 'easy')
    score = data.get('score', 0)
    
    if score <= 0:
        return jsonify({'success': False, 'error': 'Некорректный счёт'}), 400
    
    key = f"{game}_{difficulty}"
    if key not in games_data:
        games_data[key] = {}
    
    games_data[key][user] = max(games_data[key].get(user, 0), score)
    save_json(DATA_FILE, games_data)
    
    return jsonify({'success': True, 'score': score})

@app.route('/api/tournament', methods=['GET', 'POST'])
def api_tournament():
    user = get_current_user()
    if request.method == 'POST' and not user:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    if request.method == 'POST':
        data = request.get_json() or {}
        score = data.get('score', 0)
        if score > 0:
            if 'tournament' not in games_data:
                games_data['tournament'] = {}
            games_data['tournament'][user] = games_data['tournament'].get(user, 0) + score
            save_json(DATA_FILE, games_data)
        return jsonify({'success': True})
    
    return jsonify(games_data.get('tournament', {}))

@app.route('/api/tournament/reset', methods=['POST'])
def api_tournament_reset():
    user = get_current_user()
    if not user or user != 'test':
        return jsonify({'success': False, 'error': 'Только для админа'}), 403
    
    if 'tournament' in games_data:
        del games_data['tournament']
        save_json(DATA_FILE, games_data)
    
    return jsonify({'success': True})

@app.route('/api/chat', methods=['GET', 'POST'])
def api_chat():
    user = get_current_user()
    if request.method == 'POST' and not user:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    if request.method == 'POST':
        data = request.get_json() or {}
        message = data.get('message', '').strip()[:100]
        if not message:
            return jsonify({'success': False, 'error': 'Пустое сообщение'}), 400
        
        if 'chat' not in games_data:
            games_data['chat'] = []
        
        games_data['chat'].append({
            'user': user,
            'message': message,
            'time': datetime.now().strftime('%H:%M:%S')
        })
        
        # Оставляем только последние 100 сообщений
        games_data['chat'] = games_data['chat'][-100:]
        save_json(DATA_FILE, games_data)
        return jsonify({'success': True})
    
    return jsonify(games_data.get('chat', []))

@app.route('/api/admin/stats')
def api_admin_stats():
    user = get_current_user()
    if user != 'test':
        return jsonify({'error': 'Только для админа'}), 403
    
    return jsonify({
        'users': len(users),
        'sessions': len(sessions),
        'games': len([k for k in games_data if not k.startswith('chat') and k != 'tournament']),
        'total_scores': sum(len(v) for v in games_data.values() if isinstance(v, dict))
    })

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    if path != 'index.html' and os.path.exists(path):
        return send_file(path)
    
    # Возвращаем index.html для всех маршрутов SPA
    return send_file('index.html')

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'ok', 'version': 'v5.6.2'})

if __name__ == '__main__':
    # ✅ Render использует PORT=10000 автоматически!
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
