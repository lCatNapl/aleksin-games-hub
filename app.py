from flask import Flask, render_template, request, jsonify, session
import sqlite3
import hashlib
import os
import os.path
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-games-hub-2026-tournament')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False

# ✅ RENDER DISK - ДАННЫЕ НАВСЕГДА!
DISK_PATH = os.environ.get('RENDER_DISK_PATH', './persistent')
DB_PATH = os.path.join(DISK_PATH, 'users.db')
TOURNAMENT_FILE = os.path.join(DISK_PATH, 'tournaments.json')

os.makedirs(DISK_PATH, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, highscore_snake INTEGER DEFAULT 0, highscore_guess INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# ✅ ТУРНИРЫ
def load_tournaments():
    try:
        with open(TOURNAMENT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_tournaments(tournaments):
    with open(TOURNAMENT_FILE, 'w') as f:
        json.dump(tournaments, f)

def get_active_tournament():
    tournaments = load_tournaments()
    now = datetime.now()
    
    for tournament_id, data in tournaments.items():
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = start_time + timedelta(hours=24)
        
        if start_time <= now <= end_time:
            return tournament_id, data
    
    # ✅ НОВЫЙ ТУРНИР КАЖДЫЕ 24Ч
    new_id = now.strftime('%Y%m%d-%H')
    new_tournament = {
        new_id: {
            'start_time': now.isoformat(),
            'snake': {},
            'guess': {},
            'status': 'active'
        }
    }
    tournaments.update(new_tournament)
    save_tournaments(tournaments)
    return new_id, new_tournament[new_id]

@app.route('/')
def index():
    init_db()
    return render_template('index.html')

@app.route('/status')
def status():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Заполни все поля'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, hashlib.sha256(password.encode()).hexdigest()))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Пользователь уже существует'}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=? AND password=?", 
             (username, hashlib.sha256(password.encode()).hexdigest()))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username'] = username
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/save_score/<game>', methods=['POST'])
def save_score(game):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    
    data = request.json
    score = data.get('highscore', 0)
    username = session['username']
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if game == 'snake':
        c.execute("UPDATE users SET highscore_snake = MAX(highscore_snake, ?) WHERE username = ?", (score, username))
    elif game == 'guess':
        c.execute("UPDATE users SET highscore_guess = MAX(highscore_guess, ?) WHERE username = ?", (score, username))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/save_tournament_score/<game>', methods=['POST'])
def save_tournament_score(game):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    
    data = request.json
    score = data.get('score', 0)
    username = session['username']
    tournament_id, tournament_data = get_active_tournament()
    
    tournament_data[game][username] = max(tournament_data[game].get(username, 0), score)
    save_tournaments(load_tournaments())
    
    return jsonify({'success': True})

@app.route('/top/<game>')
def top(game):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if game == 'snake':
        c.execute("SELECT username, highscore_snake as score FROM users ORDER BY score DESC LIMIT 10")
    elif game == 'guess':
        c.execute("SELECT username, highscore_guess as score FROM users ORDER BY score DESC LIMIT 10")
    else:
        c.execute("SELECT username, 0 as score FROM users LIMIT 10")
    scores = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(scores)

@app.route('/tournament')
def tournament():
    tournament_id, data = get_active_tournament()
    end_time = datetime.fromisoformat(data['start_time']) + timedelta(hours=24)
    return jsonify({
        'id': tournament_id,
        'start_time': data['start_time'],
        'end_time': end_time.isoformat(),
        'snake_top': sorted(data['snake'].items(), key=lambda x: x[1], reverse=True)[:3],
        'guess_top': sorted(data['guess'].items(), key=lambda x: x[1], reverse=True)[:3]
    })

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
