from flask import Flask, render_template, request, jsonify, session
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-hub-super-secret-2026')

# 🔥 ФИКС СЕССИЙ ДЛЯ RENDER/БРАУЗЕР 🔥
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Только dev

def get_db():
    conn = sqlite3.connect('gamehub.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создать БД
def init_db():
    conn = get_db()
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
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()
init_db()

def hash_pwd(pwd):
    return hashlib.sha256((pwd + 'aleksin2026').encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = hash_pwd(data['password'])
    
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'error': 'Имя занято'})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = hash_pwd(data['password'])
    
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE username=? AND password=?", 
                       (username, password)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = username
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': 1})

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session:
        return jsonify({'ok': 0})
    data = request.json
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO scores (user_id, game, score) VALUES (?, ?, ?)",
                (session['user_id'], data['game'], data['score']))
    conn.commit()
    conn.close()
    return jsonify({'ok': 1})

@app.route('/top/<game>')
def top(game):  # ← ЭТО РОУТ ТОПА!
    conn = get_db()
    leaders = conn.execute("""
        SELECT u.username, MAX(s.score) score 
        FROM scores s 
        JOIN users u ON s.user_id=u.id 
        WHERE s.game=? 
        GROUP BY u.id 
        ORDER BY score DESC 
        LIMIT 10
    """, (game,)).fetchall()
    return jsonify(leaders)


@app.route('/status')
def status():
    return jsonify({
        'logged': 'user_id' in session,
        'user': session.get('username')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
