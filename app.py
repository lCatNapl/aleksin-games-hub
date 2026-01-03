from flask import Flask, render_template, request, jsonify, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-games-hub-2026-super-secret-final-v2')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False  
app.config['SESSION_COOKIE_SECURE'] = False

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect('gamehub.db')
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game TEXT,
        score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return jsonify({'status': 'API жив!', 'session': bool(session.get('user_id'))})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = hash_password(data.get('password', ''))
    
    if not username or len(username) < 3:
        return jsonify({'success': False, 'error': 'Имя 3+ символа'}), 400
    
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                    (username, password))
        conn.commit()
        session['user_id'] = conn.execute('SELECT id FROM users WHERE username=?', 
                                        (username,)).fetchone()['id']
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Имя занято'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = hash_password(data.get('password', ''))
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username=? AND password=?', 
                       (username, password)).fetchone()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False, 'error': 'Неверный пароль'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/status')
def status():
    if session.get('username'):
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False, 'username': None})

@app.route('/save_score', methods=['POST'])
def save_score():
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Авторизуйся'}), 401
    
    data = request.get_json()
    game = data.get('game')
    score = data.get('score', 0)
    
    conn = get_db()
    conn.execute('INSERT INTO scores (user_id, game, score) VALUES (?, ?, ?)',
                (session['user_id'], game, score))
    conn.commit()
    return jsonify({'success': True})

@app.route('/top/<game>')
def top(game):
    conn = get_db()
    leaders = conn.execute('''
        SELECT u.username, MAX(s.score) as score 
        FROM scores s JOIN users u ON s.user_id = u.id 
        WHERE s.game = ? 
        GROUP BY u.id ORDER BY score DESC LIMIT 10
    ''', (game,)).fetchall()
    return jsonify([dict(row) for row in leaders])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
