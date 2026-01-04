# app.py — ПОЛНЫЙ ФИКС ВЫХОДА + ВСЕ БАГИ
from flask import Flask, render_template, request, jsonify, session
import sqlite3, hashlib, os, json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-games-hub-2026-tournament')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False

DISK_PATH = os.environ.get('RENDER_DISK_PATH', './persistent')
DB_PATH = os.path.join(DISK_PATH, 'users.db')
os.makedirs(DISK_PATH, exist_ok=True)

# 🔥 ИНИЦИАЛИЗАЦИЯ БАЗЫ
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, total_score INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY, username TEXT, game TEXT, score INTEGER, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        'logged_in': 'username' in session,
        'username': session.get('username', '')
    })

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username, password = data['username'], data['password']
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, total_score) VALUES (?, ?, 0)", 
                 (username, hashed))
        conn.commit()
        session['username'] = username
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Пользователь существует'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username, password = data['username'], data['password']
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=? AND password=?", 
              (username, hashed))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username'] = username
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Неверный пароль'})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # 🔥 ГАРАНТИРОВАННАЯ ОЧИСТКА СЕССИИ
    return jsonify({'success': True})

@app.route('/save_score', methods=['POST'])
def save_score():
    if 'username' not in session:
        return jsonify({'success': False}), 401
    
    data = request.json
    username, game, score = session['username'], data['game'], data['score']
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scores (username, game, score) VALUES (?, ?, ?)", 
              (username, game, score))
    c.execute("UPDATE users SET total_score = total_score + ? WHERE username = ?", 
              (score, username))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT username, SUM(score) as total FROM scores 
                 GROUP BY username ORDER BY total DESC LIMIT 10""")
    top = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(top)

@app.route('/tournament')
def tournament():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cutoff = datetime.now() - timedelta(hours=24)
    c.execute("""SELECT username, SUM(score) as score FROM scores 
                 WHERE timestamp > ? GROUP BY username 
                 ORDER BY score DESC LIMIT 10""", (cutoff,))
    daily = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(daily)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
