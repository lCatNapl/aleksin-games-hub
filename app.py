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
    """Загрузка JSON с автосозданием"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
    if default is None:
        default = {}
    save_json(filename, default)
    return default

def save_json(filename, data):
    """Сохранение JSON с защитой от перезаписи"""
    try:
        tmp_file = filename + '.tmp'
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, filename)
        print(f"✅ Сохранено {filename}: {len(str(data))} байт")
    except Exception as e:
        print(f"❌ Ошибка сохранения {filename}: {e}")

# Инициализация данных
games_data = load_json(DATA_FILE, {
    'leaderboards': {'snake': {'easy':{}, 'normal':{}, 'hard':{}}, 'guess': {'easy':{}, 'normal':{}, 'hard':{}}},
    'tournament': {},
    'chat': []
})
users_data = load_json(USERS_FILE, {'test': {'password': '123456'}})
sessions_data = load_json(SESSIONS_FILE, {})

# Очистка старых сессий при старте
now = datetime.now().timestamp()
for token in list(sessions_data.keys()):
    if now - sessions_data[token]['time'] > 24*60*60:  # 24 часа
        del sessions_data[token]

def get_user():
    """Получить пользователя по токену"""
    token = request.headers.get('Authorization') or request.args.get('token')
    if token and token in sessions_data:
        sessions_data[token]['time'] = datetime.now().timestamp()
        return sessions_data[token]['user']
    return None

@app.route('/')
@app.route('/<path:path>')
def index(path=''):
    """Главная страница + все статические файлы"""
    try:
        if os.path.exists('index.html'):
            return send_file('index.html')
        else:
            # Fallback HTML если index.html нет
            return '''
<!DOCTYPE html><html><head><title>🚀 ALEKSIN GAMES</title></head>
<body style="background:#000;color:#0f0;font-family:monospace;padding:50px">
<h1>🚀 ALEKSIN GAMES v5.5 ✅ ДАННЫЕ НАВСЕГДА!</h1>
<p>✅ Сервер работает! test/123456 → играй!</p>
<div style="background:#111;padding:20px;border-radius:10px">
<p><strong>📁 Файлы сохранены:</strong></p>
<p>• games_data.json → лидерборды, турнир, чат</p>
<p>• users.json → аккаунты</p>
<p>• sessions.json → сессии</p>
</div>
</body></html>
            '''
    except Exception as e:
        return f'<h1>🚫 Ошибка: {str(e)}</h1>', 500

@app.route('/api/test')
def test():
    return jsonify({
        'status': '✅ СЕРВЕР РАБОТАЕТ v5.5!', 
        'time': str(datetime.now()),
        'data_files': [f for f in [DATA_FILE, USERS_FILE, SESSIONS_FILE] if os.path.exists(f)]
    })

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': 'Логин ≥3 символа'})
        if len(password) < 4:
            return jsonify({'success': False, 'error': 'Пароль ≥4 символа'})
        
        if username in users_data:
            return jsonify({'success': False, 'error': 'Пользователь существует'})
        
        users_data[username] = {'password': password}
        save_json(USERS_FILE, users_data)
        
        token = f"token_{username}_{int(datetime.now().timestamp())}"
        sessions_data[token] = {'user': username, 'time': datetime.now().timestamp()}
        save_json(SESSIONS_FILE, sessions_data)
        
        return jsonify({'success': True, 'user': username, 'token': token})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if username in users_data and users_data[username]['password'] == password:
            token = f"token_{username}_{int(datetime.now().timestamp())}"
            sessions_data[token] = {'user': username, 'time': datetime.now().timestamp()}
            save_json(SESSIONS_FILE, sessions_data)
            return jsonify({'success': True, 'user': username, 'token': token})
        
        return jsonify({'success': False, 'error': 'Неверный логин/пароль'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboards/<game>/<difficulty>')
def get_leaderboard(game, difficulty):
    return jsonify(games_data['leaderboards'].get(game, {}).get(difficulty, {}))

@app.route('/api/scores', methods=['POST'])
def save_score():
    user = get_user()
    if not user:
        return jsonify({'success': False, 'error': '🔐 Войди в аккаунт!'}), 401
    
    try:
        data = request.get_json()
        game = data.get('game', 'unknown')
        diff = data.get('difficulty', 'easy')
        score = int(data.get('score', 0))
        
        if game not in games_data['leaderboards']:
            games_data['leaderboards'][game] = {}
        if diff not in games_data['leaderboards'][game]:
            games_data['leaderboards'][game][diff] = {}
            
        old_score = games_data['leaderboards'][game][diff].get(user, 0)
        games_data['leaderboards'][game][diff][user] = max(old_score, score)
        save_json(DATA_FILE, games_data)
        
        return jsonify({'success': True, 'old_score': old_score, 'new_score': score})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tournament', methods=['GET', 'POST'])
def tournament():
    if request.method == 'POST':
        user = get_user()
        if not user:
            return jsonify({'success': False, 'error': '🔐 Войди!'}), 401
        try:
            score = int(request.get_json().get('score', 0))
            games_data['tournament'][user] = games_data['tournament'].get(user, 0) + score
            save_json(DATA_FILE, games_data)
            return jsonify({'success': True})
        except:
            return jsonify({'success': False}), 400
    return jsonify(games_data['tournament'])

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user = get_user()
        if not user:
            return jsonify({'success': False, 'error': '🔐 Войди!'}), 401
        try:
            msg = request.get_json().get('message', '').strip()[:100]
            if msg:
                games_data['chat'].append({
                    'user': user,
                    'message': msg,
                    'time': datetime.now().strftime('%H:%M %d.%m')
                })
                games_data['chat'] = games_data['chat'][-100:]  # Последние 100
                save_json(DATA_FILE, games_data)
            return jsonify({'success': True})
        except:
            return jsonify({'success': False}), 400
    return jsonify(games_data['chat'])

@app.route('/api/tournament/reset', methods=['POST'])
def reset_tournament():
    user = get_user()
    if user != 'admin' and user != 'test':
        return jsonify({'success': False, 'error': '🔐 Только админ!'}), 403
    games_data['tournament'] = {}
    save_json(DATA_FILE, games_data)
    return jsonify({'success': True})

@app.route('/api/admin/stats')
def admin_stats():
    user = get_user()
    if user not in ['admin', 'test']:
        return jsonify({'error': '🔐 Админ только!'}), 403
    return jsonify({
        'users_count': len(users_data),
        'leaderboards': {k: len(v) for k, v in games_data['leaderboards'].items()},
        'tournament_players': len(games_data['tournament']),
        'chat_messages': len(games_data['chat'])
    })

# Сохранение при завершении
def save_all_on_exit():
    save_json(DATA_FILE, games_data)
    save_json(USERS_FILE, users_data)
    save_json(SESSIONS_FILE, sessions_data)
    print("💾 ВСЕ ДАННЫЕ СОХРАНЕНЫ ПЕРЕД ВЫХОДОМ!")

atexit.register(save_all_on_exit)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 ALEKSIN GAMES v5.5 СТАРТУЕТ...")
    print(f"📁 {DATA_FILE}: OK" if os.path.exists(DATA_FILE) else f"📁 {DATA_FILE}: СОЗДАН")
    print(f"👥 Пользователей: {len(users_data)}")
    app.run(host='0.0.0.0', port=port, debug=False)
