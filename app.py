import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

# ✅ ПЕРСЕСТИНТНЫЕ СЕССИИ
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aleksin-games-hub-2026-super-secret-key!'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
Session(app)

# ✅ ПЕРСЕСТИНТНАЯ БАЗА ДАННЫХ
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, 'users.db')

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        c = db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        
        # ✅ ТЕСТОВЫЙ ПОЛЬЗОВАТЕЛЬ
        c.execute("SELECT id FROM users WHERE username = 'test'")
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     ('test', generate_password_hash('123456')))
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False})
    
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if user:
            return jsonify({'logged_in': True, 'username': user['username']})
    return jsonify({'logged_in': False})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or len(username) < 3 or len(password) < 6:
        return jsonify({'success': False, 'error': 'Имя 3+ символа, пароль 6+'}), 400
    
    try:
        with get_db() as db:
            c = db.cursor()
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            if c.fetchone():
                return jsonify({'success': False, 'error': 'Пользователь существует'}), 400
            
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     (username, generate_password_hash(password)))
            user_id = c.lastrowid
            db.commit()
            
        session['user_id'] = user_id
        return jsonify({'success': True, 'username': username})
    except Exception as e:
        return jsonify({'success': False, 'error': 'Ошибка сервера'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return jsonify({'success': True, 'username': username})
        return jsonify({'success': False, 'error': 'Неверный логин/пароль'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/top/<game>')
def top(game):
    limit = request.args.get('limit', 10, type=int)
    with get_db() as db:
        c = db.cursor()
        c.execute('''
            SELECT u.username, MAX(s.score) as score 
            FROM scores s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.game = ? 
            GROUP BY s.user_id, u.username 
            ORDER BY score DESC 
            LIMIT ?
        ''', (game, limit))
        leaders = [{'username': row['username'], 'score': row['score']} for row in c.fetchall()]
    return jsonify(leaders)

@app.route('/save_score', methods=['POST'])
def save_score():
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    game = data.get('game')
    score = data.get('score')
    
    if not game or score is None:
        return jsonify({'success': False, 'error': 'Неверные данные'}), 400
    
    try:
        with get_db() as db:
            c = db.cursor()
            c.execute("INSERT INTO scores (user_id, game, score) VALUES (?, ?, ?)",
                     (session['user_id'], game, score))
            db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': 'Ошибка сохранения'}), 500

@app.route('/test')
def test():
    return jsonify({'status': 'Игровой Хаб Назар работает!', 'time': datetime.now().isoformat()})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
