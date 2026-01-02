from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-hub-2026-super-secure-v3')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Для HTTPS на Render

# Инициализация БД
def get_db_connection():
    conn = sqlite3.connect('gamehub.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL CHECK(length(username) >= 3),
        password TEXT NOT NULL CHECK(length(password) >= 6),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game TEXT NOT NULL,
        score INTEGER NOT NULL CHECK(score > 0),
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE(user_id, game)
    )''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256((password + 'salt_aleksin_2026').encode()).hexdigest()

# Декоратор проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Авторизация требуется'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.before_first_request
def setup():
    init_db()

@app.route('/')
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if len(username) < 3 or len(password) < 6:
            return jsonify({'success': False, 'error': 'Имя ≥3, пароль ≥6 символов'}), 400
        
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Регистрация успешна'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Имя пользователя занято'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': 'Ошибка сервера'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", 
                 (username, password_hash))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'username': user['username']})
        return jsonify({'success': False, 'error': 'Неверное имя или пароль'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': 'Ошибка сервера'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/save_score', methods=['POST'])
@login_required
def save_score():
    try:
        data = request.get_json()
        game = data.get('game', '').strip()
        score = int(data.get('score', 0))
        
        if not game or score <= 0:
            return jsonify({'success': False, 'error': 'Неверные данные'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        # Обновляем или вставляем лучший счёт
        c.execute('''INSERT OR REPLACE INTO scores (user_id, game, score, date) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)''', 
                 (session['user_id'], game, score))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except ValueError:
        return jsonify({'success': False, 'error': 'Неверный счёт'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Ошибка сервера'}), 500

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''SELECT u.username, MAX(s.score) as best_score, COUNT(s.id) as plays
                    FROM scores s JOIN users u ON s.user_id = u.id 
                    WHERE s.game = ? 
                    GROUP BY s.user_id 
                    ORDER BY best_score DESC LIMIT 10''', (game,))
        leaders = []
        for row in c.fetchall():
            leaders.append({
                'username': row['username'],
                'score': row['best_score'],
                'plays': row['plays']
            })
        conn.close()
        return jsonify(leaders)
    except Exception as e:
        return jsonify([]), 500

@app.route('/api/user_status')
def user_status():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
