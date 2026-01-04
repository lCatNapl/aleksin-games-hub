from flask import Flask, render_template, request, jsonify, session
import sqlite3
import hashlib
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-games-hub-2026-tournament')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False

DISK_PATH = os.environ.get('RENDER_DISK_PATH', './persistent')
DB_PATH = os.path.join(DISK_PATH, 'users.db')
TOURNAMENT_FILE = os.path.join(DISK_PATH, 'tournaments.json')

os.makedirs(DISK_PATH, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, highscore INTEGER DEFAULT 0, total_games INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username'].strip()
    password = hash_password(data['password'])
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = username
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username'].strip()
    password = hash_password(data['password'])
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, highscore) VALUES (?, ?, 0)", (username, password))
        conn.commit()
        session['user_id'] = username
        conn.close()
        return jsonify({'success': True, 'username': username})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Пользователь уже существует'})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/status')
def status():
    if session.get('user_id'):
        return jsonify({'logged_in': True, 'username': session['user_id']})
    return jsonify({'logged_in': False})

@app.route('/save_score', methods=['POST'])
def save_score():
    if not session.get('user_id'):
        return jsonify({'success': False})
    
    data = request.json
    username = session['user_id']
    score = data['score']
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET highscore = MAX(highscore, ?), total_games = total_games + 1 WHERE username = ?", (score, username))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, highscore FROM users ORDER BY highscore DESC LIMIT 10")
    leaders = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(leaders)

@app.route('/tournament')
def tournament():
    try:
        with open(TOURNAMENT_FILE, 'r') as f:
            data = json.load(f)
    except:
        # ✅ НОВЫЙ ТУРНИР 24ч
        data = {
            'active': True,
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(hours=24)).isoformat(),
            'scores': {}
        }
        with open(TOURNAMENT_FILE, 'w') as f:
            json.dump(data, f)
    
    return jsonify(data)

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
