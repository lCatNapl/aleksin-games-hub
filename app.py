from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-hub-2026-super-secure-v3')

def get_db_connection():
    conn = sqlite3.connect('gamehub.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game TEXT NOT NULL,
        score INTEGER NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    conn.close()

# 🔥 ИНИЦИАЛИЗАЦИЯ БД ПЕРЕД ЗАПУСКОМ 🔥
init_db()  # ← Заменил before_first_request!

def hash_password(password):
    return hashlib.sha256((password + 'salt_aleksin_2026').encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Авторизация требуется'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Имя занято'}), 409
    except:
        return jsonify({'success': False, 'error': 'Ошибка сервера'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = hash_password(data.get('password', ''))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'username': user['username']})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/save_score', methods=['POST'])
@login_required
def save_score():
    data = request.get_json()
    game = data.get('game')
    score = int(data.get('score'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO scores (user_id, game, score) VALUES (?, ?, ?)", 
              (session['user_id'], game, score))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT u.username, MAX(s.score) as score 
                 FROM scores s JOIN users u ON s.user_id=u.id 
                 WHERE s.game=? GROUP BY s.user_id ORDER BY score DESC LIMIT 10''', (game,))
    leaders = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(leaders)

@app.route('/api/user_status')
def user_status():
    return jsonify({
        'logged_in': 'user_id' in session,
        'username': session.get('username')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
