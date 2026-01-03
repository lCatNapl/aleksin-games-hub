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
                 (username TEXT PRIMARY KEY, password TEXT, total_score INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (username TEXT, game TEXT, score INTEGER, date TIMESTAMP,
                  FOREIGN KEY(username) REFERENCES users(username))''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = hash_password(data.get('password'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username'] = username
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = hash_password(data.get('password'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        session['username'] = username
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Пользователь уже существует'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/save', methods=['POST'])
def save():
    if 'username' not in session:
        return jsonify({'success': False})
    
    data = request.json
    username = session['username']
    game = data['game']
    score = data['score']
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scores (username, game, score, date) VALUES (?, ?, ?, ?)",
              (username, game, score, datetime.now()))
    c.execute("UPDATE users SET total_score = total_score + ? WHERE username = ?",
              (score, username))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/top/<game>')
def top(game):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, MAX(score) as score FROM scores WHERE game=? GROUP BY username ORDER BY score DESC LIMIT 10", (game,))
    results = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/tournament')
def tournament():
    try:
        with open(TOURNAMENT_FILE, 'r') as f:
            data = json.load(f)
    except:
        data = {'active': False}
    
    if data.get('active'):
        return jsonify(data)
    return jsonify({'active': False})

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
